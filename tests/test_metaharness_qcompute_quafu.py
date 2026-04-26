"""Tests for the Quafu real-hardware backend integration.

pyQuafu is NOT installed in the test environment, so all tests that
exercise QuafuBackendAdapter internals mock the ``pyquafu`` module via
``unittest.mock``.
"""

from __future__ import annotations

import importlib
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from metaharness.sdk.execution import ExecutionStatus, JobHandle

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_pyquafu():
    """Inject a mock ``pyquafu`` module into ``sys.modules``."""
    mock_module = MagicMock()
    mock_module.execute_task.return_value = {
        "task_id": "test-task-123",
        "status": "queued",
    }
    mock_module.query_task.return_value = {
        "status": "completed",
        "res": {"00": 500, "11": 524},
    }
    mock_module.cancel_task.return_value = None
    with patch.dict(sys.modules, {"pyquafu": mock_module}):
        yield mock_module


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
# QuafuBackendAdapter tests -- pyquafu NOT installed
# ===========================================================================


class TestQuafuBackendNotAvailable:
    def test_available_is_false_without_pyquafu(self, quafu_module):
        adapter = quafu_module.QuafuBackendAdapter()
        # pyquafu is not installed in test env, so available should be False.
        assert adapter.available is False

    def test_run_raises_without_pyquafu(self, quafu_module):
        adapter = quafu_module.QuafuBackendAdapter()
        with pytest.raises(RuntimeError, match="pyQuafu is not installed"):
            adapter.run(circuit=MagicMock(), shots=1024)

    @pytest.mark.asyncio
    async def test_submit_raises_without_pyquafu(self, quafu_module):
        adapter = quafu_module.QuafuBackendAdapter()
        with pytest.raises(RuntimeError, match="pyQuafu is not installed"):
            await adapter.submit(MagicMock())

    @pytest.mark.asyncio
    async def test_poll_raises_without_pyquafu(self, quafu_module):
        adapter = quafu_module.QuafuBackendAdapter()
        with pytest.raises(RuntimeError, match="pyQuafu is not installed"):
            await adapter.poll("task-1")

    @pytest.mark.asyncio
    async def test_cancel_raises_without_pyquafu(self, quafu_module):
        adapter = quafu_module.QuafuBackendAdapter()
        with pytest.raises(RuntimeError, match="pyQuafu is not installed"):
            await adapter.cancel("task-1")

    @pytest.mark.asyncio
    async def test_await_result_raises_without_pyquafu(self, quafu_module):
        adapter = quafu_module.QuafuBackendAdapter()
        with pytest.raises(RuntimeError, match="pyQuafu is not installed"):
            await adapter.await_result("task-1")


# ===========================================================================
# QuafuBackendAdapter tests -- pyquafu mocked as installed
# ===========================================================================


class TestQuafuBackendAvailable:
    def test_available_is_true_with_pyquafu(self, mock_pyquafu, quafu_module):
        adapter = quafu_module.QuafuBackendAdapter()
        assert adapter.available is True


class TestQuafuSubmit:
    @pytest.mark.asyncio
    async def test_submit_returns_job_handle(self, mock_pyquafu, quafu_module, monkeypatch):
        monkeypatch.setenv("QUAFU_API_TOKEN", "fake-token-123")
        adapter = quafu_module.QuafuBackendAdapter()

        plan = MagicMock()
        plan.circuit_openqasm = 'OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; h q[0];'
        plan.execution_params.shots = 1024

        handle = await adapter.submit(plan)

        assert isinstance(handle, JobHandle)
        assert handle.job_id == "test-task-123"
        assert handle.backend == "quafu"
        assert handle.status == ExecutionStatus.QUEUED


class TestQuafuPoll:
    @pytest.mark.asyncio
    async def test_poll_returns_status(self, mock_pyquafu, quafu_module):
        adapter = quafu_module.QuafuBackendAdapter()

        # Default mock returns "completed"
        status = await adapter.poll("test-task-123")
        assert status == ExecutionStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_poll_maps_queued(self, mock_pyquafu, quafu_module):
        mock_pyquafu.query_task.return_value = {"status": "queued"}
        adapter = quafu_module.QuafuBackendAdapter()

        status = await adapter.poll("test-task-123")
        assert status == ExecutionStatus.QUEUED

    @pytest.mark.asyncio
    async def test_poll_maps_running(self, mock_pyquafu, quafu_module):
        mock_pyquafu.query_task.return_value = {"status": "running"}
        adapter = quafu_module.QuafuBackendAdapter()

        status = await adapter.poll("test-task-123")
        assert status == ExecutionStatus.RUNNING


