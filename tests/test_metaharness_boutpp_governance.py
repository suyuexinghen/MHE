from __future__ import annotations

from metaharness_ext.boutpp.contracts import (
    BoutPPEvidenceBundle,
    BoutPPPolicyReport,
    BoutPPValidationReport,
)
from metaharness_ext.boutpp.governance import BoutPPGovernanceAdapter


def test_governance_builds_core_validation_report():
    validation = BoutPPValidationReport(task_id="t1", plan_ref="p1", artifact_ref="a1", passed=True)
    policy = BoutPPPolicyReport(passed=True, decision="allow", reason="ok")
    report = BoutPPGovernanceAdapter().build_core_validation_report(validation, policy)
    assert report.valid is True


def test_governance_requires_validation_for_candidate_record():
    bundle = BoutPPEvidenceBundle(bundle_id="b1", task_id="t1")
    try:
        BoutPPGovernanceAdapter().build_candidate_record(bundle, BoutPPPolicyReport(passed=True, decision="allow", reason="ok"))
    except ValueError as error:
        assert "validation report is required" in str(error)
