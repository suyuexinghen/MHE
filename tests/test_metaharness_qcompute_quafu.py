"""Tests for the Quafu real-hardware backend integration.

quarkstudio (``from quark import Task``) is NOT installed in the test
environment, so all tests that exercise QuafuBackendAdapter internals mock
the ``quark`` module via ``unittest.mock``.
"""

from __future__ import annotations

import importlib
import importlib.util
import os
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from metaharness.sdk.execution import ExecutionStatus, JobHandle

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_quark():
    """Inject a mock ``quark`` module with ``Task`` class into ``sys.modules``."""
    mock_task_cls = MagicMock()
    mock_instance = MagicMock()
    mock_task_cls.return_value = mock_instance

    # Default: chip status shows Baihua online with 57 qubits
    mock_instance.status.return_value = {"Baihua": 57, "Miaofeng": "Maintenance"}

    # Default: run returns a task ID string
    mock_instance.run.return_value = "2604261809502337788"

    # Default: status with task_id returns "Finished"
    mock_instance.result.return_value = {
        "count": {"00": 500, "11": 524},
        "status": "Finished",
        "chip": "Baihua",
        "shots": 1024,
        "tid": "2604261809502337788",
    }

    mock_module = MagicMock(Task=mock_task_cls)

    with patch.dict(sys.modules, {"quark": mock_module}):
        yield mock_task_cls, mock_instance


@pytest.fixture()
def quafu_module():
    """Import (or re-import) the quafu backend module for clean state."""
    import metaharness_ext.qcompute.backends.quafu as quafu_mod

    importlib.reload(quafu_mod)
    return quafu_mod


@pytest.fixture()
def mock_circuit():
    """Return a minimal Qiskit-like circuit mock."""
    circuit = MagicMock()
    circuit.num_qubits = 2
    circuit.num_clbits = 2
    return circuit


# ===========================================================================
# QuafuBackendAdapter tests -- quarkstudio NOT installed
# ===========================================================================


class TestQuafuBackendNotAvailable:
    def test_available_is_false_without_quarkstudio(self, quafu_module):
        with patch.object(quafu_module, "_detect_quark", return_value=None):
            adapter = quafu_module.QuafuBackendAdapter()
            assert adapter.available is False

    def test_run_raises_without_quarkstudio(self, quafu_module):
        with patch.object(quafu_module, "_detect_quark", return_value=None):
            adapter = quafu_module.QuafuBackendAdapter()
            with pytest.raises(RuntimeError, match="quarkstudio is not installed"):
                adapter.run(circuit=MagicMock(), shots=1024)

    @pytest.mark.asyncio
    async def test_submit_raises_without_quarkstudio(self, quafu_module):
        with patch.object(quafu_module, "_detect_quark", return_value=None):
            adapter = quafu_module.QuafuBackendAdapter()
            with pytest.raises(RuntimeError, match="quarkstudio is not installed"):
                await adapter.submit(MagicMock())

    @pytest.mark.asyncio
    async def test_poll_raises_without_quarkstudio(self, quafu_module):
        with patch.object(quafu_module, "_detect_quark", return_value=None):
            adapter = quafu_module.QuafuBackendAdapter()
            with pytest.raises(RuntimeError, match="quarkstudio is not installed"):
                await adapter.poll("task-1")

    @pytest.mark.asyncio
    async def test_cancel_raises_without_quarkstudio(self, quafu_module):
        with patch.object(quafu_module, "_detect_quark", return_value=None):
            adapter = quafu_module.QuafuBackendAdapter()
            with pytest.raises(RuntimeError, match="quarkstudio is not installed"):
                await adapter.cancel("task-1")

    @pytest.mark.asyncio
    async def test_await_result_raises_without_quarkstudio(self, quafu_module):
        with patch.object(quafu_module, "_detect_quark", return_value=None):
            adapter = quafu_module.QuafuBackendAdapter()
            with pytest.raises(RuntimeError, match="quarkstudio is not installed"):
                await adapter.await_result("task-1")


# ===========================================================================
# QuafuBackendAdapter tests -- quarkstudio mocked as installed
# ===========================================================================


class TestQuafuBackendAvailable:
    def test_available_is_true_with_quarkstudio(self, mock_quark, quafu_module):
        adapter = quafu_module.QuafuBackendAdapter()
        assert adapter.available is True


