from __future__ import annotations

import os
from datetime import datetime, timezone
from importlib.util import find_spec
from typing import Literal

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.qcompute.capabilities import CAP_QCOMPUTE_ENV_PROBE
from metaharness_ext.qcompute.contracts import QComputeEnvironmentReport, QComputeExperimentSpec
from metaharness_ext.qcompute.slots import QCOMPUTE_ENVIRONMENT_SLOT


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
            available, status, prerequisite_errors = self._probe_quafu(spec, prerequisite_errors)
            if available:
                queue_depth = self._query_chip_status(spec.backend.chip_id or "default")
                estimated_wait_seconds = None

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

        calibration_fresh = spec.noise is None or spec.noise.model != "real"
        if spec.noise is not None and spec.noise.model == "real":
            available = False
            status = "calibration_unavailable"
            prerequisite_errors.append(
                "Real-noise execution requires calibration-backed noise data, which Phase 1 does not provide"
            )
        blocks_promotion = not available or bool(prerequisite_errors)
        return QComputeEnvironmentReport(
            task_id=spec.task_id,
            backend=spec.backend,
            available=available,
            status=status,
            qubit_count_available=qubit_count_available,
            queue_depth=queue_depth,
            estimated_wait_seconds=estimated_wait_seconds,
            calibration_fresh=calibration_fresh,
            prerequisite_errors=prerequisite_errors,
            blocks_promotion=blocks_promotion,
        )

    # ------------------------------------------------------------------
    # Quafu platform helpers
    # ------------------------------------------------------------------

    def _probe_quafu(
        self,
        spec: QComputeExperimentSpec,
        prerequisite_errors: list[str],
    ) -> tuple[bool, str, list[str]]:
        """Probe Quafu platform availability.

        Returns (available, status, prerequisite_errors).
        """
        if find_spec("pyquafu") is None:
            prerequisite_errors.append("pyquafu must be installed for quafu backend")
            return False, "dependency_missing", prerequisite_errors

        token_env = spec.backend.api_token_env or "QUAFU_API_TOKEN"
        token = os.getenv(token_env)
        if not token:
            prerequisite_errors.append(f"Missing Quafu API token: {token_env}")
            return False, "missing_api_token", prerequisite_errors

        # Check calibration freshness for the target chip.
        chip_id = spec.backend.chip_id or "default"
        calibration = self._query_calibration(chip_id)
        if calibration is not None:
            freshness = self._check_calibration_freshness(calibration)
            if freshness == "very_stale":
                prerequisite_errors.append(
                    f"Calibration data for chip {chip_id} is very stale (>24h)"
                )
                return False, "calibration_stale", prerequisite_errors
            if freshness == "stale":
                prerequisite_errors.append(
                    f"Warning: calibration data for chip {chip_id} is stale (3-24h)"
                )

        return True, "online", prerequisite_errors

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

    def _query_chip_status(self, chip_id: str) -> int:
        """Query the queue depth for *chip_id*.

        Placeholder implementation -- returns 0.  Override or mock for
        real integration testing.
        """
        return 0

    def _query_calibration(self, chip_id: str) -> datetime | None:
        """Query the latest calibration timestamp for *chip_id*.

        Placeholder implementation -- returns ``None`` (unknown).
        Override or mock for real integration testing.
        """
        return None
