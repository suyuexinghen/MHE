from __future__ import annotations

from metaharness.safety.gates import GateDecision, GateResult
from metaharness_ext.jedi.contracts import JediEvidenceBundle, JediEvidenceWarning, JediPolicyReport


class JediEvidencePolicy:
    def evaluate(self, bundle: JediEvidenceBundle) -> JediPolicyReport:
        gates: list[GateResult] = []
        warnings = list(bundle.warnings)
        validation = bundle.validation
        if validation is None:
            gates.append(
                GateResult(
                    gate="validation_presence",
                    decision=GateDecision.DEFER,
                    reason="Validation report is not attached to the evidence bundle.",
                    evidence={"run_id": bundle.run_id},
                )
            )
            return JediPolicyReport(
                passed=False,
                decision="defer",
                reason="Validation report is not attached to the evidence bundle.",
                warnings=warnings,
                gates=gates,
                evidence={"run_id": bundle.run_id},
            )

        if validation.status == "environment_invalid":
            gates.append(
                GateResult(
                    gate="environment_readiness",
                    decision=GateDecision.REJECT,
                    reason="Validation status is environment_invalid.",
                    evidence={
                        "status": validation.status,
                        "run_id": bundle.run_id,
                        "blocking_reasons": validation.blocking_reasons,
                    },
                )
            )
            return JediPolicyReport(
                passed=False,
                decision="reject",
                reason="Validation status is environment_invalid.",
                warnings=warnings,
                gates=gates,
                evidence={"status": validation.status, "run_id": bundle.run_id},
            )

        if validation.status in {"runtime_failed", "validation_failed"}:
            gates.append(
                GateResult(
                    gate="run_status",
                    decision=GateDecision.DEFER,
                    reason=f"Validation status is {validation.status}.",
                    evidence={
                        "status": validation.status,
                        "run_id": bundle.run_id,
                        "blocking_reasons": validation.blocking_reasons,
                    },
                )
            )
            return JediPolicyReport(
                passed=False,
                decision="defer",
                reason=f"Validation status is {validation.status}.",
                warnings=warnings,
                gates=gates,
                evidence={"status": validation.status, "run_id": bundle.run_id},
            )

        incomplete = False
        if not bundle.run.stdout_path or not bundle.run.stderr_path:
            incomplete = True
            gates.append(
                GateResult(
                    gate="log_completeness",
                    decision=GateDecision.DEFER,
                    reason="Evidence bundle is missing stdout/stderr log references.",
                    evidence={"run_id": bundle.run_id},
                )
            )

        if bundle.execution_mode == "real_run" and not bundle.run.output_files:
            incomplete = True
            gates.append(
                GateResult(
                    gate="primary_output_evidence",
                    decision=GateDecision.DEFER,
                    reason="Real run evidence is missing a primary output artifact.",
                    evidence={"run_id": bundle.run_id},
                )
            )

        if bundle.execution_mode == "real_run" and not bundle.run.diagnostic_files and not bundle.run.reference_files:
            incomplete = True
            gates.append(
                GateResult(
                    gate="diagnostic_or_reference_evidence",
                    decision=GateDecision.DEFER,
                    reason="Real run evidence is missing diagnostics or reference artifacts.",
                    evidence={"run_id": bundle.run_id},
                )
            )

        if validation.blocking_reasons:
            warnings.append(
                JediEvidenceWarning(
                    code="blocking_reasons_present",
                    message="Validation report includes blocking reasons for downstream review.",
                    evidence={"run_id": bundle.run_id, "blocking_reasons": validation.blocking_reasons},
                )
            )

        if validation.provenance_refs or validation.checkpoint_refs:
            warnings.append(
                JediEvidenceWarning(
                    code="handoff_refs_present",
                    message="Validation report already carries provenance/checkpoint handoff references.",
                    severity="info",
                    evidence={
                        "run_id": bundle.run_id,
                        "provenance_refs": validation.provenance_refs,
                        "checkpoint_refs": validation.checkpoint_refs,
                    },
                )
            )

        if incomplete:
            return JediPolicyReport(
                passed=False,
                decision="defer",
                reason="Evidence bundle is incomplete for downstream review.",
                warnings=warnings,
                gates=gates,
                evidence={"run_id": bundle.run_id, "status": validation.status},
            )

        gates.append(
            GateResult(
                gate="evidence_ready",
                decision=GateDecision.ALLOW,
                reason="Evidence bundle is complete enough for downstream consumption.",
                evidence={"run_id": bundle.run_id, "status": validation.status},
            )
        )
        return JediPolicyReport(
            passed=True,
            decision="allow",
            reason="Evidence bundle is complete enough for downstream consumption.",
            warnings=warnings,
            gates=gates,
            evidence={"run_id": bundle.run_id, "status": validation.status},
        )
