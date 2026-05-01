from __future__ import annotations

from metaharness.core.graph_versions import CandidateRecord
from metaharness.core.models import SessionEventType
from metaharness.observability.events import InMemorySessionStore
from metaharness.provenance import AuditLog, ProvGraph
from metaharness_ext.pycfd.contracts import (
    PyCFDEvidenceBundle,
    PyCFDPolicyReport,
    PyCFDValidationReport,
)
from metaharness_ext.pycfd.governance import PyCFDGovernanceAdapter
from metaharness_ext.pycfd.types import PyCFDValidationStatus


class TestPyCFDGovernanceAdapter:
    def test_build_core_validation_passed(self):
        adapter = PyCFDGovernanceAdapter()
        pycfd_report = PyCFDValidationReport(
            task_id="t1",
            plan_ref="p1",
            artifact_ref="a1",
            passed=True,
            status=PyCFDValidationStatus.EXECUTED,
        )
        policy = PyCFDPolicyReport(
            passed=True,
            decision="allow",
            reason="ok",
            gates=[
                {"gate": "g1", "result": "pass", "reason": "ok"},
            ],
        )
        core = adapter.build_core_validation_report(pycfd_report, policy)
        assert core.valid is True

    def test_build_core_validation_failed(self):
        adapter = PyCFDGovernanceAdapter()
        pycfd_report = PyCFDValidationReport(
            task_id="t1",
            plan_ref="p1",
            artifact_ref="a1",
            passed=False,
            status=PyCFDValidationStatus.RESIDUAL_EXCEEDED,
        )
        policy = PyCFDPolicyReport(
            passed=False,
            decision="defer",
            reason="failed",
            gates=[
                {"gate": "g1", "result": "defer", "reason": "residual exceeded"},
            ],
        )
        core = adapter.build_core_validation_report(pycfd_report, policy)
        assert core.valid is False

    def test_build_candidate_record(self):
        adapter = PyCFDGovernanceAdapter()
        bundle = PyCFDEvidenceBundle(
            bundle_id="b1",
            task_id="t1",
            validation=PyCFDValidationReport(
                task_id="t1",
                plan_ref="p1",
                artifact_ref="a1",
                passed=True,
                status=PyCFDValidationStatus.EXECUTED,
            ),
        )
        policy = PyCFDPolicyReport(
            passed=True,
            decision="allow",
            reason="ok",
            gates=[
                {"gate": "g1", "result": "pass", "reason": "ok"},
            ],
        )
        record = adapter.build_candidate_record(bundle, policy)
        assert isinstance(record, CandidateRecord)
        assert record.promoted is True
        assert record.snapshot is not None

    def test_session_events_include_safety_gate(self):
        adapter = PyCFDGovernanceAdapter()
        bundle = PyCFDEvidenceBundle(
            bundle_id="b1",
            task_id="t1",
            validation=PyCFDValidationReport(
                task_id="t1",
                plan_ref="p1",
                artifact_ref="a1",
                passed=True,
                status=PyCFDValidationStatus.EXECUTED,
            ),
        )
        policy = PyCFDPolicyReport(
            passed=True,
            decision="allow",
            reason="ok",
            gates=[
                {"gate": "g1", "result": "pass", "reason": "ok"},
            ],
        )
        events = adapter.build_session_events(bundle, policy)
        assert any(e.event_type == SessionEventType.SAFETY_GATE_EVALUATED for e in events)

    def test_session_events_rejected_adds_reject_event(self):
        adapter = PyCFDGovernanceAdapter()
        bundle = PyCFDEvidenceBundle(
            bundle_id="b1",
            task_id="t1",
            validation=PyCFDValidationReport(
                task_id="t1",
                plan_ref="p1",
                artifact_ref="a1",
                passed=False,
                status=PyCFDValidationStatus.RESIDUAL_EXCEEDED,
            ),
        )
        policy = PyCFDPolicyReport(
            passed=False,
            decision="reject",
            reason="residual exceeded",
            gates=[
                {"gate": "g1", "result": "reject", "reason": "residual exceeded"},
            ],
        )
        events = adapter.build_session_events(bundle, policy)
        assert any(e.event_type == SessionEventType.CANDIDATE_REJECTED for e in events)

    def test_emit_runtime_evidence_placeholders(self):
        adapter = PyCFDGovernanceAdapter()
        bundle = PyCFDEvidenceBundle(
            bundle_id="b1",
            task_id="t1",
            evidence_refs=["ref1"],
            validation=PyCFDValidationReport(
                task_id="t1",
                plan_ref="p1",
                artifact_ref="a1",
                passed=True,
                status=PyCFDValidationStatus.EXECUTED,
            ),
        )
        policy = PyCFDPolicyReport(
            passed=True,
            decision="allow",
            reason="ok",
            gates=[
                {"gate": "g1", "result": "pass", "reason": "ok"},
            ],
        )
        result = adapter.emit_runtime_evidence(bundle, policy)
        assert "audit_refs" in result
        assert "provenance_refs" in result
        assert result["provenance_refs"]  # includes bundle evidence refs + derived refs

    def test_emit_runtime_evidence_with_session_store(self):
        adapter = PyCFDGovernanceAdapter()
        session_store = InMemorySessionStore()
        bundle = PyCFDEvidenceBundle(
            bundle_id="b1",
            task_id="t1",
            validation=PyCFDValidationReport(
                task_id="t1",
                plan_ref="p1",
                artifact_ref="a1",
                passed=True,
                status=PyCFDValidationStatus.EXECUTED,
            ),
        )
        policy = PyCFDPolicyReport(
            passed=True,
            decision="allow",
            reason="ok",
            gates=[
                {"gate": "g1", "result": "pass", "reason": "ok"},
            ],
        )
        result = adapter.emit_runtime_evidence(bundle, policy, session_store=session_store)
        events = session_store.get_events("t1")
        assert len(events) == 2  # CANDIDATE_VALIDATED + SAFETY_GATE_EVALUATED
        assert "audit_refs" in result

    def test_emit_runtime_evidence_with_prov_graph(self):
        adapter = PyCFDGovernanceAdapter()
        prov = ProvGraph()
        bundle = PyCFDEvidenceBundle(
            bundle_id="b1",
            task_id="t1",
            validation=PyCFDValidationReport(
                task_id="t1",
                plan_ref="p1",
                artifact_ref="a1",
                passed=True,
                status=PyCFDValidationStatus.EXECUTED,
            ),
        )
        policy = PyCFDPolicyReport(
            passed=True,
            decision="allow",
            reason="ok",
            gates=[
                {"gate": "g1", "result": "pass", "reason": "ok"},
            ],
        )
        result = adapter.emit_runtime_evidence(bundle, policy, provenance_graph=prov)
        assert len(prov.entities) >= 2  # candidate + version entities
        assert "provenance_refs" in result

    def test_emit_runtime_evidence_with_audit_log(self):
        adapter = PyCFDGovernanceAdapter()
        audit = AuditLog()
        bundle = PyCFDEvidenceBundle(
            bundle_id="b1",
            task_id="t1",
            validation=PyCFDValidationReport(
                task_id="t1",
                plan_ref="p1",
                artifact_ref="a1",
                passed=True,
                status=PyCFDValidationStatus.EXECUTED,
            ),
        )
        policy = PyCFDPolicyReport(
            passed=True,
            decision="allow",
            reason="ok",
            gates=[
                {"gate": "g1", "result": "pass", "reason": "ok"},
            ],
        )
        result = adapter.emit_runtime_evidence(bundle, policy, audit_log=audit)
        assert len(audit) >= 3  # 2 session events + governance_handoff
        assert result["audit_refs"]

    def test_policy_gate_issues_from_rejected_gate(self):
        adapter = PyCFDGovernanceAdapter()
        validation = PyCFDValidationReport(
            task_id="t1",
            plan_ref="p1",
            artifact_ref="a1",
            passed=True,
            status=PyCFDValidationStatus.EXECUTED,
        )
        policy = PyCFDPolicyReport(
            passed=False,
            decision="reject",
            reason="env unavailable",
            gates=[
                {
                    "gate": "pycfd_environment_readiness",
                    "result": "reject",
                    "reason": "PyCFD environment is not available.",
                },
            ],
        )
        issues = adapter._policy_gate_issues(validation, policy)
        assert len(issues) == 1
        assert issues[0].code == "pycfd_gate_pycfd_environment_readiness"
        assert issues[0].blocks_promotion is True

    def test_require_validation_raises_when_missing(self):
        adapter = PyCFDGovernanceAdapter()
        bundle = PyCFDEvidenceBundle(bundle_id="b1", task_id="t1")
        try:
            adapter._require_validation(bundle)
            assert False, "Should have raised"
        except ValueError:
            pass
