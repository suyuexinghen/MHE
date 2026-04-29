from __future__ import annotations

import pytest

from metaharness.core.graph_versions import CandidateRecord
from metaharness.core.models import (
    GraphSnapshot,
    SessionEventType,
    ValidationIssue,
)
from metaharness.observability.events import InMemorySessionStore
from metaharness.provenance import AuditLog, ProvGraph
from metaharness.safety.gates import GateDecision, GateResult
from metaharness_ext.fealpy.contracts import (
    FealpyEvidenceBundle,
    FealpyPolicyReport,
    FealpyProblemSpec,
    FealpyRunArtifact,
    FealpyRunPlan,
    FealpyValidationReport,
)
from metaharness_ext.fealpy.governance import FealpyGovernanceAdapter
from metaharness_ext.fealpy.types import FealpyValidationStatus


def _validation(**overrides) -> FealpyValidationReport:
    defaults = {
        "task_id": "gov-test",
        "plan_ref": "fealpy-gov-test-abc123",
        "artifact_ref": "artifact-1",
        "passed": True,
        "status": FealpyValidationStatus.EXECUTED,
        "l2_passed": True,
        "h1_passed": True,
    }
    defaults.update(overrides)
    return FealpyValidationReport(**defaults)


def _policy(**overrides) -> FealpyPolicyReport:
    defaults: dict = {
        "passed": True,
        "decision": "allow",
        "reason": "all gates passed",
        "gates": [
            GateResult(
                gate="fealpy_evidence_ready",
                decision=GateDecision.ALLOW,
                reason="fealpy evidence is complete.",
                evidence={},
            )
        ],
        "evidence": {"task_id": "gov-test"},
    }
    defaults.update(overrides)
    return FealpyPolicyReport(**defaults)


def _bundle(**overrides) -> FealpyEvidenceBundle:
    validation = _validation()
    spec = FealpyProblemSpec(task_id="gov-test")
    plan = FealpyRunPlan(
        plan_id="fealpy-gov-test-abc123",
        task_id="gov-test",
        run_id="run-fealpy-gov-test-abc123",
        spec=spec,
        workspace_dir=".runs/fealpy/gov-test",
        script_source="print('hello')",
    )
    artifact = FealpyRunArtifact(
        artifact_id="artifact-1",
        run_id="run-fealpy-gov-test-abc123",
        task_id="gov-test",
        plan_ref="fealpy-gov-test-abc123",
        status="completed",
        l2_error=0.001,
        h1_error=0.01,
        dof_count=81,
    )
    defaults = {
        "bundle_id": "fealpy-gov-test-run-1",
        "task_id": "gov-test",
        "run_id": "run-fealpy-gov-test-abc123",
        "plan_ref": "fealpy-gov-test-abc123",
        "artifact_ref": "artifact-1",
        "validation_ref": "fealpy://validation/gov-test/artifact-1",
        "plan": plan,
        "artifact": artifact,
        "validation": validation,
        "evidence_refs": ["fealpy://run/gov-test/run-1"],
    }
    defaults.update(overrides)
    return FealpyEvidenceBundle(**defaults)


# ── build_core_validation_report ────────────────────────────────────────


def test_validation_report_passed() -> None:
    adapter = FealpyGovernanceAdapter()
    report = adapter.build_core_validation_report(_validation(), _policy())
    assert report.valid is True
    assert len(report.issues) == 0


def test_validation_report_failed_validation() -> None:
    adapter = FealpyGovernanceAdapter()
    report = adapter.build_core_validation_report(_validation(passed=False), _policy())
    assert report.valid is False


def test_validation_report_blocks_promotion() -> None:
    adapter = FealpyGovernanceAdapter()
    validation = _validation(
        issues=[
            ValidationIssue(
                code="FEALPY_L2_TOLERANCE",
                message="L2 too high",
                subject="l2_error",
                blocks_promotion=True,
            )
        ]
    )
    report = adapter.build_core_validation_report(validation, _policy())
    assert report.valid is False


def test_validation_report_policy_reject() -> None:
    adapter = FealpyGovernanceAdapter()
    report = adapter.build_core_validation_report(
        _validation(),
        _policy(passed=False, decision="reject", reason="env unavailable"),
    )
    assert report.valid is False


def test_validation_report_policy_defer_not_valid() -> None:
    adapter = FealpyGovernanceAdapter()
    report = adapter.build_core_validation_report(
        _validation(),
        _policy(passed=False, decision="defer", reason="evidence incomplete"),
    )
    assert report.valid is False


# ── build_candidate_record ───────────────────────────────────────────────


