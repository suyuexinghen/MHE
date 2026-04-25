from __future__ import annotations

from metaharness.safety.gates import GateDecision, GateResult
from metaharness_ext.qcompute.contracts import QComputeEvidenceBundle, QComputePolicyReport
from metaharness_ext.qcompute.types import QComputeValidationStatus


class QComputeEvidencePolicy:
    def evaluate(self, bundle: QComputeEvidenceBundle) -> QComputePolicyReport:
        gates: list[GateResult] = []
        warnings = list(bundle.warnings)
        validation = bundle.validation_report
        environment = bundle.environment_report

        if environment.blocks_promotion or not environment.available:
            gates.append(
                GateResult(
                    gate="environment_readiness",
                    decision=GateDecision.REJECT,
                    reason=f"Environment status is {environment.status}.",
                    evidence={
                        "task_id": environment.task_id,
                        "status": environment.status,
                        "prerequisite_errors": list(environment.prerequisite_errors),
                    },
                )
            )

        if validation.status in {
            QComputeValidationStatus.ENVIRONMENT_INVALID,
            QComputeValidationStatus.BACKEND_UNAVAILABLE,
            QComputeValidationStatus.EXECUTION_FAILED,
        }:
            gates.append(
                GateResult(
                    gate="validation_status",
                    decision=GateDecision.REJECT,
                    reason=f"Validation status is {validation.status.value}.",
                    evidence={"task_id": validation.task_id, "status": validation.status.value},
                )
            )
        elif validation.status in {
            QComputeValidationStatus.RESULT_INCOMPLETE,
            QComputeValidationStatus.BELOW_FIDELITY_THRESHOLD,
            QComputeValidationStatus.NOISE_CORRUPTED,
        }:
            gates.append(
                GateResult(
                    gate="validation_status",
                    decision=GateDecision.DEFER,
                    reason=f"Validation status is {validation.status.value}.",
                    evidence={"task_id": validation.task_id, "status": validation.status.value},
                )
            )

        if bundle.run_artifact.raw_output_path is None:
            gates.append(
                GateResult(
                    gate="raw_output_anchor",
                    decision=GateDecision.DEFER,
                    reason="Evidence bundle is missing the raw output path.",
                    evidence={"artifact_id": bundle.run_artifact.artifact_id},
                )
            )

        if not validation.promotion_ready:
            gates.append(
                GateResult(
                    gate="promotion_readiness",
                    decision=GateDecision.DEFER,
                    reason="Validation report is not marked promotion-ready.",
                    evidence={"task_id": validation.task_id, "status": validation.status.value},
                )
            )

        if any(gate.decision is GateDecision.REJECT for gate in gates):
            first_reject = next(gate for gate in gates if gate.decision is GateDecision.REJECT)
            return QComputePolicyReport(
                passed=False,
                decision="reject",
                reason=first_reject.reason,
                warnings=warnings,
                gates=gates,
                evidence=self._report_evidence(bundle),
            )
        if gates:
            return QComputePolicyReport(
                passed=False,
                decision="defer",
                reason="QCompute evidence requires follow-up before promotion.",
                warnings=warnings,
                gates=gates,
                evidence=self._report_evidence(bundle),
            )

        gates.append(
            GateResult(
                gate="qcompute_evidence_ready",
                decision=GateDecision.ALLOW,
                reason="QCompute evidence is complete enough for governance review.",
                evidence=self._report_evidence(bundle),
            )
        )
        return QComputePolicyReport(
            passed=True,
            decision="allow",
            reason="QCompute evidence is complete enough for governance review.",
            warnings=warnings,
            gates=gates,
            evidence=self._report_evidence(bundle),
        )

    def _report_evidence(self, bundle: QComputeEvidenceBundle) -> dict[str, object]:
        validation = bundle.validation_report
        return {
            "task_id": validation.task_id,
            "plan_ref": validation.plan_ref,
            "artifact_ref": validation.artifact_ref,
            "validation_status": validation.status.value,
            "promotion_ready": validation.promotion_ready,
            "environment_status": bundle.environment_report.status,
            "fidelity": validation.metrics.fidelity,
            "noise_impact_score": validation.metrics.noise_impact_score,
        }
