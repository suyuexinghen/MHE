from __future__ import annotations

from metaharness.core.models import (
    BudgetState,
    ConvergenceState,
    ScoredEvidence,
    ValidationIssue,
    ValidationIssueCategory,
)
from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.qcompute.capabilities import CAP_QCOMPUTE_RESULT_VALIDATE
from metaharness_ext.qcompute.contracts import (
    QComputeEnvironmentReport,
    QComputeEvidenceBundle,
    QComputeRunArtifact,
    QComputeRunPlan,
    QComputeValidationMetrics,
    QComputeValidationReport,
)
from metaharness_ext.qcompute.evidence import build_evidence_bundle
from metaharness_ext.qcompute.slots import QCOMPUTE_VALIDATOR_SLOT
from metaharness_ext.qcompute.types import QComputeValidationStatus


class QComputeValidatorComponent(HarnessComponent):
    protected = True

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(QCOMPUTE_VALIDATOR_SLOT)
        api.declare_input("run", "QComputeRunArtifact")
        api.declare_input("plan", "QComputeRunPlan")
        api.declare_input("environment", "QComputeEnvironmentReport")
        api.declare_output("validation", "QComputeValidationReport", mode="sync")
        api.provide_capability(CAP_QCOMPUTE_RESULT_VALIDATE)

    def validate_run(
        self,
        artifact: QComputeRunArtifact,
        plan: QComputeRunPlan,
        environment: QComputeEnvironmentReport,
    ) -> QComputeValidationReport:
        issues: list[ValidationIssue] = []
        evidence_refs = self._build_evidence_refs(artifact, plan, environment)
        metrics = QComputeValidationMetrics(
            fidelity=plan.estimated_fidelity,
            circuit_depth_executed=plan.estimated_depth,
            swap_count_executed=plan.estimated_swap_count,
            noise_impact_score=self._noise_impact_score(plan),
            gate_error_accumulation=self._gate_error_accumulation(plan),
            readout_confidence=self._readout_confidence(plan),
            syntax_valid=True,
        )

        if not environment.available or environment.blocks_promotion:
            issues.append(
                ValidationIssue(
                    code="qcompute_environment_invalid",
                    message=f"QCompute environment status is {environment.status}.",
                    subject=environment.task_id,
                    category=ValidationIssueCategory.READINESS,
                    blocks_promotion=True,
                )
            )
            return self._build_report(
                artifact,
                plan,
                status=QComputeValidationStatus.ENVIRONMENT_INVALID,
                passed=False,
                metrics=metrics,
                issues=issues,
                evidence_refs=evidence_refs,
            )

        if artifact.backend_actual != plan.target_backend.platform:
            issues.append(
                ValidationIssue(
                    code="qcompute_backend_mismatch",
                    message=(
                        f"Run backend {artifact.backend_actual} does not match plan backend "
                        f"{plan.target_backend.platform}."
                    ),
                    subject=artifact.artifact_id,
                    category=ValidationIssueCategory.READINESS,
                    blocks_promotion=True,
                )
            )
            return self._build_report(
                artifact,
                plan,
                status=QComputeValidationStatus.BACKEND_UNAVAILABLE,
                passed=False,
                metrics=metrics,
                issues=issues,
                evidence_refs=evidence_refs,
            )

        if artifact.status != "completed" or artifact.error_message:
            issues.append(
                ValidationIssue(
                    code="qcompute_execution_failed",
                    message=artifact.error_message or f"Run status is {artifact.status}.",
                    subject=artifact.artifact_id,
                    category=ValidationIssueCategory.READINESS,
                    blocks_promotion=True,
                )
            )
            return self._build_report(
                artifact,
                plan,
                status=QComputeValidationStatus.EXECUTION_FAILED,
                passed=False,
                metrics=metrics,
                issues=issues,
                evidence_refs=evidence_refs,
            )

        requested_shots = plan.execution_params.shots
        completed_shots = artifact.shots_completed or sum((artifact.counts or {}).values())
        if completed_shots < requested_shots or not (artifact.counts or artifact.statevector):
            issues.append(
                ValidationIssue(
                    code="qcompute_result_incomplete",
                    message="QCompute result is missing counts/statevector or completed shots.",
                    subject=artifact.artifact_id,
                    category=ValidationIssueCategory.PROMOTION_BLOCKER,
                    blocks_promotion=True,
                )
            )
            return self._build_report(
                artifact,
                plan,
                status=QComputeValidationStatus.RESULT_INCOMPLETE,
                passed=False,
                metrics=metrics,
                issues=issues,
                evidence_refs=evidence_refs,
            )

        threshold = plan.compilation_metadata.get("fidelity_threshold")
        if isinstance(threshold, int | float) and metrics.fidelity is not None:
            if metrics.fidelity < float(threshold):
                issues.append(
                    ValidationIssue(
                        code="qcompute_fidelity_below_threshold",
                        message=f"Estimated fidelity {metrics.fidelity:.6f} is below {threshold}.",
                        subject=artifact.artifact_id,
                        category=ValidationIssueCategory.SEMANTIC,
                        blocks_promotion=True,
                    )
                )
                return self._build_report(
                    artifact,
                    plan,
                    status=QComputeValidationStatus.BELOW_FIDELITY_THRESHOLD,
                    passed=False,
                    metrics=metrics,
                    issues=issues,
                    evidence_refs=evidence_refs,
                )

        if metrics.noise_impact_score is not None and metrics.noise_impact_score >= 0.5:
            issues.append(
                ValidationIssue(
                    code="qcompute_noise_impact_high",
                    message=f"Noise impact score {metrics.noise_impact_score:.6f} is high.",
                    subject=artifact.artifact_id,
                    category=ValidationIssueCategory.SEMANTIC,
                    blocks_promotion=False,
                )
            )
            return self._build_report(
                artifact,
                plan,
                status=QComputeValidationStatus.NOISE_CORRUPTED,
                passed=False,
                metrics=metrics,
                issues=issues,
                evidence_refs=evidence_refs,
            )

        status = (
            QComputeValidationStatus.CONVERGED
            if plan.estimated_fidelity == 1.0
            else QComputeValidationStatus.VALIDATED
        )
        return self._build_report(
            artifact,
            plan,
            status=status,
            passed=True,
            metrics=metrics,
            issues=issues,
            evidence_refs=evidence_refs,
        )

    def build_evidence_bundle(
        self,
        artifact: QComputeRunArtifact,
        validation: QComputeValidationReport,
        environment: QComputeEnvironmentReport,
    ) -> QComputeEvidenceBundle:
        return build_evidence_bundle(artifact, validation, environment)

    def _build_report(
        self,
        artifact: QComputeRunArtifact,
        plan: QComputeRunPlan,
        *,
        status: QComputeValidationStatus,
        passed: bool,
        metrics: QComputeValidationMetrics,
        issues: list[ValidationIssue],
        evidence_refs: list[str],
    ) -> QComputeValidationReport:
        promotion_ready = passed and not any(issue.blocks_promotion for issue in issues)
        scored_evidence = ScoredEvidence(
            score=1.0 if passed else 0.0,
            metrics={
                key: float(value)
                for key, value in metrics.model_dump().items()
                if isinstance(value, int | float)
            },
            safety_score=1.0 if promotion_ready else 0.0,
            budget=BudgetState(used=1, exhausted=not promotion_ready),
            convergence=ConvergenceState(
                converged=status is QComputeValidationStatus.CONVERGED,
                criteria_met=[status.value] if passed else [],
                reason="validator accepted run" if passed else "validator blocked promotion",
            ),
            evidence_refs=evidence_refs,
            reasons=[issue.message for issue in issues] or [status.value],
            attributes={
                "status": status.value,
                "backend": artifact.backend_actual,
                "promotion_ready": promotion_ready,
            },
        )
        return QComputeValidationReport(
            task_id=plan.experiment_ref,
            plan_ref=plan.plan_id,
            artifact_ref=artifact.artifact_id,
            passed=passed,
            status=status,
            metrics=metrics,
            issues=issues,
            promotion_ready=promotion_ready,
            evidence_refs=evidence_refs,
            checkpoint_refs=list(dict.fromkeys([*plan.checkpoint_refs, *artifact.checkpoint_refs])),
            provenance_refs=list(dict.fromkeys([*plan.provenance_refs, *artifact.provenance_refs])),
            trace_refs=list(dict.fromkeys([*plan.trace_refs, *artifact.trace_refs])),
            scored_evidence=scored_evidence,
        )

    def _build_evidence_refs(
        self,
        artifact: QComputeRunArtifact,
        plan: QComputeRunPlan,
        environment: QComputeEnvironmentReport,
    ) -> list[str]:
        refs = [
            f"qcompute://plan/{plan.experiment_ref}/{plan.plan_id}",
            f"qcompute://artifact/{artifact.artifact_id}",
            f"qcompute://environment/{environment.task_id}/{environment.status}",
        ]
        if artifact.raw_output_path is not None:
            refs.append(f"qcompute://raw-output/{artifact.artifact_id}")
        return refs

    def _noise_impact_score(self, plan: QComputeRunPlan) -> float:
        if plan.noise is None or plan.noise.model == "none":
            return 0.0
        gate_error = self._gate_error_accumulation(plan)
        readout_error = plan.noise.readout_error or 0.0
        if plan.noise.model == "thermal_relaxation":
            return min(1.0, gate_error + readout_error + 0.05)
        if plan.noise.model == "depolarizing":
            return min(1.0, gate_error + readout_error)
        return 1.0

    def _gate_error_accumulation(self, plan: QComputeRunPlan) -> float:
        if plan.noise is None:
            return 0.0
        operation_counts = plan.compilation_metadata.get("operation_counts")
        if not isinstance(operation_counts, dict):
            return 0.0
        gate_error_map = plan.noise.gate_error_map or {}
        total = 0.0
        for gate_name, raw_count in operation_counts.items():
            if not isinstance(raw_count, int | float):
                continue
            default_error = plan.noise.depolarizing_prob or 0.0
            total += float(raw_count) * float(gate_error_map.get(gate_name, default_error))
        return min(1.0, total)

    def _readout_confidence(self, plan: QComputeRunPlan) -> float:
        readout_error = plan.noise.readout_error if plan.noise is not None else None
        if readout_error is None:
            return 1.0
        return max(0.0, min(1.0, 1.0 - readout_error))