class TestQuafuSubmit:
    @pytest.mark.asyncio
    async def test_submit_returns_job_handle(self, mock_quark, quafu_module, monkeypatch):
        mock_task_cls, mock_instance = mock_quark
        monkeypatch.setenv("Qcompute_Token", "fake-token-123")
        adapter = quafu_module.QuafuBackendAdapter()

        plan = MagicMock()
        plan.circuit_openqasm = 'OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; h q[0];'
        plan.execution_params.shots = 1024
        plan.experiment_ref = "test-experiment"

        handle = await adapter.submit(plan)

        assert isinstance(handle, JobHandle)
        assert handle.job_id == "2604261809502337788"
        assert handle.backend == "quafu"
        assert handle.status == ExecutionStatus.QUEUED

        # Verify tmgr.run was called with the expected dict
        mock_instance.run.assert_called_once()
        call_args = mock_instance.run.call_args[0][0]
        assert call_args["chip"] == "Baihua"
        assert call_args["name"] == "MHE_test-experiment"
        assert call_args["compile"] is True


class TestQuafuPoll:
    @pytest.mark.asyncio
    async def test_poll_returns_completed_status(self, mock_quark, quafu_module, monkeypatch):
        mock_task_cls, mock_instance = mock_quark
        monkeypatch.setenv("Qcompute_Token", "fake-token-123")
        adapter = quafu_module.QuafuBackendAdapter()

        mock_instance.status.return_value = "Finished"
        status = await adapter.poll("2604261809502337788")
        assert status == ExecutionStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_poll_maps_submitted(self, mock_quark, quafu_module, monkeypatch):
        mock_task_cls, mock_instance = mock_quark
        monkeypatch.setenv("Qcompute_Token", "fake-token-123")
        adapter = quafu_module.QuafuBackendAdapter()

        mock_instance.status.return_value = "Submitted"
        status = await adapter.poll("2604261809502337788")
        assert status == ExecutionStatus.QUEUED

    @pytest.mark.asyncio
    async def test_poll_maps_running(self, mock_quark, quafu_module, monkeypatch):
        mock_task_cls, mock_instance = mock_quark
        monkeypatch.setenv("Qcompute_Token", "fake-token-123")
        adapter = quafu_module.QuafuBackendAdapter()

        mock_instance.status.return_value = "Running"
        status = await adapter.poll("2604261809502337788")
        assert status == ExecutionStatus.RUNNING

    @pytest.mark.asyncio
    async def test_poll_maps_queue_status_payload(self, mock_quark, quafu_module, monkeypatch):
        mock_task_cls, mock_instance = mock_quark
        monkeypatch.setenv("Qcompute_Token", "fake-token-123")
        adapter = quafu_module.QuafuBackendAdapter()

        mock_instance.status.return_value = {"status": "In Queue", "queue_position": 4}
        status = await adapter.poll("2604261809502337788")
        assert status == ExecutionStatus.QUEUED

    @pytest.mark.asyncio
    async def test_poll_maps_timeout_status(self, mock_quark, quafu_module, monkeypatch):
        mock_task_cls, mock_instance = mock_quark
        monkeypatch.setenv("Qcompute_Token", "fake-token-123")
        adapter = quafu_module.QuafuBackendAdapter()

        mock_instance.status.return_value = "Timed Out"
        status = await adapter.poll("2604261809502337788")
        assert status == ExecutionStatus.TIMEOUT

    @pytest.mark.asyncio
    async def test_poll_maps_failed(self, mock_quark, quafu_module, monkeypatch):
        mock_task_cls, mock_instance = mock_quark
        monkeypatch.setenv("Qcompute_Token", "fake-token-123")
        adapter = quafu_module.QuafuBackendAdapter()

        mock_instance.status.return_value = "Failed"
        status = await adapter.poll("2604261809502337788")
        assert status == ExecutionStatus.FAILED

    @pytest.mark.asyncio
    async def test_poll_maps_cancelled(self, mock_quark, quafu_module, monkeypatch):
        mock_task_cls, mock_instance = mock_quark
        monkeypatch.setenv("Qcompute_Token", "fake-token-123")
        adapter = quafu_module.QuafuBackendAdapter()

        mock_instance.status.return_value = "Cancelled"
        status = await adapter.poll("2604261809502337788")
        assert status == ExecutionStatus.CANCELLED


