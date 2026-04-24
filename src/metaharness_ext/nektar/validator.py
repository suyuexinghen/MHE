from __future__ import annotations

from metaharness.core.models import BudgetState, ConvergenceState, ScoredEvidence
from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.nektar.capabilities import CAP_NEKTAR_VALIDATE
from metaharness_ext.nektar.contracts import NektarRunArtifact, NektarValidationReport
from metaharness_ext.nektar.slots import VALIDATOR_SLOT


class NektarValidatorComponent(HarnessComponent):
    protected = True

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(VALIDATOR_SLOT)
        api.declare_input("run", "NektarRunArtifact")
        api.declare_output("validation", "NektarValidationReport", mode="sync")
        api.provide_capability(CAP_NEKTAR_VALIDATE)

    def validate_run(self, artifact: NektarRunArtifact) -> NektarValidationReport:
        exit_code = artifact.result_summary.get("exit_code")
        field_files_exist = bool(artifact.field_files or artifact.filter_output.checkpoint_files)
        solver_exited_cleanly = exit_code == 0
        messages: list[str] = []
        fallback_reason = artifact.result_summary.get("fallback_reason")
        if fallback_reason:
            messages.append(f"Solver did not run: {fallback_reason}.")
        elif exit_code is None:
            messages.append("Solver exit code unavailable.")
        elif exit_code != 0:
            messages.append(f"Solver exited with code {exit_code}.")
        if not field_files_exist:
            messages.append("No field or checkpoint outputs were produced.")

        error_vs_reference = self._evaluate_error_vs_reference(artifact)
        if error_vs_reference is True:
            messages.append("Reference error is within tolerance.")
        elif error_vs_reference is False:
            messages.append("Reference error exceeds tolerance.")

        passed = solver_exited_cleanly and field_files_exist and error_vs_reference is not False
        if passed:
            messages.append("Solver exited cleanly and produced output artifacts.")
        postprocess_summary = artifact.result_summary.get("postprocess")
        if isinstance(postprocess_summary, dict):
            pp_status = postprocess_summary.get("status")
            if pp_status == "completed":
                messages.append("FieldConvert postprocessing completed successfully.")
            elif pp_status == "failed":
                messages.append(
                    f"FieldConvert postprocessing failed: {postprocess_summary.get('fallback_reason', 'unknown')}."
                )
            elif pp_status == "skipped":
                messages.append("FieldConvert postprocessing was skipped.")
            elif pp_status == "unavailable":
                messages.append(
                    f"FieldConvert postprocessing unavailable: {postprocess_summary.get('fallback_reason', 'unknown')}."
                )
        metrics: dict[str, float | str] = {
            "output_file_count": len(artifact.field_files)
            + len(artifact.filter_output.checkpoint_files),
        }
        if artifact.filter_output.error_norms:
            metrics.update(artifact.filter_output.error_norms)
        if artifact.filter_output.metrics:
            metrics.update(artifact.filter_output.metrics)
            if artifact.solver_family.name == "INCNS":
                if "incns_velocity_iterations" in artifact.filter_output.metrics:
                    messages.append("IncNS velocity system convergence metrics were captured.")
                if "incns_pressure_iterations" in artifact.filter_output.metrics:
                    messages.append("IncNS pressure system convergence metrics were captured.")
                if "incns_newton_iterations" in artifact.filter_output.metrics:
                    messages.append("IncNS Newton iteration metrics were captured.")
        evidence_refs = list(
            dict.fromkeys(
                [*artifact.checkpoint_refs, *artifact.trace_refs, *artifact.provenance_refs]
            )
        )
        scored_evidence = ScoredEvidence(
            score=1.0 if passed else 0.0,
            metrics={
                key: float(value)
                for key, value in metrics.items()
                if isinstance(value, int | float)
            },
            safety_score=1.0 if passed else 0.0,
            budget=BudgetState(used=1, exhausted=not passed),
            convergence=ConvergenceState(
                converged=passed,
                criteria_met=["solver_exit_clean", "outputs_present"] if passed else [],
                reason="validator accepted run" if passed else "validator rejected run",
            ),
            evidence_refs=evidence_refs,
            reasons=list(messages),
            attributes={"status": artifact.status, "solver_family": artifact.solver_family.value},
        )
        return NektarValidationReport(
            task_id=artifact.task_id,
            passed=passed,
            solver_exited_cleanly=solver_exited_cleanly,
            field_files_exist=field_files_exist,
            error_vs_reference=error_vs_reference,
            messages=messages,
            metrics=metrics,
            checkpoint_refs=list(artifact.checkpoint_refs),
            provenance_refs=list(artifact.provenance_refs),
            trace_refs=list(artifact.trace_refs),
            scored_evidence=scored_evidence,
        )

    def _evaluate_error_vs_reference(self, artifact: NektarRunArtifact) -> bool | None:
        if not artifact.filter_output.error_norms:
            return None
        tolerance = float(artifact.result_summary.get("error_tolerance", 1e-3))
        l2_values: list[float] = []
        for key, value in artifact.filter_output.error_norms.items():
            if "l2" not in key.lower():
                continue
            try:
                l2_values.append(float(value))
            except (TypeError, ValueError):
                continue
        if not l2_values:
            return None
        return max(l2_values) <= tolerance