class TestQuafuCancel:
    @pytest.mark.asyncio
    async def test_cancel_calls_pyquafu(self, mock_pyquafu, quafu_module):
        adapter = quafu_module.QuafuBackendAdapter()

        await adapter.cancel("test-task-123")

        mock_pyquafu.cancel_task.assert_called_once_with(task_id="test-task-123")


class TestQuafuAwaitResult:
    @pytest.mark.asyncio
    async def test_await_result_completes(self, mock_pyquafu, quafu_module, monkeypatch):
        monkeypatch.setenv("QUAFU_API_TOKEN", "fake-token-123")
        adapter = quafu_module.QuafuBackendAdapter()

        # Mock time.sleep to avoid real delays.
        with patch.object(quafu_module.time, "sleep"):
            result = await adapter.await_result("test-task-123")

        assert result["counts"] == {"00": 500, "11": 524}
        assert result["shots_completed"] == 1024

    @pytest.mark.asyncio
    async def test_await_result_timeout(self, mock_pyquafu, quafu_module):
        # Task never completes.
        mock_pyquafu.query_task.return_value = {"status": "running"}
        adapter = quafu_module.QuafuBackendAdapter()

        with patch.object(quafu_module.time, "sleep"):
            with pytest.raises(TimeoutError, match="did not complete"):
                await adapter.await_result("test-task-123", timeout=0.01)

    @pytest.mark.asyncio
    async def test_await_result_failed_raises(self, mock_pyquafu, quafu_module):
        mock_pyquafu.query_task.return_value = {"status": "failed"}
        adapter = quafu_module.QuafuBackendAdapter()

        with patch.object(quafu_module.time, "sleep"):
            with pytest.raises(quafu_module.QuafuError, match="terminal state"):
                await adapter.await_result("test-task-123", timeout=1.0)