class TestQuafuCancel:
    @pytest.mark.asyncio
    async def test_cancel_calls_quark_cancel(self, mock_quark, quafu_module, monkeypatch):
        mock_task_cls, mock_instance = mock_quark
        monkeypatch.setenv("Qcompute_Token", "fake-token-123")
        adapter = quafu_module.QuafuBackendAdapter()

        await adapter.cancel("2604261809502337788")

        mock_instance.cancel.assert_called_once_with(2604261809502337788)


class TestQuafuAwaitResult:
    @pytest.mark.asyncio
    async def test_await_result_completes(self, mock_quark, quafu_module, monkeypatch):
        mock_task_cls, mock_instance = mock_quark
        monkeypatch.setenv("Qcompute_Token", "fake-token-123")
        adapter = quafu_module.QuafuBackendAdapter()

        # First call to status() returns "Finished"
        mock_instance.status.return_value = "Finished"
        mock_instance.result.return_value = {
            "count": {"00": 500, "11": 524},
            "status": "Finished",
            "chip": "Baihua",
            "shots": 1024,
            "tid": "2604261809502337788",
        }

        with patch.object(quafu_module.time, "sleep"):
            result = await adapter.await_result("2604261809502337788")

        assert result["counts"] == {"00": 500, "11": 524}
        assert result["shots_completed"] == 1024
        assert result["metadata"]["task_id"] == "2604261809502337788"

    @pytest.mark.asyncio
    async def test_await_result_includes_queue_and_quota_metadata(
        self, mock_quark, quafu_module, monkeypatch
    ):
        mock_task_cls, mock_instance = mock_quark
        monkeypatch.setenv("Qcompute_Token", "fake-token-123")
        adapter = quafu_module.QuafuBackendAdapter()

        mock_instance.status.return_value = {
            "status": "Finished",
            "queue_depth": 2,
            "queue_position": 0,
            "quota": {"remaining": 9, "limit": 10},
        }
        mock_instance.result.return_value = {
            "counts": {"0": "7", "1": 3},
            "chip": "Baihua",
            "task_id": "2604261809502337788",
            "execution_time_ms": 125.5,
        }

        with patch.object(quafu_module.time, "sleep"):
            result = await adapter.await_result("2604261809502337788")

        assert result["counts"] == {"0": 7, "1": 3}
        assert result["execution_time_ms"] == 125.5
        assert result["metadata"]["queue_depth"] == 2
        assert result["metadata"]["queue_position"] == 0
        assert result["metadata"]["quota"] == {"remaining": 9, "limit": 10}

    @pytest.mark.asyncio
    async def test_await_result_parses_nested_counts(self, mock_quark, quafu_module, monkeypatch):
        mock_task_cls, mock_instance = mock_quark
        monkeypatch.setenv("Qcompute_Token", "fake-token-123")
        adapter = quafu_module.QuafuBackendAdapter()

        mock_instance.status.return_value = "Finished"
        mock_instance.result.return_value = {"data": {"measurement_counts": {"00": 2, "11": 2}}}

        result = await adapter.await_result("2604261809502337788")

        assert result["counts"] == {"00": 2, "11": 2}
        assert result["shots_completed"] == 4

    @pytest.mark.asyncio
    async def test_await_result_rejects_missing_counts(self, mock_quark, quafu_module, monkeypatch):
        mock_task_cls, mock_instance = mock_quark
        monkeypatch.setenv("Qcompute_Token", "fake-token-123")
        adapter = quafu_module.QuafuBackendAdapter()

        mock_instance.status.return_value = "Finished"
        mock_instance.result.return_value = {"status": "Finished"}

        with pytest.raises(quafu_module.QuafuError, match="does not contain counts"):
            await adapter.await_result("2604261809502337788")

    @pytest.mark.asyncio
    async def test_await_result_timeout(self, mock_quark, quafu_module, monkeypatch):
        mock_task_cls, mock_instance = mock_quark
        monkeypatch.setenv("Qcompute_Token", "fake-token-123")
        # Task never completes.
        mock_instance.status.return_value = "Running"
        adapter = quafu_module.QuafuBackendAdapter()

        with patch.object(quafu_module.time, "sleep"):
            with pytest.raises(TimeoutError, match="did not complete"):
                await adapter.await_result("2604261809502337788", timeout=0.01)

    @pytest.mark.asyncio
    async def test_await_result_failed_raises(self, mock_quark, quafu_module, monkeypatch):
        mock_task_cls, mock_instance = mock_quark
        monkeypatch.setenv("Qcompute_Token", "fake-token-123")
        mock_instance.status.return_value = "Failed"
        adapter = quafu_module.QuafuBackendAdapter()

        with patch.object(quafu_module.time, "sleep"):
            with pytest.raises(quafu_module.QuafuError, match="terminal state"):
                await adapter.await_result("2604261809502337788", timeout=1.0)


