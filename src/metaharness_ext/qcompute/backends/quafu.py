"""Quafu real-hardware backend adapter using quarkstudio SDK.

This module provides ``QuafuBackendAdapter`` which wraps the ``quarkstudio``
package (``from quark import Task``) for submitting circuits to real quantum
hardware via the Quafu cloud platform.  When ``quarkstudio`` is not installed
every public method fails gracefully with ``RuntimeError`` so that callers
can check ``available`` first.
"""

from __future__ import annotations

import os
import time
from collections.abc import Mapping
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

# quarkstudio status strings -> ExecutionStatus mapping
_QUAFU_STATUS_MAP: dict[str, ExecutionStatus] = {
    "Submitted": ExecutionStatus.QUEUED,
    "Queued": ExecutionStatus.QUEUED,
    "In Queue": ExecutionStatus.QUEUED,
    "Pending": ExecutionStatus.QUEUED,
    "Running": ExecutionStatus.RUNNING,
    "Finished": ExecutionStatus.COMPLETED,
    "Completed": ExecutionStatus.COMPLETED,
    "Failed": ExecutionStatus.FAILED,
    "Error": ExecutionStatus.FAILED,
    "Timeout": ExecutionStatus.TIMEOUT,
    "Timed Out": ExecutionStatus.TIMEOUT,
    "Cancelled": ExecutionStatus.CANCELLED,
    "Canceled": ExecutionStatus.CANCELLED,
}

_DEFAULT_CHIP_ID = "Baihua"
_DEFAULT_TOKEN_ENV = "Qcompute_Token"
_DEFAULT_MAX_RETRIES = 3


def _detect_quark() -> Any:
    """Return the quark ``Task`` class if available, else ``None``."""
    try:
        from quark import Task  # type: ignore[import-untyped]

        return Task
    except ImportError:
        return None


def _circuit_to_openqasm(circuit: Any) -> str:
    """Convert a Qiskit ``QuantumCircuit`` to an OpenQASM 2 string."""
    import qiskit.qasm2  # type: ignore[import-untyped]

    return qiskit.qasm2.dumps(circuit)


