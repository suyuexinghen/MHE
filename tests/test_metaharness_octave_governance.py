from metaharness.core.models import ValidationIssue, ValidationIssueCategory
from metaharness.safety.gates import GateDecision, GateResult
from metaharness_ext.octave.contracts import (
    OctaveEvidenceBundle,
    OctavePolicyReport,
    OctaveValidationReport,
)
from metaharness_ext.octave.governance import OctaveGovernanceAdapter


def _validation(*, passed: bool = True) -> OctaveValidationReport:
    return OctaveValidationReport(
        task_id="task-1",
        plan_ref="plan-1",
        artifact_ref="artifact-1",
        passed=passed,
        status="executed" if passed else "numeric_validation_failed",
        governance_state="ready" if passed else "blocked",
        evidence_refs=["octave://validation/task-1/artifact-1"],
    )


def _policy(*, decision: str = "allow") -> OctavePolicyReport:
    gates = [
        GateResult(
            gate="octave_evidence_ready",
            decision=GateDecision.ALLOW if decision == "allow" else GateDecision.REJECT,
            reason="ready" if decision == "allow" else "blocked",
        )
    ]
    return OctavePolicyReport(
        passed=decision == "allow",
        decision=decision,
        governance_state="ready" if decision == "allow" else "blocked",
        reason="ready" if decision == "allow" else "blocked",
        gates=gates,
    )


def test_octave_governance_builds_valid_core_report() -> None:
    report = OctaveGovernanceAdapter().build_core_validation_report(_validation(), _policy())

    assert report.valid is True
    assert report.issues == []


def test_octave_governance_aggregates_policy_gate_blockers() -> None:
    validation = _validation(passed=False)
    validation.issues.append(
        ValidationIssue(
            code="octave_numeric_failed",
            message="numeric tolerance failed",
            subject="task-1",
            category=ValidationIssueCategory.PROMOTION_BLOCKER,
            blocks_promotion=True,
        )
    )

    report = OctaveGovernanceAdapter().build_core_validation_report(
        validation, _policy(decision="reject")
    )

    assert report.valid is False
    assert {issue.code for issue in report.issues} == {
        "octave_numeric_failed",
        "octave_gate_octave_evidence_ready",
    }


def test_octave_governance_builds_candidate_record_and_events() -> None:
    validation = _validation()
    bundle = OctaveEvidenceBundle(
        bundle_id="bundle-1",
        task_id="task-1",
        run_id="run-1",
        validation=validation,
        metadata={"graph_version": 7},
    )
    adapter = OctaveGovernanceAdapter(session_id="session-1")

    candidate = adapter.build_candidate_record(bundle, _policy())
    events = adapter.build_session_events(bundle, _policy())

    assert candidate.candidate_id == "octave-candidate-v7"
    assert candidate.promoted is True
    assert [event.event_type.value for event in events] == [
        "candidate_validated",
        "safety_gate_evaluated",
    ]


def test_octave_governance_runtime_evidence_noops_without_services() -> None:
    validation = _validation()
    bundle = OctaveEvidenceBundle(bundle_id="bundle-1", task_id="task-1", validation=validation)

    refs = OctaveGovernanceAdapter().record_with_artifact_store(bundle, _policy())

    assert refs["audit_refs"] == []
    assert refs["artifact_refs"] == []
    assert "octave://validation/task-1/artifact-1" in refs["provenance_refs"]
