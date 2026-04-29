from __future__ import annotations

from metaharness.safety.gates import GateDecision, GateResult
from metaharness_ext.fealpy.contracts import FealpyEvidenceBundle, FealpyPolicyReport


class FealpyEvidencePolicy:
    def evaluate(self, bundle: FealpyEvidenceBundle) -> FealpyPolicyReport:
        gates: list[GateResult] = []
        warnings = list(bundle.warnings)
        environment = bundle.environment
        validation = bundle.validation

        if environment is not None and (environment.blocks_promotion or not environment.available):
            gates.append(
                GateResult(
                    gate="fealpy_environment_readiness",
                    decision=GateDecision.REJECT,
                    reason=f"fealpy environment status is {environment.status}.",
                    evidence={
                        "task_id": environment.task_id,
                        "status": environment.status,
                        "missing_prerequisites": list(environment.missing_prerequisites),
                    },
                )
            )

        if validation is None:
            gates.append(
                GateResult(
                    gate="fealpy_validation_presence",
                    decision=GateDecision.DEFER,
                    reason="fealpy validation report is not attached.",
                    evidence={"run_id": bundle.run_id},
                )
            )
        elif validation.blocks_promotion or not validation.passed:
            gates.append(
                GateResult(
                    gate="fealpy_validation_status",
                    decision=GateDecision.REJECT
                    if validation.blocks_promotion
                    else GateDecision.DEFER,
                    reason=f"fealpy validation status is {validation.status}.",
                    evidence=self._report_evidence(bundle),
                )
            )

        if not bundle.evidence_refs:
            gates.append(
                GateResult(
                    gate="fealpy_evidence_files",
                    decision=GateDecision.DEFER,
                    reason="fealpy evidence bundle does not include evidence refs.",
                    evidence={"run_id": bundle.run_id},
                )
            )

        if any(gate.decision is GateDecision.REJECT for gate in gates):
            first_reject = next(gate for gate in gates if gate.decision is GateDecision.REJECT)
            return FealpyPolicyReport(
                passed=False,
                decision="reject",
                reason=first_reject.reason,
                warnings=warnings,
                gates=gates,
                evidence=self._report_evidence(bundle),
            )

        if gates:
            return FealpyPolicyReport(
                passed=False,
                decision="defer",
                reason="fealpy evidence requires follow-up.",
                warnings=warnings,
                gates=gates,
                evidence=self._report_evidence(bundle),
            )

        gates.append(
            GateResult(
                gate="fealpy_evidence_ready",
                decision=GateDecision.ALLOW,
                reason="fealpy evidence is complete for governance review.",
                evidence=self._report_evidence(bundle),
            )
        )
        return FealpyPolicyReport(
            passed=True,
            decision="allow",
            reason="fealpy evidence is complete for governance review.",
            warnings=warnings,
            gates=gates,
            evidence=self._report_evidence(bundle),
        )

    def _report_evidence(self, bundle: FealpyEvidenceBundle) -> dict[str, object]:
        validation = bundle.validation
        return {
            "task_id": bundle.task_id,
            "run_id": bundle.run_id,
            "plan_ref": bundle.plan_ref,
            "artifact_id": bundle.artifact_ref,
            "run_status": bundle.artifact.status if bundle.artifact is not None else None,
            "validation_status": validation.status if validation is not None else None,
            "evidence_ref_count": len(bundle.evidence_refs),
        }
