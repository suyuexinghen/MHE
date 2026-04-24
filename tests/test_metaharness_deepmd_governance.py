from metaharness.core.graph_versions import ExternalCandidateReview, ExternalCandidateReviewState
from metaharness.core.models import (
    GraphSnapshot,
    SessionEventType,
    ValidationIssue,
    ValidationIssueCategory,
)
from metaharness.observability.events import InMemorySessionStore
from metaharness.provenance import AuditLog, ProvGraph, RelationKind
from metaharness.safety.gates import GateDecision, GateResult
from metaharness_ext.deepmd.contracts import (
    DeepMDDiagnosticSummary,
    DeepMDEvidenceBundle,
    DeepMDPolicyReport,
    DeepMDRunArtifact,
    DeepMDValidationReport,
)
from metaharness_ext.deepmd.governance import DeepMDGovernanceAdapter


def _bundle(
    *,
    decision: str = "allow",
    governance_state: str = "ready",
    blocks_promotion: bool = False,
    graph_version: int | None = 3,
    candidate_id: str = "candidate-1",
) -> tuple[DeepMDEvidenceBundle, DeepMDPolicyReport]:
    run = DeepMDRunArtifact(
        task_id="task-1",
        run_id="run-1",
        application_family="deepmd_train",
        execution_mode="train",
        command=["dp", "train", "input.json"],
        return_code=0,
        stdout_path="/tmp/stdout.log",
        stderr_path="/tmp/stderr.log",
        working_directory="/tmp/run-1",
        status="completed",
    )
    validation = DeepMDValidationReport(
        task_id="task-1",
        run_id="run-1",
        passed=decision == "allow" and not blocks_promotion and governance_state == "ready",
        status="trained" if decision == "allow" else "validation_failed",
        issues=[],
        blocks_promotion=blocks_promotion,
        governance_state=governance_state,
        summary_metrics={
            "candidate_id": candidate_id,
            "graph_version": graph_version if graph_version is not None else 0,
        },
    )
    bundle = DeepMDEvidenceBundle(
        task_id="task-1",
        run_id="run-1",
        application_family="deepmd_train",
        execution_mode="train",
        run=run,
        validation=validation,
        summary=DeepMDDiagnosticSummary(),
        metadata={
            "candidate_id": candidate_id,
            **({"graph_version": graph_version} if graph_version is not None else {}),
        },
    )
    policy = DeepMDPolicyReport(
        passed=decision == "allow",
        decision=decision,
        reason="ready" if decision == "allow" else "defer for review",
        gates=[
            GateResult(
                gate="evidence_ready" if decision == "allow" else "review_required",
                decision=GateDecision.ALLOW if decision == "allow" else GateDecision.DEFER,
                reason="ready" if decision == "allow" else "missing review evidence",
            )
        ],
    )
    return bundle, policy


def test_deepmd_governance_adapter_builds_candidate_record() -> None:
    bundle, policy = _bundle()

    record = DeepMDGovernanceAdapter().build_candidate_record(bundle, policy)

    assert record.candidate_id == "candidate-1"
    assert record.promoted is True
    assert record.snapshot.graph_version == 3
    assert record.report.valid is True
    assert record.report.issues == []


def test_deepmd_governance_adapter_maps_blockers_into_core_validation_report() -> None:
    bundle, policy = _bundle(decision="defer")

    report = DeepMDGovernanceAdapter().build_core_validation_report(bundle.validation, policy)

    assert report.valid is False
    assert report.issues[0].code == "deepmd_gate_review_required"
    assert report.issues[0].blocks_promotion is True


def test_deepmd_governance_adapter_preserves_validation_issues() -> None:
    bundle, policy = _bundle()
    bundle.validation.issues.append(
        ValidationIssue(
            code="deepmd_missing_curve",
            message="Learning curve missing.",
            subject="task-1",
            category=ValidationIssueCategory.PROMOTION_BLOCKER,
            blocks_promotion=True,
        )
    )
    bundle.validation.blocks_promotion = True
    bundle.validation.governance_state = "blocked"
    bundle.validation.passed = False

    report = DeepMDGovernanceAdapter().build_core_validation_report(bundle.validation, policy)

    assert report.valid is False
    assert report.issues[0].code == "deepmd_missing_curve"


def test_deepmd_governance_adapter_uses_supplied_snapshot() -> None:
    bundle, policy = _bundle(graph_version=None)

    record = DeepMDGovernanceAdapter().build_candidate_record(
        bundle,
        policy,
        snapshot=GraphSnapshot(graph_version=11),
    )

    assert record.snapshot.graph_version == 11
    assert record.candidate_id == "candidate-1"


def test_deepmd_governance_adapter_leaves_external_review_unset() -> None:
    bundle, policy = _bundle()

    record = DeepMDGovernanceAdapter().build_candidate_record(bundle, policy)

    assert record.external_review is None


def test_deepmd_governance_adapter_preserves_external_review_on_runtime_handoff() -> None:
    bundle, policy = _bundle()
    record = DeepMDGovernanceAdapter().build_candidate_record(bundle, policy)
    record.external_review = ExternalCandidateReview(
        state=ExternalCandidateReviewState.ADOPTED,
        reviewer="runtime-review",
        source="deepmd-baseline",
        reason="accepted for downstream promotion tracking",
    )

    assert record.external_review is not None
    assert record.external_review.state is ExternalCandidateReviewState.ADOPTED
    assert record.external_review.reviewer == "runtime-review"
    assert record.external_review.source == "deepmd-baseline"


def test_deepmd_governance_adapter_emits_session_audit_and_provenance_evidence() -> None:
    bundle, policy = _bundle()
    session_store = InMemorySessionStore()
    audit_log = AuditLog()
    provenance_graph = ProvGraph()

    refs = DeepMDGovernanceAdapter(session_id="deepmd-session").emit_runtime_evidence(
        bundle,
        policy,
        session_store=session_store,
        audit_log=audit_log,
        provenance_graph=provenance_graph,
    )

    events = session_store.get_events("deepmd-session")
    assert [event.event_type for event in events] == [
        SessionEventType.CANDIDATE_VALIDATED,
        SessionEventType.SAFETY_GATE_EVALUATED,
    ]
    assert events[1].payload == {
        "decision": "allow",
        "reason": "ready",
        "gate_count": 1,
        "execution_mode": "train",
        "application_family": "deepmd_train",
    }
    assert len(audit_log.by_kind("session.candidate_validated")) == 1
    assert len(audit_log.by_kind("session.safety_gate_evaluated")) == 1
    assert len(audit_log.by_kind("deepmd.governance_handoff")) == 1
    assert all(ref.startswith("audit-record:") for ref in refs["audit_refs"])
    assert "provenance://deepmd/validation/task-1" in refs["provenance_refs"]

    provenance = provenance_graph.to_dict()
    assert "graph-candidate:candidate-1" in provenance["entities"]
    assert "graph-version:3" in provenance["entities"]
    assert any(
        relation["subject"].startswith("session-event:")
        and relation["kind"] == RelationKind.WAS_DERIVED_FROM.value
        and relation["object"] == "graph-candidate:candidate-1"
        for relation in provenance["relations"]
    )
