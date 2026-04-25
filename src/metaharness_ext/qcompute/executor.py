from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.qcompute.backends.qiskit_aer import QiskitAerBackend
from metaharness_ext.qcompute.capabilities import CAP_QCOMPUTE_CIRCUIT_RUN
from metaharness_ext.qcompute.contracts import (
    QComputeEnvironmentReport,
    QComputeRunArtifact,
    QComputeRunPlan,
)
from metaharness_ext.qcompute.slots import QCOMPUTE_EXECUTOR_SLOT


class QComputeExecutorComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(QCOMPUTE_EXECUTOR_SLOT)
        api.declare_input("plan", "QComputeRunPlan")
        api.declare_input("environment", "QComputeEnvironmentReport", required=False)
        api.declare_output("run", "QComputeRunArtifact", mode="sync")
        api.provide_capability(CAP_QCOMPUTE_CIRCUIT_RUN)

    def execute_plan(
        self,
        plan: QComputeRunPlan,
        environment_report: QComputeEnvironmentReport | None = None,
    ) -> QComputeRunArtifact:
        run_dir = self._resolve_run_dir(plan)
        if environment_report is not None and not environment_report.available:
            return self._failed_artifact(
                plan,
                run_dir=run_dir,
                error_message=(
                    f"Environment probe reported unavailable backend: {environment_report.status}"
                ),
                terminal_error_type="environment_unavailable",
            )

        if plan.target_backend.platform != "qiskit_aer":
            return self._failed_artifact(
                plan,
                run_dir=run_dir,
                error_message=f"Unsupported backend platform: {plan.target_backend.platform}",
                terminal_error_type="unsupported_backend",
            )

        try:
            circuit = self._load_circuit(plan.circuit_openqasm)
            result = QiskitAerBackend().run(
                circuit=circuit,
                shots=plan.execution_params.shots,
                noise=plan.noise,
            )
        except Exception as error:
            return self._failed_artifact(
                plan,
                run_dir=run_dir,
                error_message=str(error),
                terminal_error_type=type(error).__name__,
            )

        raw_output_path = run_dir / "result.json"
        raw_output_path.write_text(json.dumps(result, sort_keys=True, indent=2))
        return QComputeRunArtifact(
            artifact_id=f"{plan.plan_id}-artifact-{uuid.uuid4().hex[:8]}",
            plan_ref=plan.plan_id,
            backend_actual="qiskit_aer",
            status="completed",
            counts=result["counts"],
            probabilities=result["probabilities"],
            execution_time_ms=result["execution_time_ms"],
            raw_output_path=str(raw_output_path),
            shots_requested=plan.execution_params.shots,
            shots_completed=result["shots_completed"],
            graph_metadata=dict(plan.graph_metadata),
            candidate_identity=plan.candidate_identity.model_copy(deep=True),
            promotion_metadata=plan.promotion_metadata.model_copy(deep=True),
            checkpoint_refs=list(plan.checkpoint_refs),
            provenance_refs=list(plan.provenance_refs),
            trace_refs=list(plan.trace_refs),
            execution_policy=plan.execution_policy.model_copy(deep=True),
        )

    def _resolve_run_dir(self, plan: QComputeRunPlan) -> Path:
        runtime = getattr(self, "_runtime", None)
        if runtime is None or runtime.storage_path is None:
            raise RuntimeError("QComputeExecutorComponent requires runtime.storage_path")
        self._validate_id(plan.experiment_ref)
        self._validate_id(plan.plan_id)
        run_dir = runtime.storage_path / "qcompute_runs" / plan.experiment_ref / plan.plan_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def _validate_id(self, value: str) -> None:
        if not value or ".." in value or "/" in value or "\\" in value:
            raise ValueError(f"Invalid identifier: {value!r}")

    def _load_circuit(self, openqasm: str) -> Any:
        from qiskit import QuantumCircuit

        return QuantumCircuit.from_qasm_str(openqasm)

    def _failed_artifact(
        self,
        plan: QComputeRunPlan,
        *,
        run_dir: Path,
        error_message: str,
        terminal_error_type: str,
    ) -> QComputeRunArtifact:
        raw_output_path = run_dir / "result.json"
        raw_output_path.write_text(
            json.dumps(
                {
                    "status": "failed",
                    "error_message": error_message,
                    "terminal_error_type": terminal_error_type,
                },
                sort_keys=True,
                indent=2,
            )
        )
        return QComputeRunArtifact(
            artifact_id=f"{plan.plan_id}-artifact-{uuid.uuid4().hex[:8]}",
            plan_ref=plan.plan_id,
            backend_actual=plan.target_backend.platform,
            status="failed",
            raw_output_path=str(raw_output_path),
            error_message=error_message,
            shots_requested=plan.execution_params.shots,
            shots_completed=0,
            terminal_error_type=terminal_error_type,
            graph_metadata=dict(plan.graph_metadata),
            candidate_identity=plan.candidate_identity.model_copy(deep=True),
            promotion_metadata=plan.promotion_metadata.model_copy(deep=True),
            checkpoint_refs=list(plan.checkpoint_refs),
            provenance_refs=list(plan.provenance_refs),
            trace_refs=list(plan.trace_refs),
            execution_policy=plan.execution_policy.model_copy(deep=True),
        )