def test_candidate_record_promoted_when_valid() -> None:
    adapter = FealpyGovernanceAdapter()
    bundle = _bundle()
    record = adapter.build_candidate_record(bundle, _policy())
    assert isinstance(record, CandidateRecord)
    assert record.promoted is True
    assert record.report.valid is True


def test_candidate_record_not_promoted_when_invalid() -> None:
    adapter = FealpyGovernanceAdapter()
    bundle = _bundle(validation=_validation(passed=False))
    record = adapter.build_candidate_record(bundle, _policy())
    assert record.promoted is False


def test_candidate_record_uses_provided_snapshot() -> None:
    adapter = FealpyGovernanceAdapter()
    snapshot = GraphSnapshot(graph_version=5)
    record = adapter.build_candidate_record(_bundle(), _policy(), snapshot=snapshot)
    assert record.snapshot.graph_version == 5


# ── build_session_events ─────────────────────────────────────────────────


def test_session_events_validated_and_safety_gate() -> None:
    adapter = FealpyGovernanceAdapter(session_id="session-1")
    events = adapter.build_session_events(_bundle(), _policy())
    event_types = {e.event_type for e in events}
    assert SessionEventType.CANDIDATE_VALIDATED in event_types
    assert SessionEventType.SAFETY_GATE_EVALUATED in event_types


def test_session_events_includes_rejected_when_policy_rejects() -> None:
    adapter = FealpyGovernanceAdapter()
    events = adapter.build_session_events(
        _bundle(), _policy(passed=False, decision="reject", reason="env missing")
    )
    assert any(e.event_type == SessionEventType.CANDIDATE_REJECTED for e in events)


def test_session_events_no_rejected_when_policy_allows() -> None:
    adapter = FealpyGovernanceAdapter()
    events = adapter.build_session_events(_bundle(), _policy())
    assert not any(e.event_type == SessionEventType.CANDIDATE_REJECTED for e in events)


# ── emit_runtime_evidence ────────────────────────────────────────────────


def test_emit_returns_refs() -> None:
    adapter = FealpyGovernanceAdapter()
    refs = adapter.emit_runtime_evidence(_bundle(), _policy())
    assert "audit_refs" in refs
    assert "provenance_refs" in refs


def test_emit_with_session_store() -> None:
    store = InMemorySessionStore()
    adapter = FealpyGovernanceAdapter(session_id="session-1")
    refs = adapter.emit_runtime_evidence(_bundle(), _policy(), session_store=store)
    assert "audit_refs" in refs
    events = store.get_events("session-1")
    assert len(events) >= 2


def test_emit_with_audit_log() -> None:
    audit = AuditLog()
    adapter = FealpyGovernanceAdapter()
    refs = adapter.emit_runtime_evidence(_bundle(), _policy(), audit_log=audit)
    assert len(refs["audit_refs"]) > 0
    assert any("audit-record:" in ref for ref in refs["audit_refs"])


def test_emit_with_provenance_graph() -> None:
    graph = ProvGraph()
    adapter = FealpyGovernanceAdapter()
    refs = adapter.emit_runtime_evidence(_bundle(), _policy(), provenance_graph=graph)
    assert len(refs["provenance_refs"]) > 0
    assert len(graph.entities) > 0
    assert any(eid.startswith("graph-candidate:") for eid in graph.entities)


def test_emit_all_stores_together() -> None:
    store = InMemorySessionStore()
    audit = AuditLog()
    graph = ProvGraph()
    adapter = FealpyGovernanceAdapter(session_id="session-1")
    refs = adapter.emit_runtime_evidence(
        _bundle(),
        _policy(),
        session_store=store,
        audit_log=audit,
        provenance_graph=graph,
    )
    assert len(store.get_events("session-1")) >= 2
    assert len(refs["audit_refs"]) > 0
    assert len(refs["provenance_refs"]) > 0
    assert len(graph.entities) > 0


# ── Error cases ──────────────────────────────────────────────────────────


def test_require_validation_raises() -> None:
    adapter = FealpyGovernanceAdapter()
    bundle = _bundle(validation=None)
    with pytest.raises(ValueError, match="validation report"):
        adapter.build_session_events(bundle, _policy())


def test_policy_gate_issues_reject_gate() -> None:
    adapter = FealpyGovernanceAdapter()
    policy = _policy(
        passed=False,
        decision="reject",
        gates=[
            GateResult(
                gate="fealpy_environment_readiness",
                decision=GateDecision.REJECT,
                reason="env not available",
                evidence={},
            )
        ],
    )
    report = adapter.build_core_validation_report(_validation(), policy)
    assert report.valid is False
    assert any(issue.blocks_promotion for issue in report.issues)
    assert any("fealpy_gate_fealpy_environment_readiness" in issue.code for issue in report.issues)