class TestQuafuRetry:
    def test_retry_on_queue_timeout(self, mock_quark, quafu_module, monkeypatch):
        mock_task_cls, mock_instance = mock_quark
        monkeypatch.setenv("Qcompute_Token", "fake-token-123")

        # Fail twice with retriable error, then succeed.
        call_count = 0

        def side_effect(task_dict):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise quafu_module.QuafuQueueTimeoutError("queue full")
            return "retried-task-id"

        mock_instance.run.side_effect = side_effect

        adapter = quafu_module.QuafuBackendAdapter(max_retries=3)

        with patch.object(quafu_module.time, "sleep"):
            result = adapter._execute_with_retries(
                lambda: mock_instance.run({"chip": "Baihua", "circuit": "...", "compile": True})
            )

        assert result == "retried-task-id"
        assert call_count == 3

    def test_no_retry_on_circuit_error(self, mock_quark, quafu_module, monkeypatch):
        mock_task_cls, mock_instance = mock_quark
        monkeypatch.setenv("Qcompute_Token", "fake-token-123")

        mock_instance.run.side_effect = quafu_module.QuafuCircuitTopologyError("gate unsupported")

        adapter = quafu_module.QuafuBackendAdapter(max_retries=3)

        with pytest.raises(quafu_module.QuafuCircuitTopologyError, match="gate unsupported"):
            adapter._execute_with_retries(
                lambda: mock_instance.run({"chip": "Baihua", "circuit": "...", "compile": True})
            )

    def test_no_retry_on_auth_error(self, mock_quark, quafu_module, monkeypatch):
        mock_task_cls, mock_instance = mock_quark
        monkeypatch.setenv("Qcompute_Token", "fake-token-123")

        mock_instance.run.side_effect = quafu_module.QuafuAuthenticationError("bad token")

        adapter = quafu_module.QuafuBackendAdapter(max_retries=3)

        with pytest.raises(quafu_module.QuafuAuthenticationError, match="bad token"):
            adapter._execute_with_retries(
                lambda: mock_instance.run({"chip": "Baihua", "circuit": "...", "compile": True})
            )


class TestQuafuFibonacciPolling:
    def test_fibonacci_polling_schedule_is_used(self, mock_quark, quafu_module):
        adapter = quafu_module.QuafuBackendAdapter()

        # The adapter's internal polling strategy should produce Fibonacci
        # delays.  We just verify the strategy produces non-zero delays
        # that are capped.
        from metaharness.sdk.execution import FibonacciPollingStrategy

        strategy = adapter._polling
        assert isinstance(strategy, FibonacciPollingStrategy)
        assert strategy.base_delay == 1.0
        assert strategy.max_delay == 60.0

        delays = strategy.schedule(10)
        assert len(delays) == 10
        # First delay is base * fib(1) = 1.0 * 1 = 1.0
        assert delays[0] == pytest.approx(1.0)
        # Second delay is base * fib(2) = 1.0 * 1 = 1.0
        assert delays[1] == pytest.approx(1.0)
        # Third delay is base * fib(3) = 1.0 * 2 = 2.0
        assert delays[2] == pytest.approx(2.0)


class TestQuafuSyncRun:
    def test_run_returns_result_dict(self, mock_quark, quafu_module, mock_circuit, monkeypatch):
        mock_task_cls, mock_instance = mock_quark
        monkeypatch.setenv("Qcompute_Token", "fake-token-123")

        # status returns "Finished" when called with int task_id
        def mock_status(arg=None):
            if arg is None:
                return {"Baihua": 57}
            return "Finished"

        mock_instance.status.side_effect = mock_status
        mock_instance.result.return_value = {
            "count": {"00": 500, "11": 524},
            "status": "Finished",
            "chip": "Baihua",
            "shots": 1024,
        }

        with patch.object(quafu_module, "_circuit_to_openqasm", return_value="OPENQASM 2.0;"):
            with patch.object(quafu_module.time, "sleep"):
                adapter = quafu_module.QuafuBackendAdapter()
                result = adapter.run(circuit=mock_circuit, shots=1024)

        assert result["counts"] == {"00": 500, "11": 524}
        assert result["shots_completed"] == 1024
        assert result["metadata"]["backend"] == "quafu"
        assert result["metadata"]["task_id"] == "2604261809502337788"
        assert abs(sum(result["probabilities"].values()) - 1.0) < 1e-9


