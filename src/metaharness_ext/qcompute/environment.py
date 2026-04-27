from __future__ import annotations

import os
from collections.abc import Mapping
from datetime import datetime, timezone
from importlib.util import find_spec
from typing import Any, Literal

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.qcompute.capabilities import CAP_QCOMPUTE_ENV_PROBE
from metaharness_ext.qcompute.contracts import (
    QComputeCalibrationData,
    QComputeEnvironmentReport,
    QComputeExperimentSpec,
)
from metaharness_ext.qcompute.slots import QCOMPUTE_ENVIRONMENT_SLOT


class _QuafuProbeResult:
    def __init__(
        self,
        *,
        available: bool,
        status: str,
        prerequisite_errors: list[str],
        qubit_count_available: int | None = None,
        queue_depth: int | None = None,
        estimated_wait_seconds: int | None = None,
        calibration_data: QComputeCalibrationData | None = None,
    ) -> None:
        self.available = available
        self.status = status
        self.prerequisite_errors = prerequisite_errors
        self.qubit_count_available = qubit_count_available
        self.queue_depth = queue_depth
        self.estimated_wait_seconds = estimated_wait_seconds
        self.calibration_data = calibration_data


class QComputeEnvironmentProbeComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(QCOMPUTE_ENVIRONMENT_SLOT)
        api.declare_input("task", "QComputeExperimentSpec")
        api.declare_output("environment", "QComputeEnvironmentReport", mode="sync")
        api.provide_capability(CAP_QCOMPUTE_ENV_PROBE)

    def probe(self, spec: QComputeExperimentSpec) -> QComputeEnvironmentReport:
        prerequisite_errors: list[str] = []
        status = "online"
        available = True
        qubit_count_available = spec.backend.qubit_count
        queue_depth = 0 if spec.backend.simulator else None
        estimated_wait_seconds = 0 if spec.backend.simulator else None

        supported_platforms = {"qiskit_aer", "pennylane_aer", "quafu"}
        if spec.backend.platform not in supported_platforms:
            available = False
            status = "unsupported_platform"
            prerequisite_errors.append(
                f"Unsupported backend platform for current executor: {spec.backend.platform}"
            )
        elif spec.backend.platform == "qiskit_aer":
            if find_spec("qiskit") is None or find_spec("qiskit_aer") is None:
                available = False
                status = "dependency_missing"
                prerequisite_errors.append("qiskit and qiskit_aer must be installed for qiskit_aer")
            elif not spec.backend.simulator:
                available = False
                status = "invalid_backend_spec"
                prerequisite_errors.append("qiskit_aer backend must declare simulator=True")
        elif spec.backend.platform == "pennylane_aer":
            if find_spec("pennylane") is None:
                available = False
                status = "dependency_missing"
                prerequisite_errors.append("pennylane must be installed for pennylane_aer")
        elif spec.backend.platform == "quafu":
            quafu_probe = self._probe_quafu(spec, prerequisite_errors)
            available = quafu_probe.available
            status = quafu_probe.status
            prerequisite_errors = quafu_probe.prerequisite_errors
            if available and quafu_probe.qubit_count_available is not None:
                qubit_count_available = quafu_probe.qubit_count_available
                queue_depth = quafu_probe.queue_depth
                estimated_wait_seconds = quafu_probe.estimated_wait_seconds

        if qubit_count_available is not None and spec.circuit.num_qubits > qubit_count_available:
            available = False
            status = "insufficient_qubits"
            prerequisite_errors.append(
                "Circuit requires more qubits than declared backend capacity"
            )

        token_env = spec.backend.api_token_env or spec.execution_policy.api_token_env
        if spec.execution_policy.requires_api_token:
            if token_env is None:
                available = False
                status = "missing_api_token"
                prerequisite_errors.append("Execution policy requires api_token_env")
            elif not os.getenv(token_env):
                available = False
                status = "missing_api_token"
                prerequisite_errors.append(f"Missing API token environment variable: {token_env}")

        calibration_data = None
        if spec.backend.platform == "quafu" and "quafu_probe" in locals():
            calibration_data = quafu_probe.calibration_data

        calibration_fresh = spec.noise is None or spec.noise.model != "real"
        if spec.noise is not None and spec.noise.model == "real":
            if calibration_data is None:
                available = False
                status = "calibration_unavailable"
                prerequisite_errors.append(
                    "Real-noise execution requires calibration-backed noise data"
                )
            else:
                calibration_fresh = True
        blocks_promotion = not available or bool(prerequisite_errors)

        # Build ResourceQuota if daily_quota is configured
        quota_snapshot = None
        if spec.execution_policy.daily_quota is not None:
            from metaharness.sdk.execution import ResourceQuota

            quota_snapshot = ResourceQuota(
                resource_type="api_calls",
                provider=spec.backend.platform,
                limit=spec.execution_policy.daily_quota,
                metadata={"chip_id": spec.backend.chip_id},
            )

        return QComputeEnvironmentReport(
            task_id=spec.task_id,
            backend=spec.backend,
            available=available,
            status=status,
            qubit_count_available=qubit_count_available,
            queue_depth=queue_depth,
            estimated_wait_seconds=estimated_wait_seconds,
            calibration_fresh=calibration_fresh,
            calibration_data=calibration_data,
            prerequisite_errors=prerequisite_errors,
            blocks_promotion=blocks_promotion,
            quota_snapshot=quota_snapshot,
        )

    # ------------------------------------------------------------------
    # Quafu platform helpers
    # ------------------------------------------------------------------

    def _probe_quafu(
        self,
        spec: QComputeExperimentSpec,
        prerequisite_errors: list[str],
    ) -> _QuafuProbeResult:
        from metaharness_ext.qcompute.backends.quafu import _detect_quark

        task_cls = _detect_quark()
        if task_cls is None:
            prerequisite_errors.append(
                "quarkstudio must be installed for quafu backend (pip install quarkstudio)"
            )
            return _QuafuProbeResult(
                available=False,
                status="dependency_missing",
                prerequisite_errors=prerequisite_errors,
            )

        token_env = spec.backend.api_token_env or "Qcompute_Token"
        token = os.getenv(token_env)
        if not token:
            prerequisite_errors.append(f"Missing Quafu API token: {token_env}")
            return _QuafuProbeResult(
                available=False,
                status="missing_api_token",
                prerequisite_errors=prerequisite_errors,
            )

        chip_id = spec.backend.chip_id or "Baihua"
        try:
            tmgr = task_cls(token=token)
            chip_statuses = tmgr.status()
            chip_status = self._extract_chip_status(chip_statuses, chip_id)
            chip_payload = self._extract_chip_payload(chip_statuses, chip_id)
            calibration_data = self._normalize_calibration_data(
                self._query_calibration(chip_id, tmgr)
            )
            queue_depth = self._query_chip_status(chip_id, tmgr, chip_payload)

            if isinstance(chip_status, str) and chip_status in {"Maintenance", "Calibrating"}:
                prerequisite_errors.append(f"Chip {chip_id} is {chip_status}")
                return _QuafuProbeResult(
                    available=False,
                    status=f"chip_{chip_status.lower()}",
                    prerequisite_errors=prerequisite_errors,
                    queue_depth=queue_depth,
                    calibration_data=calibration_data,
                )

            qubit_count_available = self._extract_qubit_count(chip_status, chip_payload)
        except Exception as exc:
            prerequisite_errors.append(f"Quafu connection error: {exc}")
            return _QuafuProbeResult(
                available=False,
                status="connection_error",
                prerequisite_errors=prerequisite_errors,
            )

        if calibration_data is not None:
            freshness = self._check_calibration_freshness(calibration_data.timestamp)
            if freshness == "very_stale":
                prerequisite_errors.append(
                    f"Calibration data for chip {chip_id} is very stale (>24h)"
                )
                return _QuafuProbeResult(
                    available=False,
                    status="calibration_stale",
                    prerequisite_errors=prerequisite_errors,
                    qubit_count_available=qubit_count_available,
                    queue_depth=queue_depth,
                    calibration_data=calibration_data,
                )
            if freshness == "stale":
                prerequisite_errors.append(
                    f"Warning: calibration data for chip {chip_id} is stale (3-24h)"
                )

        return _QuafuProbeResult(
            available=True,
            status="online",
            prerequisite_errors=prerequisite_errors,
            qubit_count_available=qubit_count_available,
            queue_depth=queue_depth,
            calibration_data=calibration_data,
        )

    def _check_calibration_freshness(
        self, calibration_timestamp: datetime
    ) -> Literal["fresh", "stale", "very_stale"]:
        """Classify calibration freshness based on age.

        - fresh: < 3 hours old
        - stale: 3-24 hours (warning, not blocking)
        - very_stale: > 24 hours (blocks promotion)
        """
        now = datetime.now(timezone.utc)
        if calibration_timestamp.tzinfo is None:
            calibration_timestamp = calibration_timestamp.replace(tzinfo=timezone.utc)
        age_seconds = (now - calibration_timestamp).total_seconds()
        age_hours = age_seconds / 3600.0

        if age_hours < 3.0:
            return "fresh"
        if age_hours < 24.0:
            return "stale"
        return "very_stale"

    def _query_chip_status(
        self,
        chip_id: str,
        tmgr: Any | None = None,
        chip_payload: Any | None = None,
    ) -> int | None:
        for payload in (chip_payload, self._call_optional_sdk_method(tmgr, "snapshot", chip_id)):
            queue_depth = self._extract_int_field(
                payload,
                ("queue_depth", "queue", "queue_size", "pending_tasks"),
            )
            if queue_depth is not None:
                return queue_depth
        return None

    def _query_calibration(
        self,
        chip_id: str,
        tmgr: Any | None = None,
    ) -> QComputeCalibrationData | None:
        for payload in self._calibration_payload_candidates(chip_id, tmgr):
            calibration_data = self._build_calibration_data(payload)
            if calibration_data is not None:
                return calibration_data
        return None

    def _calibration_payload_candidates(self, chip_id: str, tmgr: Any | None) -> list[Any]:
        candidates: list[Any] = []
        for method_name in ("get_backend_info", "backend_info", "calibration", "snapshot"):
            for args in ((chip_id,), ()):
                payload = self._call_optional_sdk_method(tmgr, method_name, *args)
                if payload is not None:
                    candidates.append(payload)
        if tmgr is not None:
            candidates.append(getattr(tmgr, "backend", None))
        return candidates

    def _call_optional_sdk_method(self, target: Any, method_name: str, *args: Any) -> Any | None:
        if target is None:
            return None
        method = getattr(target, method_name, None)
        if not callable(method):
            return None
        try:
            return method(*args)
        except TypeError:
            return None

    def _normalize_calibration_data(self, payload: Any) -> QComputeCalibrationData | None:
        if isinstance(payload, QComputeCalibrationData):
            return payload
        if isinstance(payload, datetime):
            return QComputeCalibrationData(timestamp=payload)
        return self._build_calibration_data(payload)

    def _build_calibration_data(self, payload: Any) -> QComputeCalibrationData | None:
        payload = self._unwrap_payload(payload)
        if not isinstance(payload, Mapping):
            return None
        timestamp = self._extract_timestamp(payload)
        if timestamp is None:
            return None
        return QComputeCalibrationData(
            timestamp=timestamp,
            t1_us_avg=self._extract_float_field(payload, ("t1_us_avg", "avg_t1_us", "t1_avg")),
            t2_us_avg=self._extract_float_field(payload, ("t2_us_avg", "avg_t2_us", "t2_avg")),
            single_qubit_gate_fidelity_avg=self._extract_float_field(
                payload,
                ("single_qubit_gate_fidelity_avg", "single_gate_fidelity", "single_qubit_fidelity"),
            ),
            two_qubit_gate_fidelity_avg=self._extract_float_field(
                payload,
                ("two_qubit_gate_fidelity_avg", "two_qubit_gate_fidelity", "two_qubit_fidelity"),
            ),
            readout_fidelity_avg=self._extract_float_field(
                payload,
                ("readout_fidelity_avg", "readout_fidelity", "readout_fidelity_mean"),
            ),
            qubit_connectivity=self._extract_connectivity(payload),
        )

    def _extract_chip_payload(self, chip_statuses: Any, chip_id: str) -> Any | None:
        if not isinstance(chip_statuses, Mapping):
            return None
        payload = chip_statuses.get(chip_id)
        if payload is not None:
            return payload
        for key in ("backends", "backend", "chips", "devices"):
            nested = chip_statuses.get(key)
            if isinstance(nested, Mapping) and chip_id in nested:
                return nested[chip_id]
        return None

    def _extract_chip_status(self, chip_statuses: Any, chip_id: str) -> Any:
        chip_payload = self._extract_chip_payload(chip_statuses, chip_id)
        if isinstance(chip_payload, Mapping):
            for key in ("status", "state", "availability"):
                if key in chip_payload:
                    return chip_payload[key]
        return chip_payload if chip_payload is not None else "unknown"

    def _extract_qubit_count(self, chip_status: Any, chip_payload: Any | None) -> int | None:
        if isinstance(chip_status, int):
            return chip_status
        return self._extract_int_field(
            chip_payload, ("qubit_count", "qubits", "n_qubits", "num_qubits")
        )

    def _unwrap_payload(self, payload: Any) -> Any:
        if not isinstance(payload, Mapping):
            return payload
        for key in ("calibration", "calibration_data", "data", "backend_info"):
            nested = payload.get(key)
            if isinstance(nested, Mapping):
                return nested
        return payload

    def _extract_timestamp(self, payload: Mapping[str, Any]) -> datetime | None:
        for key in ("timestamp", "calibration_timestamp", "calibration_time", "calibration_date"):
            value = payload.get(key)
            if isinstance(value, datetime):
                return value
            if isinstance(value, str):
                try:
                    return datetime.fromisoformat(value.replace("Z", "+00:00"))
                except ValueError:
                    continue
        return None

    def _extract_int_field(self, payload: Any, keys: tuple[str, ...]) -> int | None:
        if not isinstance(payload, Mapping):
            return None
        for key in keys:
            value = payload.get(key)
            if value is not None:
                try:
                    return int(value)
                except (TypeError, ValueError):
                    continue
        return None

    def _extract_float_field(
        self, payload: Mapping[str, Any], keys: tuple[str, ...]
    ) -> float | None:
        for key in keys:
            value = payload.get(key)
            if value is not None:
                try:
                    return float(value)
                except (TypeError, ValueError):
                    continue
        return None

    def _extract_connectivity(self, payload: Mapping[str, Any]) -> list[tuple[int, int]] | None:
        value = payload.get("qubit_connectivity") or payload.get("coupling_map")
        if not isinstance(value, list):
            return None
        connectivity: list[tuple[int, int]] = []
        for edge in value:
            if isinstance(edge, (list, tuple)) and len(edge) == 2:
                connectivity.append((int(edge[0]), int(edge[1])))
        return connectivity or None
