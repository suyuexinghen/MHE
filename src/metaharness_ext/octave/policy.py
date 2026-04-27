from __future__ import annotations

from metaharness.safety.gates import GateDecision, GateResult
from metaharness_ext.octave.contracts import OctaveEvidenceBundle, OctavePolicyReport


class OctaveEvidencePolicy:
    def evaluate(self, bundle: OctaveEvidenceBundle) -> OctavePolicyReport:
        gates: list[GateResult] = []
        warnings = list(bundle.warnings)
        environment = bundle.environment
        validation = bundle.validation

        if environment is not None and (environment.blocks_promotion or not environment.available):
            gates.append(
                GateResult(
                    gate="octave_environment_readiness",
                    decision=GateDecision.REJECT,
                    reason=f"Octave environment status is {environment.status}.",
                    evidence={
                        "task_id": environment.task_id,
                        "status": environment.status,
                        "missing_packages": list(environment.missing_packages),
                        "prerequisite_errors": list(environment.prerequisite_errors),
                    },
                )
            )

        if validation is None:
            gates.append(
                GateResult(
                    gate="octave_validation_presence",
                    decision=GateDecision.DEFER,
                    reason="Octave validation report is not attached.",
                    evidence={"run_id": bundle.run_id},
                )
            )
        else:
            if validation.governance_state == "blocked" or validation.blocks_promotion:
                gates.append(
                    GateResult(
                        gate="octave_validation_status",
                        decision=GateDecision.REJECT,
                        reason=f"Octave validation status is {validation.status}.",
                        evidence=self._report_evidence(bundle),
                    )
                )
            elif validation.governance_state == "defer" or not validation.passed:
                gates.append(
                    GateResult(
                        gate="octave_validation_status",
                        decision=GateDecision.DEFER,
                        reason=f"Octave validation status is {validation.status}.",
                        evidence=self._report_evidence(bundle),
                    )
                )

        if not bundle.evidence_files:
            gates.append(
                GateResult(
                    gate="octave_evidence_files",
                    decision=GateDecision.DEFER,
                    reason="Octave evidence bundle does not include file evidence.",
                    evidence={"run_id": bundle.run_id},
                )
            )
        if (
            bundle.artifact is not None
            and bundle.artifact.status == "completed"
            and not bundle.artifact.output_files
        ):
            gates.append(
                GateResult(
                    gate="octave_output_completeness",
                    decision=GateDecision.DEFER,
                    reason="Octave run completed without declared output files.",
                    evidence={"run_id": bundle.run_id},
                )
            )

        if any(gate.decision is GateDecision.REJECT for gate in gates):
            first_reject = next(gate for gate in gates if gate.decision is GateDecision.REJECT)
            return OctavePolicyReport(
                passed=False,
                decision="reject",
                governance_state="blocked",
                reason=first_reject.reason,
                warnings=warnings,
                gates=gates,
                evidence=self._report_evidence(bundle),
            )
        if gates:
            return OctavePolicyReport(
                passed=False,
                decision="defer",
                governance_state="defer",
                reason="Octave evidence requires follow-up before governance consumption.",
                warnings=warnings,
                gates=gates,
                evidence=self._report_evidence(bundle),
            )

        gates.append(
            GateResult(
                gate="octave_evidence_ready",
                decision=GateDecision.ALLOW,
                reason="Octave evidence is complete enough for governance review.",
                evidence=self._report_evidence(bundle),
            )
        )
        return OctavePolicyReport(
            passed=True,
            decision="allow",
            governance_state="ready",
            reason="Octave evidence is complete enough for governance review.",
            warnings=warnings,
            gates=gates,
            evidence=self._report_evidence(bundle),
        )

    def _report_evidence(self, bundle: OctaveEvidenceBundle) -> dict[str, object]:
        validation = bundle.validation
        return {
            "task_id": bundle.task_id,
            "run_id": bundle.run_id,
            "plan_ref": bundle.plan_ref,
            "artifact_id": bundle.artifact_ref,
            "run_status": bundle.artifact.status if bundle.artifact is not None else None,
            "validation_status": validation.status if validation is not None else None,
            "governance_state": validation.governance_state if validation is not None else None,
            "evidence_ref_count": len(bundle.evidence_refs),
        }