class TestQuafuExceptions:
    def test_exception_hierarchy(self, quafu_module):
        assert issubclass(quafu_module.QuafuAuthenticationError, quafu_module.QuafuError)
        assert issubclass(quafu_module.QuafuQueueTimeoutError, quafu_module.QuafuError)
        assert issubclass(quafu_module.QuafuNetworkError, quafu_module.QuafuError)
        assert issubclass(quafu_module.QuafuCircuitTopologyError, quafu_module.QuafuError)
        assert issubclass(quafu_module.QuafuCalibrationError, quafu_module.QuafuError)


class TestQuafuDefaults:
    def test_default_chip_is_baihua(self, quafu_module):
        adapter = quafu_module.QuafuBackendAdapter()
        assert adapter._chip_id == "Baihua"

    def test_default_token_env_is_qcompute_token(self, quafu_module):
        adapter = quafu_module.QuafuBackendAdapter()
        assert adapter._api_token_env == "Qcompute_Token"

    def test_custom_chip_id(self, quafu_module):
        adapter = quafu_module.QuafuBackendAdapter(chip_id="Yudu")
        assert adapter._chip_id == "Yudu"

    def test_custom_token_env(self, quafu_module):
        adapter = quafu_module.QuafuBackendAdapter(api_token_env="MY_TOKEN")
        assert adapter._api_token_env == "MY_TOKEN"


class TestQuafuStatusMapping:
    def test_all_real_statuses_mapped(self, quafu_module):
        status_map = quafu_module._QUAFU_STATUS_MAP
        assert status_map["Submitted"] == ExecutionStatus.QUEUED
        assert status_map["Queued"] == ExecutionStatus.QUEUED
        assert status_map["In Queue"] == ExecutionStatus.QUEUED
        assert status_map["Pending"] == ExecutionStatus.QUEUED
        assert status_map["Running"] == ExecutionStatus.RUNNING
        assert status_map["Finished"] == ExecutionStatus.COMPLETED
        assert status_map["Completed"] == ExecutionStatus.COMPLETED
        assert status_map["Failed"] == ExecutionStatus.FAILED
        assert status_map["Error"] == ExecutionStatus.FAILED
        assert status_map["Timeout"] == ExecutionStatus.TIMEOUT
        assert status_map["Timed Out"] == ExecutionStatus.TIMEOUT
        assert status_map["Cancelled"] == ExecutionStatus.CANCELLED
        assert status_map["Canceled"] == ExecutionStatus.CANCELLED


# ===========================================================================
# Environment probe tests
# ===========================================================================


def _build_quafu_spec(**overrides):
    from metaharness_ext.qcompute.contracts import (
        QComputeBackendSpec,
        QComputeExperimentSpec,
        QComputeNoiseSpec,
    )

    data = {
        "task_id": "qcompute-quafu-1",
        "mode": "simulate",
        "backend": QComputeBackendSpec(
            platform="quafu",
            simulator=False,
            qubit_count=10,
            chip_id="Baihua",
        ),
        "circuit": {
            "ansatz": "custom",
            "num_qubits": 2,
            "openqasm": ('OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; h q[0]; cx q[0],q[1];'),
        },
        "noise": QComputeNoiseSpec(model="none"),
    }
    data.update(overrides)
    return QComputeExperimentSpec(**data)


