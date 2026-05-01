from __future__ import annotations

from metaharness_ext.pycfd.contracts import (
    PyCFDEvidenceBundle,
    PyCFDEvidenceWarning,
    PyCFDPolicyReport,
)


class PyCFDEvidencePolicy:
    """Evaluates a 5-gate evidence policy chain for PyCFD artifacts.

    All gates are always evaluated (non-short-circuit).
    Decision: ALLOW / DEFER / REJECT.
    """

    def evaluate(self, bundle: PyCFDEvidenceBundle) -> PyCFDPolicyReport:
        gates: list[dict] = []
        warnings: list[PyCFDEvidenceWarning] = list(bundle.warnings)

        # Gate 1: Environment readiness
        g1 = self._gate_environment(bundle)
        gates.append(g1)

        # Gate 2: Validation presence
        g2 = self._gate_validation_presence(bundle)
        gates.append(g2)

        # Gate 3: Validation status
        g3 = self._gate_validation_status(bundle)
        gates.append(g3)

        # Gate 4: Evidence files
        g4 = self._gate_evidence_files(bundle)
        gates.append(g4)

        # Gate 5: Overall readiness
        g5 = self._gate_readiness(gates)
        gates.append(g5)

        # Determine decision
        if any(g["result"] == "reject" for g in gates):
            decision = "reject"
            passed = False
            reason = next(g["reason"] for g in gates if g["result"] == "reject")
        elif any(g["result"] == "defer" for g in gates):
            decision = "defer"
            passed = False
            reason = next(g["reason"] for g in gates if g["result"] == "defer")
        else:
            decision = "allow"
            passed = True
            reason = "All policy gates passed."

        return PyCFDPolicyReport(
            passed=passed,
            decision=decision,
            reason=reason,
            warnings=warnings,
            gates=gates,
            evidence={"bundle_id": bundle.bundle_id},
        )

    def _gate_environment(self, bundle: PyCFDEvidenceBundle) -> dict:
        env = bundle.environment
        if env is None or not env.available or env.blocks_promotion:
            return {
                "gate": "pycfd_environment_readiness",
                "result": "reject",
                "reason": "PyCFD environment is not available.",
            }
        return {"gate": "pycfd_environment_readiness", "result": "pass", "reason": "ok"}

    def _gate_validation_presence(self, bundle: PyCFDEvidenceBundle) -> dict:
        if bundle.validation is None:
            return {
                "gate": "pycfd_validation_presence",
                "result": "defer",
                "reason": "Validation report is missing.",
            }
        return {"gate": "pycfd_validation_presence", "result": "pass", "reason": "ok"}

    def _gate_validation_status(self, bundle: PyCFDEvidenceBundle) -> dict:
        val = bundle.validation
        if val is None:
            return {
                "gate": "pycfd_validation_status",
                "result": "defer",
                "reason": "No validation to check.",
            }
        if val.status.value == "runtime_failed" or val.status.value == "environment_unavailable":
            return {
                "gate": "pycfd_validation_status",
                "result": "reject",
                "reason": f"Validation failed with status: {val.status.value}",
            }
        if val.blocks_promotion:
            return {
                "gate": "pycfd_validation_status",
                "result": "defer",
                "reason": "Validation has blocking issues.",
            }
        if not val.passed:
            return {
                "gate": "pycfd_validation_status",
                "result": "defer",
                "reason": "Validation did not pass.",
            }
        return {"gate": "pycfd_validation_status", "result": "pass", "reason": "ok"}

    def _gate_evidence_files(self, bundle: PyCFDEvidenceBundle) -> dict:
        if not bundle.evidence_refs and not bundle.evidence_files:
            return {
                "gate": "pycfd_evidence_files",
                "result": "defer",
                "reason": "No evidence files or refs present.",
            }
        return {"gate": "pycfd_evidence_files", "result": "pass", "reason": "ok"}

    def _gate_readiness(self, gates: list[dict]) -> dict:
        if all(g["result"] == "pass" for g in gates[:-1]):
            return {"gate": "pycfd_evidence_ready", "result": "pass", "reason": "All gates passed."}
        return {
            "gate": "pycfd_evidence_ready",
            "result": "defer",
            "reason": "Not all gates passed.",
        }
