from __future__ import annotations

from metaharness_ext.boutpp.contracts import (
    BoutPPEvidenceBundle,
    BoutPPEvidenceWarning,
    BoutPPPolicyReport,
)


class BoutPPEvidencePolicy:
    protected: bool = True

    def evaluate(self, bundle: BoutPPEvidenceBundle) -> BoutPPPolicyReport:
        gates = [
            self._gate_environment(bundle),
            self._gate_artifact(bundle),
            self._gate_postprocess(bundle),
            self._gate_validation(bundle),
        ]
        gates.append(self._gate_readiness(gates))
        if any(gate["result"] == "reject" for gate in gates):
            decision = "reject"
            passed = False
            reason = next(gate["reason"] for gate in gates if gate["result"] == "reject")
        elif any(gate["result"] == "defer" for gate in gates):
            decision = "defer"
            passed = False
            reason = next(gate["reason"] for gate in gates if gate["result"] == "defer")
        else:
            decision = "allow"
            passed = True
            reason = "All BOUT++ policy gates passed."
        return BoutPPPolicyReport(
            passed=passed,
            decision=decision,
            reason=reason,
            warnings=list(bundle.warnings),
            gates=gates,
            evidence={"bundle_id": bundle.bundle_id},
        )

    def _gate_environment(self, bundle: BoutPPEvidenceBundle) -> dict:
        environment = bundle.environment
        if environment is None or not environment.available or environment.blocks_promotion:
            return {
                "gate": "boutpp_environment_readiness",
                "result": "reject",
                "reason": "BOUT++ environment is not available.",
            }
        return {"gate": "boutpp_environment_readiness", "result": "pass", "reason": "ok"}

    def _gate_artifact(self, bundle: BoutPPEvidenceBundle) -> dict:
        artifact = bundle.artifact
        if artifact is None:
            return {"gate": "boutpp_artifact_presence", "result": "defer", "reason": "Artifact missing."}
        if artifact.status in {"failed", "timeout", "unavailable"}:
            return {
                "gate": "boutpp_artifact_status",
                "result": "reject",
                "reason": f"Artifact status is {artifact.status}.",
            }
        return {"gate": "boutpp_artifact_status", "result": "pass", "reason": "ok"}

    def _gate_postprocess(self, bundle: BoutPPEvidenceBundle) -> dict:
        postprocess = bundle.postprocess
        if postprocess is None:
            return {
                "gate": "boutpp_postprocess_presence",
                "result": "defer",
                "reason": "Postprocess report missing.",
            }
        if postprocess.status == "failed":
            return {
                "gate": "boutpp_postprocess_status",
                "result": "reject",
                "reason": "Postprocess failed.",
            }
        return {"gate": "boutpp_postprocess_status", "result": "pass", "reason": "ok"}

    def _gate_validation(self, bundle: BoutPPEvidenceBundle) -> dict:
        validation = bundle.validation
        if validation is None:
            return {
                "gate": "boutpp_validation_presence",
                "result": "defer",
                "reason": "Validation report missing.",
            }
        if validation.blocks_promotion:
            return {
                "gate": "boutpp_validation_status",
                "result": "reject",
                "reason": f"Validation failed with status {validation.status.value}.",
            }
        if not validation.passed:
            return {
                "gate": "boutpp_validation_status",
                "result": "defer",
                "reason": "Validation did not pass.",
            }
        return {"gate": "boutpp_validation_status", "result": "pass", "reason": "ok"}

    def _gate_readiness(self, gates: list[dict]) -> dict:
        if all(gate["result"] == "pass" for gate in gates):
            return {"gate": "boutpp_evidence_ready", "result": "pass", "reason": "All gates passed."}
        return {
            "gate": "boutpp_evidence_ready",
            "result": "defer",
            "reason": "Not all gates passed.",
        }


def build_policy_warning(code: str, message: str) -> BoutPPEvidenceWarning:
    return BoutPPEvidenceWarning(code=code, message=message)