class TestQuafuRetry:
    def test_retry_on_queue_timeout(self, mock_pyquafu, quafu_module, monkeypatch):
        monkeypatch.setenv("QUAFU_API_TOKEN", "fake-token-123")

        # Fail twice with retriable error, then succeed.
        call_count = 0

        def side_effect(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise quafu_module.QuafuQueueTimeoutError("queue full")
            return {"task_id": "retried-task", "status": "queued"}

        mock_pyquafu.execute_task.side_effect = side_effect

        adapter = quafu_module.QuafuBackendAdapter(max_retries=3)

        with patch.object(quafu_module.time, "sleep"):
            plan = MagicMock()
            plan.circuit_openqasm = "OPENQASM 2.0;"
            plan.execution_params.shots = 100

            # submit() is async; use the sync _execute_with_retries directly.
            result = adapter._execute_with_retries(
                lambda: mock_pyquafu.execute_task(
                    openqasm="OPENQASM 2.0;", shots=100, chip_id="ScQ-P10"
                )
            )

        assert result["task_id"] == "retried-task"
        assert call_count == 3

    def test_no_retry_on_circuit_error(self, mock_pyquafu, quafu_module, monkeypatch):
        monkeypatch.setenv("QUAFU_API_TOKEN", "fake-token-123")

        mock_pyquafu.execute_task.side_effect = quafu_module.QuafuCircuitTopologyError(
            "gate unsupported"
        )

        adapter = quafu_module.QuafuBackendAdapter(max_retries=3)

        with pytest.raises(quafu_module.QuafuCircuitTopologyError, match="gate unsupported"):
            adapter._execute_with_retries(lambda: mock_pyquafu.execute_task())

    def test_no_retry_on_auth_error(self, mock_pyquafu, quafu_module, monkeypatch):
        monkeypatch.setenv("QUAFU_API_TOKEN", "fake-token-123")

        mock_pyquafu.execute_task.side_effect = quafu_module.QuafuAuthenticationError("bad token")

        adapter = quafu_module.QuafuBackendAdapter(max_retries=3)

        with pytest.raises(quafu_module.QuafuAuthenticationError, match="bad token"):
            adapter._execute_with_retries(lambda: mock_pyquafu.execute_task())


class TestQuafuFibonacciPolling:
    def test_fibonacci_polling_schedule_is_used(self, mock_pyquafu, quafu_module):
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
    def test_run_returns_result_dict(self, mock_pyquafu, quafu_module, mock_circuit, monkeypatch):
        monkeypatch.setenv("QUAFU_API_TOKEN", "fake-token-123")

        with patch.object(quafu_module, "_circuit_to_openqasm", return_value="OPENQASM 2.0;"):
            with patch.object(quafu_module.time, "sleep"):
                adapter = quafu_module.QuafuBackendAdapter()
                result = adapter.run(circuit=mock_circuit, shots=1024)

        assert result["counts"] == {"00": 500, "11": 524}
        assert result["shots_completed"] == 1024
        assert result["metadata"]["backend"] == "quafu"
        assert abs(sum(result["probabilities"].values()) - 1.0) < 1e-9


class TestQuafuExceptions:
    def test_exception_hierarchy(self, quafu_module):
        assert issubclass(quafu_module.QuafuAuthenticationError, quafu_module.QuafuError)
        assert issubclass(quafu_module.QuafuQueueTimeoutError, quafu_module.QuafuError)
        assert issubclass(quafu_module.QuafuNetworkError, quafu_module.QuafuError)
        assert issubclass(quafu_module.QuafuCircuitTopologyError, quafu_module.QuafuError)
        assert issubclass(quafu_module.QuafuCalibrationError, quafu_module.QuafuError)


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
            chip_id="ScQ-P10",
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

        # find_spec("pyquafu") returns None -> dependency_missing
        with patch(
            "metaharness_ext.qcompute.environment.find_spec",
            side_effect=lambda name: None,
        ):
            report = QComputeEnvironmentProbeComponent().probe(_build_quafu_spec())

        assert report.available is False
        assert report.status == "dependency_missing"
        assert any("pyquafu" in msg for msg in report.prerequisite_errors)

    def test_quafu_missing_token(self):
        from metaharness_ext.qcompute.environment import (
            QComputeEnvironmentProbeComponent,
        )

        spec = _build_quafu_spec()

        def fake_find_spec(name):
            if name == "pyquafu":
                return MagicMock()  # truthy -> installed
            return None

        with patch(
            "metaharness_ext.qcompute.environment.find_spec",
            side_effect=fake_find_spec,
        ):
            # Ensure the token env var is absent.
            with patch("os.getenv", return_value=None):
                report = QComputeEnvironmentProbeComponent().probe(spec)

        assert report.available is False
        assert report.status == "missing_api_token"

    def test_quafu_available_with_token(self):
        from metaharness_ext.qcompute.environment import (
            QComputeEnvironmentProbeComponent,
        )

        spec = _build_quafu_spec()

        def fake_find_spec(name):
            if name == "pyquafu":
                return MagicMock()
            return None

        with patch(
            "metaharness_ext.qcompute.environment.find_spec",
            side_effect=fake_find_spec,
        ):
            with patch("os.getenv", return_value="fake-quafu-token"):
                with patch.object(
                    QComputeEnvironmentProbeComponent,
                    "_query_calibration",
                    return_value=None,
                ):
                    report = QComputeEnvironmentProbeComponent().probe(spec)

        assert report.available is True
        assert report.status == "online"


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

        spec = _build_quafu_spec()

        def fake_find_spec(name):
            if name == "pyquafu":
                return MagicMock()
            return None

        very_stale_ts = datetime.now(timezone.utc) - timedelta(hours=48)

        with patch(
            "metaharness_ext.qcompute.environment.find_spec",
            side_effect=fake_find_spec,
        ):
            with patch("os.getenv", return_value="fake-token"):
                with patch.object(
                    QComputeEnvironmentProbeComponent,
                    "_query_calibration",
                    return_value=very_stale_ts,
                ):
                    report = QComputeEnvironmentProbeComponent().probe(spec)

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
            chip_id="ScQ-P10",
            status="online",
            qubit_count=10,
            queue_depth=3,
        )
        assert info.chip_id == "ScQ-P10"
        assert info.status == "online"
        assert info.qubit_count == 10
        assert info.queue_depth == 3
        assert info.calibration_timestamp is None

    def test_chip_info_with_calibration_timestamp(self):
        from metaharness_ext.qcompute.contracts import QComputeQuafuChipInfo

        now = datetime.now(timezone.utc)
        info = QComputeQuafuChipInfo(
            chip_id="ScQ-P18",
            status="maintenance",
            qubit_count=18,
            calibration_timestamp=now,
            queue_depth=0,
        )
        assert info.calibration_timestamp == now
