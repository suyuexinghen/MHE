from __future__ import annotations

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
        policy = PyCFDPolicyReport(passed=True, decision="allow", reason="ok")
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
        core = adapter.build_core_validation_report(pycfd_report)
        assert core.valid is False

    def test_session_events_include_safety_gate(self):
        adapter = PyCFDGovernanceAdapter()
        bundle = PyCFDEvidenceBundle(bundle_id="b1", task_id="t1")
        policy = PyCFDPolicyReport(passed=True, decision="allow", reason="ok")
        events = adapter.build_session_events(bundle, policy)
        from metaharness.core.models import SessionEventType

        assert any(e.event_type == SessionEventType.SAFETY_GATE_EVALUATED for e in events)

    def test_session_events_rejected_adds_reject_event(self):
        adapter = PyCFDGovernanceAdapter()
        bundle = PyCFDEvidenceBundle(bundle_id="b1", task_id="t1")
        policy = PyCFDPolicyReport(passed=False, decision="reject", reason="failed")
        events = adapter.build_session_events(bundle, policy)
        from metaharness.core.models import SessionEventType

        assert any(e.event_type == SessionEventType.CANDIDATE_REJECTED for e in events)

    def test_emit_runtime_evidence(self):
        adapter = PyCFDGovernanceAdapter()
        bundle = PyCFDEvidenceBundle(
            bundle_id="b1",
            task_id="t1",
            evidence_refs=["ref1"],
        )
        policy = PyCFDPolicyReport(passed=True, decision="allow", reason="ok")
        result = adapter.emit_runtime_evidence(bundle, policy)
        assert result["bundle_id"] == "b1"
        assert result["policy_decision"] == "allow"
