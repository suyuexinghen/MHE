from __future__ import annotations

from metaharness_ext.moose.contracts import MooseEvidenceBundle, MoosePolicyReport


class MooseEvidencePolicy:
    def evaluate(self, bundle: MooseEvidenceBundle) -> MoosePolicyReport:
        validation = bundle.validation
        environment = bundle.environment
        if environment is not None and not environment.available:
            return MoosePolicyReport(
                passed=False,
                decision="reject",
                reason=f"MOOSE environment unavailable: {environment.status}",
            )
        if validation is None:
            return MoosePolicyReport(
                passed=False, decision="defer", reason="Validation evidence missing"
            )
        if validation.passed and not validation.blocks_promotion:
            return MoosePolicyReport(passed=True, decision="allow", reason="Validation passed")
        return MoosePolicyReport(
            passed=False,
            decision="reject",
            reason="Validation found blocking issues",
        )
