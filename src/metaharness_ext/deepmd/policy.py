from __future__ import annotations

from metaharness.safety.gates import GateDecision, GateResult
from metaharness_ext.deepmd.contracts import (
    DeepMDEvidenceBundle,
    DeepMDEvidenceWarning,
    DeepMDPolicyReport,
)


class DeepMDEvidencePolicy:
    def evaluate(self, bundle: DeepMDEvidenceBundle) -> DeepMDPolicyReport:
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
            return DeepMDPolicyReport(
                passed=False,
                decision="defer",
                reason="Validation report is not attached to the evidence bundle.",
                warnings=warnings,
                gates=gates,
                evidence={"run_id": bundle.run_id},
            )

        if validation.status in {
            "environment_invalid",
            "workspace_failed",
            "run_failed",
            "runtime_failed",
            "validation_failed",
        }:
            gates.append(
                GateResult(
                    gate="run_status",
                    decision=GateDecision.REJECT,
                    reason=f"Validation status is {validation.status}.",
                    evidence={"status": validation.status, "run_id": bundle.run_id},
                )
            )
            return DeepMDPolicyReport(
                passed=False,
                decision="reject",
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
        if bundle.execution_mode in {"dpgen_run", "dpgen_simplify"}:
            collection = bundle.summary.dpgen_collection
            if collection is None or not collection.iterations:
                incomplete = True
                gates.append(
                    GateResult(
                        gate="dpgen_iteration_evidence",
                        decision=GateDecision.DEFER,
                        reason="DP-GEN evidence is missing iteration details.",
                        evidence={"run_id": bundle.run_id},
                    )
                )
        if bundle.execution_mode == "dpgen_autotest" and not bundle.summary.autotest_properties:
            incomplete = True
            gates.append(
                GateResult(
                    gate="autotest_property_evidence",
                    decision=GateDecision.DEFER,
                    reason="Autotest evidence is missing structured property results.",
                    evidence={"run_id": bundle.run_id},
                )
            )

        if bundle.execution_mode == "dpgen_simplify" and validation.status != "converged":
            warnings.append(
                DeepMDEvidenceWarning(
                    code="simplify_not_converged",
                    message="DP-GEN simplify finished without convergence evidence.",
                    severity="warning",
                    evidence={"status": validation.status, "run_id": bundle.run_id},
                )
            )
        if validation.summary_metrics.get("relabeling_detected") == "true":
            warnings.append(
                DeepMDEvidenceWarning(
                    code="relabeling_detected",
                    message="Relabeling clues were detected in the DP-GEN evidence.",
                    severity="warning",
                    evidence={"run_id": bundle.run_id},
                )
            )

        if incomplete:
            return DeepMDPolicyReport(
                passed=False,
                decision="defer",
                reason="Evidence bundle is incomplete for downstream review.",
                warnings=warnings,
                gates=gates,
                evidence={"run_id": bundle.run_id},
            )

        gates.append(
            GateResult(
                gate="evidence_ready",
                decision=GateDecision.ALLOW,
                reason="Evidence bundle is complete enough for downstream consumption.",
                evidence={"run_id": bundle.run_id, "status": validation.status},
            )
        )
        return DeepMDPolicyReport(
            passed=True,
            decision="allow",
            reason="Evidence bundle is complete enough for downstream consumption.",
            warnings=warnings,
            gates=gates,
            evidence={"run_id": bundle.run_id, "status": validation.status},
        )