class TestEnvironmentQuafu:
    def test_quafu_missing_dependency(self):
        from metaharness_ext.qcompute.environment import (
            QComputeEnvironmentProbeComponent,
        )

        # _detect_quark returns None -> dependency_missing
        with patch(
            "metaharness_ext.qcompute.backends.quafu._detect_quark",
            return_value=None,
        ):
            report = QComputeEnvironmentProbeComponent().probe(_build_quafu_spec())

        assert report.available is False
        assert report.status == "dependency_missing"
        assert any("quarkstudio" in msg for msg in report.prerequisite_errors)

    def test_quafu_missing_token(self):
        from metaharness_ext.qcompute.environment import (
            QComputeEnvironmentProbeComponent,
        )

        mock_task_cls = MagicMock()

        with patch(
            "metaharness_ext.qcompute.backends.quafu._detect_quark",
            return_value=mock_task_cls,
        ):
            # Ensure the token env var is absent.
            with patch("os.getenv", return_value=None):
                report = QComputeEnvironmentProbeComponent().probe(_build_quafu_spec())

        assert report.available is False
        assert report.status == "missing_api_token"

    def test_quafu_available_with_token(self):
        from metaharness_ext.qcompute.environment import (
            QComputeEnvironmentProbeComponent,
        )

        mock_task_cls = MagicMock()
        mock_instance = MagicMock()
        mock_task_cls.return_value = mock_instance
        mock_instance.status.return_value = {"Baihua": 57}

        with patch(
            "metaharness_ext.qcompute.backends.quafu._detect_quark",
            return_value=mock_task_cls,
        ):
            with patch("os.getenv", return_value="fake-quafu-token"):
                with patch.object(
                    QComputeEnvironmentProbeComponent,
                    "_query_calibration",
                    return_value=None,
                ):
                    report = QComputeEnvironmentProbeComponent().probe(_build_quafu_spec())

        assert report.available is True
        assert report.status == "online"

    def test_quafu_chip_in_maintenance(self):
        from metaharness_ext.qcompute.environment import (
            QComputeEnvironmentProbeComponent,
        )

        mock_task_cls = MagicMock()
        mock_instance = MagicMock()
        mock_task_cls.return_value = mock_instance
        mock_instance.status.return_value = {"Baihua": "Maintenance"}

        with patch(
            "metaharness_ext.qcompute.backends.quafu._detect_quark",
            return_value=mock_task_cls,
        ):
            with patch("os.getenv", return_value="fake-quafu-token"):
                report = QComputeEnvironmentProbeComponent().probe(_build_quafu_spec())

        assert report.available is False
        assert report.status == "chip_maintenance"

    def test_quafu_chip_calibrating(self):
        from metaharness_ext.qcompute.environment import (
            QComputeEnvironmentProbeComponent,
        )

        mock_task_cls = MagicMock()
        mock_instance = MagicMock()
        mock_task_cls.return_value = mock_instance
        mock_instance.status.return_value = {"Baihua": "Calibrating"}

        with patch(
            "metaharness_ext.qcompute.backends.quafu._detect_quark",
            return_value=mock_task_cls,
        ):
            with patch("os.getenv", return_value="fake-quafu-token"):
                report = QComputeEnvironmentProbeComponent().probe(_build_quafu_spec())

        assert report.available is False
        assert report.status == "chip_calibrating"

    def test_quafu_connection_error(self):
        from metaharness_ext.qcompute.environment import (
            QComputeEnvironmentProbeComponent,
        )

        mock_task_cls = MagicMock()
        mock_instance = MagicMock()
        mock_task_cls.return_value = mock_instance
        mock_instance.status.side_effect = ConnectionError("network down")

        with patch(
            "metaharness_ext.qcompute.backends.quafu._detect_quark",
            return_value=mock_task_cls,
        ):
            with patch("os.getenv", return_value="fake-quafu-token"):
                report = QComputeEnvironmentProbeComponent().probe(_build_quafu_spec())

        assert report.available is False
        assert report.status == "connection_error"


class TestCalibrationFreshness:
    def _make_probe(self):
        from metaharness_ext.qcompute.environment import (
            QComputeEnvironmentProbeComponent,
        )

        return QComputeEnvironmentProbeComponent()

    def test_fresh_calibration(self):
        probe = self._make_probe()
        recent = datetime.now(timezone.utc) - timedelta(hours=1)
        assert probe._check_calibration_freshness(recent) == "fresh"

    def test_stale_calibration(self):
        probe = self._make_probe()
        stale = datetime.now(timezone.utc) - timedelta(hours=6)
        assert probe._check_calibration_freshness(stale) == "stale"

    def test_very_stale_calibration(self):
        probe = self._make_probe()
        very_stale = datetime.now(timezone.utc) - timedelta(hours=48)
        assert probe._check_calibration_freshness(very_stale) == "very_stale"

    def test_naive_datetime_treated_as_utc(self):
        probe = self._make_probe()
        naive = datetime.now() - timedelta(hours=1)
        # Should not crash; naive datetime gets tzinfo added.
        result = probe._check_calibration_freshness(naive)
        assert result in {"fresh", "stale", "very_stale"}


