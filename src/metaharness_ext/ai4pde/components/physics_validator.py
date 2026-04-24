from __future__ import annotations

from metaharness.core.models import BudgetState, ScoredEvidence, SessionEventType
from metaharness.observability.events import make_session_event
from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.ai4pde.capabilities import (
    CAP_BOUNDARY_VALIDATION,
    CAP_REFERENCE_BASELINE,
    CAP_RESIDUAL_VALIDATION,
)
from metaharness_ext.ai4pde.contracts import (
    CandidateIdentity,
    PDERunArtifact,
    PromotionMetadata,
    ReferenceResult,
    RollbackContext,
    SafetyEvaluation,
    ValidationBundle,
)
from metaharness_ext.ai4pde.slots import PHYSICS_VALIDATOR_SLOT
from metaharness_ext.ai4pde.types import NextAction
from metaharness_ext.ai4pde.validation import (
    compare_against_reference,
    summarize_boundary_conditions,
    summarize_residuals,
)


class PhysicsValidatorComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(PHYSICS_VALIDATOR_SLOT)
        api.declare_input("run_artifact", "PDERunArtifact")
        api.declare_output("validation_bundle", "ValidationBundle", mode="sync")
        api.provide_capability(CAP_RESIDUAL_VALIDATION)
        api.provide_capability(CAP_BOUNDARY_VALIDATION)
        api.require_capability(CAP_REFERENCE_BASELINE)

    def validate_run(
        self,
        run_artifact: PDERunArtifact,
        *,
        graph_version_id: int = 1,
        reference_result: ReferenceResult | None = None,
    ) -> ValidationBundle:
        residual_metrics = summarize_residuals(run_artifact)
        boundary_metrics = summarize_boundary_conditions(run_artifact)
        reference_comparison = (
            compare_against_reference(run_artifact, reference_result)
            if reference_result is not None
            else {}
        )
        violations: list[str] = []
        if residual_metrics["residual_ok"] < 1.0:
            violations.append("residual_threshold_exceeded")
        if boundary_metrics["boundary_ok"] < 1.0:
            violations.append("boundary_conditions_failed")
        if reference_comparison.get("status") == "worse_than_baseline":
            violations.append("baseline_divergence_exceeded")
        next_action = NextAction.ACCEPT if not violations else NextAction.RETRY
        candidate_identity = CandidateIdentity(
            candidate_id=run_artifact.run_id,
            graph_version_id=graph_version_id,
            solver_family=run_artifact.solver_family,
        )
        protection_violations = [
            violation
            for violation in violations
            if "baseline" in violation or "boundary" in violation
        ]
        session_events = [
            make_session_event(
                run_artifact.task_id,
                SessionEventType.CANDIDATE_VALIDATED,
                graph_version=graph_version_id,
                candidate_id=run_artifact.run_id,
                payload={
                    "validation_id": f"validation-{run_artifact.task_id}",
                    "next_action": next_action.value,
                    "violations": list(violations),
                },
            )
        ]
        if violations:
            session_events.append(
                make_session_event(
                    run_artifact.task_id,
                    SessionEventType.CANDIDATE_REJECTED,
                    graph_version=graph_version_id,
                    candidate_id=run_artifact.run_id,
                    payload={"violations": list(violations)},
                )
            )
        residual_score = max(0.0, 1.0 - float(residual_metrics.get("residual_l2", 1.0)))
        boundary_score = max(0.0, 1.0 - float(boundary_metrics.get("boundary_error", 1.0)))
        reference_score = (
            1.0 if reference_comparison.get("status") != "worse_than_baseline" else 0.0
        )
        score = (residual_score + boundary_score + reference_score) / 3.0
        scored_evidence = ScoredEvidence(
            score=score,
            metrics={
                "residual_l2": float(residual_metrics.get("residual_l2", 0.0)),
                "boundary_error": float(boundary_metrics.get("boundary_error", 0.0)),
                "reference_ok": reference_score,
            },
            safety_score=1.0 if not protection_violations else 0.0,
            budget=BudgetState(
                **{
                    k: v
                    for k, v in {
                        "used": 0,
                        "limit": None,
                        "remaining": None,
                        "exhausted": False,
                    }.items()
                }
            ),
            evidence_refs=[
                f"validation://{run_artifact.task_id}",
                f"provenance://ai4pde/validation/{run_artifact.task_id}",
            ],
            reasons=list(violations),
            attributes={
                "next_action": next_action.value,
                "reference_status": reference_comparison.get("status", "not_run"),
            },
        )
        provenance = {
            "candidate_id": run_artifact.run_id,
            "graph_version_id": graph_version_id,
            "validation_id": f"validation-{run_artifact.task_id}",
            "lineage": [
                f"run://{run_artifact.run_id}",
                f"reference://{reference_result.reference_id}"
                if reference_result is not None
                else None,
            ],
        }
        provenance["lineage"] = [entry for entry in provenance["lineage"] if entry is not None]
        return ValidationBundle(
            validation_id=f"validation-{run_artifact.task_id}",
            task_id=run_artifact.task_id,
            graph_version_id=graph_version_id,
            residual_metrics=residual_metrics,
            bc_ic_metrics=boundary_metrics,
            reference_comparison=reference_comparison,
            violations=violations,
            next_action=next_action,
            summary={
                "status": next_action.value,
                "residual_l2": residual_metrics["residual_l2"],
                "boundary_error": boundary_metrics["boundary_error"],
                "reference_status": reference_comparison.get("status", "not_run"),
            },
            promotion_metadata=PromotionMetadata(candidate_identity=candidate_identity),
            candidate_identity=candidate_identity,
            safety_evaluation=SafetyEvaluation(
                outcome=("allowed" if next_action == NextAction.ACCEPT else "rejected"),
                protection={
                    "protected_components": ["physics_validator"],
                    "violations": protection_violations,
                    "allowed": not protection_violations,
                },
                details={"reference_status": reference_comparison.get("status", "not_run")},
            ),
            rollback_context=RollbackContext(
                rollback_recommended=reference_comparison.get("status") == "worse_than_baseline",
                rollback_reason=(
                    "baseline_divergence_exceeded"
                    if reference_comparison.get("status") == "worse_than_baseline"
                    else None
                ),
            ),
            scored_evidence=scored_evidence,
            session_events=session_events,
            provenance=provenance,
        )