class QuafuBackendAdapter:
    """Adapter that executes circuits on Quafu real-hardware backends.

    Uses the quarkstudio SDK (``pip install quarkstudio``,
    ``from quark import Task``).  All methods are safe to call even when
    ``quarkstudio`` is not installed; callers should check the ``available``
    property first or handle ``RuntimeError``.
    """

    # Satisfies metaharness.sdk.execution.AsyncExecutorProtocol by structural subtyping
    # (submit/poll/cancel/await_result methods match the protocol signature).

    def __init__(
        self,
        chip_id: str | None = None,
        api_token_env: str = _DEFAULT_TOKEN_ENV,
        max_retries: int = _DEFAULT_MAX_RETRIES,
    ) -> None:
        self._chip_id = chip_id or _DEFAULT_CHIP_ID
        self._api_token_env = api_token_env
        self._max_retries = max_retries
        self._polling = FibonacciPollingStrategy()
        self._task_manager: Any | None = None  # Lazy-init'd quark.Task

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    @property
    def available(self) -> bool:
        """Return ``True`` when ``quarkstudio`` is importable."""
        return _detect_quark() is not None

    def _get_task_manager(self) -> Any:
        """Lazy-initialize and return the quark Task manager."""
        if self._task_manager is not None:
            return self._task_manager
        task_cls = _detect_quark()
        if task_cls is None:
            raise RuntimeError("quarkstudio is not installed (pip install quarkstudio)")
        token = os.getenv(self._api_token_env)
        if not token:
            raise QuafuAuthenticationError(f"Missing Quafu API token: {self._api_token_env}")
        self._task_manager = task_cls(token=token)
        return self._task_manager

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
        tmgr = self._get_task_manager()
        qasm_str = _circuit_to_openqasm(circuit)

        task_id = self._execute_with_retries(
            lambda: tmgr.run(
                {
                    "chip": self._chip_id,
                    "name": f"MHE_{self._chip_id}",
                    "circuit": qasm_str,
                    "compile": True,
                }
            )
        )

        counts = self._poll_until_complete(tmgr, str(task_id), shots)
        total_shots = sum(counts.values())
        probabilities = {bs: cnt / total_shots for bs, cnt in counts.items()} if total_shots else {}
        return {
            "counts": counts,
            "probabilities": probabilities,
            "execution_time_ms": None,
            "metadata": {
                "backend": "quafu",
                "chip_id": self._chip_id,
                "task_id": str(task_id),
            },
            "shots_completed": total_shots,
        }

    # ------------------------------------------------------------------
    # Async executor protocol methods
    # ------------------------------------------------------------------

    async def submit(self, plan: Any) -> JobHandle:
        """Submit a compiled run plan and return a stable ``JobHandle``."""
        tmgr = self._get_task_manager()

        circuit_openqasm: str = plan.circuit_openqasm

        task_id = self._execute_with_retries(
            lambda: tmgr.run(
                {
                    "chip": self._chip_id,
                    "name": f"MHE_{plan.experiment_ref}",
                    "circuit": circuit_openqasm,
                    "compile": True,
                }
            )
        )
        return JobHandle(
            job_id=str(task_id),
            backend="quafu",
            status=ExecutionStatus.QUEUED,
            submitted_at=datetime.now(timezone.utc),
        )

    async def poll(self, job_id: str) -> ExecutionStatus:
        """Return the latest ``ExecutionStatus`` for *job_id*."""
        tmgr = self._get_task_manager()
        return self._normalize_status(tmgr.status(int(job_id)))

    async def cancel(self, job_id: str) -> None:
        """Request cancellation of a queued / running task."""
        tmgr = self._get_task_manager()
        tmgr.cancel(int(job_id))

    async def await_result(
        self,
        job_id: str,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """Poll until terminal state and return the final result dict.

        Raises ``TimeoutError`` when ``max_total_wait`` is exceeded.
        """
        polling = (
            FibonacciPollingStrategy(max_total_wait=timeout)
            if timeout is not None
            else self._polling
        )
        tmgr = self._get_task_manager()

        delays = polling.schedule(max_attempts=1000)
        for delay in delays:
            raw_status = tmgr.status(int(job_id))
            status = self._normalize_status(raw_status)

            if status == ExecutionStatus.COMPLETED:
                return self._fetch_result(tmgr, job_id, raw_status)
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

    def _poll_until_complete(self, tmgr: Any, task_id: str, shots: int) -> dict[str, int]:
        """Block until task completes and return the raw counts dict."""
        delays = self._polling.schedule(max_attempts=1000)
        for delay in delays:
            raw_status = tmgr.status(int(task_id))
            status = self._normalize_status(raw_status)

            if status == ExecutionStatus.COMPLETED:
                result = self._fetch_result(tmgr, task_id, raw_status)
                return result["counts"]

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

    def _fetch_result(
        self,
        tmgr: Any,
        job_id: str,
        raw_status: Any | None = None,
    ) -> dict[str, Any]:
        """Fetch and normalize the result dict for a completed task."""
        result = tmgr.result(int(job_id))
        if not isinstance(result, Mapping):
            raise QuafuError(f"Task {job_id} returned an invalid result payload")

        counts_payload = self._extract_counts(result)
        normalized = {str(k): int(v) for k, v in counts_payload.items()}
        total_shots = sum(normalized.values())
        probabilities = (
            {bs: cnt / total_shots for bs, cnt in normalized.items()} if total_shots else {}
        )
        metadata = self._build_metadata(job_id, result, raw_status)
        return {
            "counts": normalized,
            "probabilities": probabilities,
            "execution_time_ms": self._extract_execution_time_ms(result),
            "metadata": metadata,
            "shots_completed": total_shots,
        }

    def _normalize_status(self, raw_status: Any) -> ExecutionStatus:
        if isinstance(raw_status, Mapping):
            for key in ("status", "state", "task_status"):
                if key in raw_status:
                    return self._normalize_status(raw_status[key])
            if self._chip_id in raw_status:
                return ExecutionStatus.QUEUED
            return ExecutionStatus.FAILED
        return _QUAFU_STATUS_MAP.get(str(raw_status), ExecutionStatus.FAILED)

    def _extract_counts(self, result: Mapping[str, Any]) -> Mapping[Any, Any]:
        for key in ("count", "counts", "measurement_counts"):
            value = result.get(key)
            if isinstance(value, Mapping):
                return value
        data = result.get("data")
        if isinstance(data, Mapping):
            for key in ("count", "counts", "measurement_counts"):
                value = data.get(key)
                if isinstance(value, Mapping):
                    return value
        raise QuafuError("Quafu result payload does not contain counts")

    def _build_metadata(
        self,
        job_id: str,
        result: Mapping[str, Any],
        raw_status: Any | None,
    ) -> dict[str, Any]:
        metadata: dict[str, Any] = {
            "backend": "quafu",
            "chip_id": str(result.get("chip") or self._chip_id),
            "task_id": str(result.get("tid") or result.get("task_id") or job_id),
        }
        for source in (raw_status, result):
            if not isinstance(source, Mapping):
                continue
            for key in ("queue_depth", "queue_position", "quota", "quota_snapshot"):
                if key in source:
                    metadata[key] = source[key]
        return metadata

    def _extract_execution_time_ms(self, result: Mapping[str, Any]) -> float | None:
        for key in ("execution_time_ms", "time_ms"):
            value = result.get(key)
            if value is not None:
                return float(value)
        for key in ("execution_time", "time", "elapsed"):
            value = result.get(key)
            if value is not None:
                return float(value) * 1000.0
        return None

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
