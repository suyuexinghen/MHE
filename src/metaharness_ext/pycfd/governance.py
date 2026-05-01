from __future__ import annotations

from metaharness.core.models import SessionEvent, SessionEventType
from metaharness.core.models import ValidationReport as CoreValidationReport
from metaharness_ext.pycfd.contracts import (
    PyCFDEvidenceBundle,
    PyCFDPolicyReport,
    PyCFDValidationReport,
)


class PyCFDGovernanceAdapter:
    """Bridges PyCFD extension artifacts to MHE core governance interfaces.

    Note: Full core integration (CandidateRecord, GraphSnapshot, audit log, provenance
    graph) requires runtime injection of session state. This adapter provides the
    validation and session event bridges; graph promotion requires the MHE runtime.
    """

    def build_core_validation_report(
        self,
        pycfd_report: PyCFDValidationReport,
        policy: PyCFDPolicyReport | None = None,
    ) -> CoreValidationReport:
        """Convert PyCFD validation report to MHE core format."""
        return CoreValidationReport(
            valid=pycfd_report.passed,
            issues=list(pycfd_report.issues),
        )

    def build_session_events(
        self,
        bundle: PyCFDEvidenceBundle,
        policy: PyCFDPolicyReport,
        session_id: str = "pycfd-session",
        graph_version: int = 0,
    ) -> list[SessionEvent]:
        """Emit session events for audit trail."""
        import uuid
        from datetime import datetime, timezone

        events: list[SessionEvent] = []
        _ts = datetime.now(timezone.utc)

        if bundle.validation and bundle.validation.passed:
            events.append(
                SessionEvent(
                    event_id=f"evt-{uuid.uuid4().hex[:12]}",
                    session_id=session_id,
                    event_type=SessionEventType.CANDIDATE_VALIDATED,
                    graph_version=graph_version,
                    candidate_id=bundle.bundle_id,
                    timestamp=_ts,
                    payload={"bundle_id": bundle.bundle_id},
                )
            )

        events.append(
            SessionEvent(
                event_id=f"evt-{uuid.uuid4().hex[:12]}",
                session_id=session_id,
                event_type=SessionEventType.SAFETY_GATE_EVALUATED,
                graph_version=graph_version,
                timestamp=_ts,
                payload={
                    "bundle_id": bundle.bundle_id,
                    "decision": policy.decision,
                    "reason": policy.reason,
                },
            )
        )

        if policy.decision == "reject":
            events.append(
                SessionEvent(
                    event_id=f"evt-{uuid.uuid4().hex[:12]}",
                    session_id=session_id,
                    event_type=SessionEventType.CANDIDATE_REJECTED,
                    graph_version=graph_version,
                    candidate_id=bundle.bundle_id,
                    timestamp=_ts,
                    payload={"bundle_id": bundle.bundle_id, "reason": policy.reason},
                )
            )

        return events

    def emit_runtime_evidence(self, bundle: PyCFDEvidenceBundle, policy: PyCFDPolicyReport) -> dict:
        """Emit evidence to session store, audit log, and provenance graph.

        Placeholder — full MHE core integration requires runtime injection of
        SessionStore, AuditLog, and ProvGraph instances.
        """
        return {
            "bundle_id": bundle.bundle_id,
            "policy_decision": policy.decision,
            "evidence_refs": bundle.evidence_refs,
        }
