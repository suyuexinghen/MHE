from __future__ import annotations

import os
from importlib.util import find_spec

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

        supported_platforms = {"qiskit_aer", "pennylane_aer"}
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