class TestCalibrationBlockingPromotion:
    def test_very_stale_blocks_promotion(self):
        from metaharness_ext.qcompute.environment import (
            QComputeEnvironmentProbeComponent,
        )

        mock_task_cls = MagicMock()
        mock_instance = MagicMock()
        mock_task_cls.return_value = mock_instance
        mock_instance.status.return_value = {"Baihua": 57}

        very_stale_ts = datetime.now(timezone.utc) - timedelta(hours=48)

        with patch(
            "metaharness_ext.qcompute.backends.quafu._detect_quark",
            return_value=mock_task_cls,
        ):
            with patch("os.getenv", return_value="fake-token"):
                with patch.object(
                    QComputeEnvironmentProbeComponent,
                    "_query_calibration",
                    return_value=very_stale_ts,
                ):
                    report = QComputeEnvironmentProbeComponent().probe(_build_quafu_spec())

        assert report.available is False
        assert report.status == "calibration_stale"
        assert any("very stale" in msg for msg in report.prerequisite_errors)


# ===========================================================================
# Executor integration test
# ===========================================================================


class TestExecutorQuafuBackend:
    def test_select_backend_returns_quafu_adapter(self):
        from metaharness_ext.qcompute.backends.quafu import QuafuBackendAdapter
        from metaharness_ext.qcompute.executor import QComputeExecutorComponent

        executor = QComputeExecutorComponent()
        backend = executor._select_backend("quafu")

        assert isinstance(backend, QuafuBackendAdapter)


# ===========================================================================
# Contracts tests
# ===========================================================================


class TestQuafuChipInfoContract:
    def test_chip_info_model(self):
        from metaharness_ext.qcompute.contracts import QComputeQuafuChipInfo

        info = QComputeQuafuChipInfo(
            chip_id="Baihua",
            status="online",
            qubit_count=41,
            queue_depth=3,
        )
        assert info.chip_id == "Baihua"
        assert info.status == "online"
        assert info.qubit_count == 41
        assert info.queue_depth == 3
        assert info.calibration_timestamp is None

    def test_chip_info_with_calibration_timestamp(self):
        from metaharness_ext.qcompute.contracts import QComputeQuafuChipInfo

        now = datetime.now(timezone.utc)
        info = QComputeQuafuChipInfo(
            chip_id="Baihua",
            status="online",
            qubit_count=41,
            calibration_timestamp=now,
            queue_depth=0,
        )
        assert info.calibration_timestamp == now


# ===========================================================================
# Real hardware test (requires Qcompute_Token)
# ===========================================================================


@pytest.mark.quafu
def test_quafu_real_baihua_bell_state():
    """Submit a real Bell state to Baihua chip. Requires Qcompute_Token in env."""
    import time as real_time

    token = os.getenv("Qcompute_Token")
    if not token:
        pytest.skip("Qcompute_Token not set")
    if importlib.util.find_spec("quark") is None:
        pytest.skip("quarkstudio is not installed")

    from quark import Task  # type: ignore[import-untyped]

    tmgr = Task(token=token)

    # Check Baihua is online
    status = tmgr.status()
    if not isinstance(status.get("Baihua"), int):
        pytest.skip(f"Baihua not available: {status.get('Baihua')}")

    qasm = """OPENQASM 2.0;
include "qelib1.inc";
qreg q[8];
creg c[8];
h q[2];
cx q[2],q[3];
measure q[2] -> c[2];
measure q[3] -> c[3];
"""
    tid = tmgr.run({"chip": "Baihua", "name": "MHE_Bell_Test", "circuit": qasm, "compile": True})
    assert tid is not None

    # Wait for result
    for _ in range(60):
        s = tmgr.status(tid)
        if s == "Finished":
            break
        real_time.sleep(2)

    res = tmgr.result(tid)
    counts = res.get("count", {})
    total = sum(counts.values())
    # Bell state should be dominated by |00> and |11>
    bell_fraction = (counts.get("00", 0) + counts.get("11", 0)) / total
    assert bell_fraction > 0.7, f"Bell fraction too low: {bell_fraction}, counts: {counts}"
