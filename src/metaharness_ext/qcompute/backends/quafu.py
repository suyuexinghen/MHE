"""Quafu real-hardware backend adapter.

This module provides ``QuafuBackendAdapter`` which wraps the ``pyquafu``
package for submitting circuits to real quantum hardware via the Quafu
cloud platform.  When ``pyquafu`` is not installed every public method
fails gracefully with ``RuntimeError`` so that callers can check
``available`` first.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Any

from metaharness.sdk.execution import (
    ExecutionStatus,
    FibonacciPollingStrategy,
    JobHandle,
)
from metaharness_ext.qcompute.contracts import QComputeNoiseSpec

# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class QuafuError(Exception):
    """Base exception for all Quafu-related errors."""


class QuafuAuthenticationError(QuafuError):
    """Non-retriable: invalid or missing API token."""


class QuafuQueueTimeoutError(QuafuError):
    """Retriable: task timed out waiting in the hardware queue."""


class QuafuNetworkError(QuafuError):
    """Retriable: transient network connectivity issue."""


class QuafuCircuitTopologyError(QuafuError):
    """Non-retriable: circuit does not fit target chip topology."""


class QuafuCalibrationError(QuafuError):
    """Non-retriable: calibration data unavailable or unusable."""


# ---------------------------------------------------------------------------
# Retriable / non-retriable classification
# ---------------------------------------------------------------------------

_RETRIABLE_ERRORS: tuple[type[QuafuError], ...] = (
    QuafuQueueTimeoutError,
    QuafuNetworkError,
)

_NON_RETRIABLE_ERRORS: tuple[type[QuafuError], ...] = (
    QuafuAuthenticationError,
    QuafuCircuitTopologyError,
    QuafuCalibrationError,
)

# Status strings returned by the Quafu cloud API.
_QUAFU_TO_EXECUTION_STATUS: dict[str, ExecutionStatus] = {
    "created": ExecutionStatus.CREATED,
    "queued": ExecutionStatus.QUEUED,
    "running": ExecutionStatus.RUNNING,
    "completed": ExecutionStatus.COMPLETED,
    "failed": ExecutionStatus.FAILED,
    "timeout": ExecutionStatus.TIMEOUT,
    "cancelled": ExecutionStatus.CANCELLED,
}

_DEFAULT_CHIP_ID = "ScQ-P10"
_DEFAULT_MAX_RETRIES = 3


def _detect_pyquafu() -> Any:
    """Return the ``pyquafu`` module if available, else ``None``."""
    try:
        import pyquafu  # noqa: F401

        return pyquafu
    except ImportError:
        return None


def _circuit_to_openqasm(circuit: Any) -> str:
    """Convert a Qiskit ``QuantumCircuit`` to an OpenQASM 2 string."""
    import qiskit.qasm2  # type: ignore[import-untyped]

    return qiskit.qasm2.dumps(circuit)


class QuafuBackendAdapter:
    """Adapter that executes circuits on Quafu real-hardware backends.

    All methods are safe to call even when ``pyquafu`` is not installed;
    callers should check the ``available`` property first or handle
    ``RuntimeError``.
    """

    def __init__(
        self,
        chip_id: str | None = None,
        api_token_env: str = "QUAFU_API_TOKEN",
        max_retries: int = _DEFAULT_MAX_RETRIES,
    ) -> None:
        self._chip_id = chip_id or _DEFAULT_CHIP_ID
        self._api_token_env = api_token_env
        self._max_retries = max_retries
        self._polling = FibonacciPollingStrategy()

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    @property
    def available(self) -> bool:
        """Return ``True`` when ``pyquafu`` is importable."""
        return _detect_pyquafu() is not None

    # ------------------------------------------------------------------
    # Sync interface (matching QiskitAerBackend.run)
    # ------------------------------------------------------------------

    def run(
        self,
        *,
        circuit: Any,
        shots: int,
        noise: QComputeNoiseSpec | None = None,
    ) -> dict[str, Any]:
        """Execute *circuit* on Quafu hardware and return result dict.

        This is the synchronous entry-point matching the
        ``QiskitAerBackend.run()`` signature.  It submits the circuit,
        polls until completion using the Fibonacci strategy, and returns
        a normalised result dict.
        """
        self._require_pyquafu()
        qasm_str = _circuit_to_openqasm(circuit)

        task_id = self._submit_raw(qasm_str, shots)
        counts = self._poll_until_complete(task_id)
        total_shots = sum(counts.values())
        probabilities = {bs: cnt / total_shots for bs, cnt in counts.items()} if total_shots else {}
        return {
            "counts": counts,
            "probabilities": probabilities,
            "execution_time_ms": None,
            "metadata": {"backend": "quafu", "chip_id": self._chip_id},
            "shots_completed": total_shots,
        }

    # ------------------------------------------------------------------
    # Async executor protocol methods
    # ------------------------------------------------------------------

    async def submit(self, plan: Any) -> JobHandle:
        """Submit a compiled run plan and return a stable ``JobHandle``."""
        self._require_pyquafu()

        circuit_openqasm: str = plan.circuit_openqasm
        shots: int = plan.execution_params.shots

        task_id = self._execute_with_retries(lambda: self._submit_raw(circuit_openqasm, shots))
        return JobHandle(
            job_id=task_id,
            backend="quafu",
            status=ExecutionStatus.QUEUED,
            submitted_at=datetime.now(timezone.utc),
        )

    async def poll(self, job_id: str) -> ExecutionStatus:
        """Return the latest ``ExecutionStatus`` for *job_id*."""
        self._require_pyquafu()
        raw_status = self._query_task_status(job_id)
        return _QUAFU_TO_EXECUTION_STATUS.get(raw_status, ExecutionStatus.FAILED)

    async def cancel(self, job_id: str) -> None:
        """Request cancellation of a queued / running task."""
        self._require_pyquafu()
        pyquafu = _detect_pyquafu()
        pyquafu.cancel_task(task_id=job_id)  # type: ignore[attr-defined]

    async def await_result(
        self,
        job_id: str,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """Poll until terminal state and return the final result dict.

        Raises ``TimeoutError`` when ``max_total_wait`` is exceeded.
        """
        self._require_pyquafu()

        polling = (
            FibonacciPollingStrategy(max_total_wait=timeout)
            if timeout is not None
            else self._polling
        )

        delays = polling.schedule(max_attempts=1000)
        for delay in delays:
            raw_status = self._query_task_status(job_id)
            status = _QUAFU_TO_EXECUTION_STATUS.get(raw_status, ExecutionStatus.FAILED)

            if status == ExecutionStatus.COMPLETED:
                return self._fetch_result(job_id)
            if status in {
                ExecutionStatus.FAILED,
                ExecutionStatus.TIMEOUT,
                ExecutionStatus.CANCELLED,
            }:
                raise QuafuError(f"Task {job_id} ended in terminal state: {status.value}")

            time.sleep(delay)

        raise TimeoutError(f"Task {job_id} did not complete within {polling.max_total_wait}s")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require_pyquafu(self) -> None:
        if not self.available:
            raise RuntimeError("pyQuafu is not installed")

    def _get_token(self) -> str:
        token = os.getenv(self._api_token_env)
        if not token:
            raise QuafuAuthenticationError(f"Missing Quafu API token: {self._api_token_env}")
        return token

    def _submit_raw(self, openqasm: str, shots: int) -> str:
        """Submit OpenQASM to Quafu and return the task id."""
        pyquafu = _detect_pyquafu()
        self._get_token()  # ensure token is present
        result = pyquafu.execute_task(  # type: ignore[attr-defined]
            openqasm=openqasm,
            shots=shots,
            chip_id=self._chip_id,
        )
        task_id: str = result["task_id"]
        return task_id

    def _query_task_status(self, task_id: str) -> str:
        pyquafu = _detect_pyquafu()
        info = pyquafu.query_task(task_id=task_id)  # type: ignore[attr-defined]
        return str(info.get("status", "failed"))

    def _fetch_result(self, task_id: str) -> dict[str, Any]:
        pyquafu = _detect_pyquafu()
        info = pyquafu.query_task(task_id=task_id)  # type: ignore[attr-defined]
        raw_res = info.get("res", {})
        counts = {str(k): int(v) for k, v in raw_res.items()}
        total_shots = sum(counts.values())
        probabilities = {bs: cnt / total_shots for bs, cnt in counts.items()} if total_shots else {}
        return {
            "counts": counts,
            "probabilities": probabilities,
            "execution_time_ms": None,
            "metadata": {"backend": "quafu", "chip_id": self._chip_id},
            "shots_completed": total_shots,
        }

    def _poll_until_complete(self, task_id: str) -> dict[str, int]:
        """Block until task completes and return the raw counts dict."""
        delays = self._polling.schedule(max_attempts=1000)
        for delay in delays:
            raw_status = self._query_task_status(task_id)
            status = _QUAFU_TO_EXECUTION_STATUS.get(raw_status, ExecutionStatus.FAILED)

            if status == ExecutionStatus.COMPLETED:
                pyquafu = _detect_pyquafu()
                info = pyquafu.query_task(task_id=task_id)  # type: ignore[attr-defined]
                raw_res = info.get("res", {})
                return {str(k): int(v) for k, v in raw_res.items()}

            if status in {
                ExecutionStatus.FAILED,
                ExecutionStatus.TIMEOUT,
                ExecutionStatus.CANCELLED,
            }:
                raise QuafuError(f"Task {task_id} ended in terminal state: {status.value}")

            time.sleep(delay)

        raise TimeoutError(
            f"Task {task_id} did not complete within {self._polling.max_total_wait}s"
        )

    def _execute_with_retries(self, fn: Any) -> Any:
        """Execute *fn* with retry logic for retriable Quafu errors."""
        last_error: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                return fn()
            except _RETRIABLE_ERRORS as exc:
                last_error = exc
                backoff = 2**attempt
                time.sleep(backoff)
            except _NON_RETRIABLE_ERRORS:
                raise
        if last_error is not None:
            raise last_error
        raise QuafuError("Unexpected retry exhaustion")  # pragma: no cover
