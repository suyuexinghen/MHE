from __future__ import annotations

from metaharness.core.graph_versions import CandidateRecord
from metaharness.core.models import (
    GraphSnapshot,
    SessionEvent,
    SessionEventType,
    ValidationIssue,
    ValidationIssueCategory,
    ValidationReport,
)
from metaharness.observability.events import SessionStore, make_session_event
from metaharness.provenance import AuditLog, ProvGraph, RelationKind
from metaharness_ext.jedi.contracts import (
    JediEvidenceBundle,
    JediPolicyReport,
    JediValidationReport,
)


class JediGovernanceAdapter:
    def __init__(
        self,
        *,
        session_id: str | None = None,
        actor: str = "jedi_governance_adapter",
    ) -> None:
        self.session_id = session_id
        self.actor = actor

    def _diagnostics_payload(self, bundle: JediEvidenceBundle) -> dict[str, object]:
        summary = bundle.summary
        if summary is None:
            return {}
        return {
            "diagnostic_files_scanned": len(summary.files_scanned),
            "ioda_groups_found": list(summary.ioda_groups_found),
            "ioda_groups_missing": list(summary.ioda_groups_missing),
            "minimizer_iterations": summary.minimizer_iterations,
            "outer_iterations": summary.outer_iterations,
            "inner_iterations": summary.inner_iterations,
            "initial_cost_function": summary.initial_cost_function,
            "final_cost_function": summary.final_cost_function,
            "initial_gradient_norm": summary.initial_gradient_norm,
            "final_gradient_norm": summary.final_gradient_norm,
            "gradient_norm_reduction": summary.gradient_norm_reduction,
            "observer_output_detected": summary.observer_output_detected,
            "posterior_output_detected": summary.posterior_output_detected,
        }

    def build_candidate_record(
        self,
        bundle: JediEvidenceBundle,
        policy: JediPolicyReport,
        *,
        snapshot: GraphSnapshot | None = None,
    ) -> CandidateRecord:
        validation = self._require_validation(bundle)
        graph_version = validation.graph_version_id or bundle.graph_version_id or 0
        candidate_snapshot = snapshot or GraphSnapshot(graph_version=graph_version)
        report = self.build_core_validation_report(validation, policy)
        candidate_id = validation.candidate_id or bundle.candidate_id or bundle.run_id
        return CandidateRecord(
            candidate_id=candidate_id,
            snapshot=candidate_snapshot,
            report=report,
            promoted=report.valid,
        )

    def build_core_validation_report(
        self,
        validation: JediValidationReport,
        policy: JediPolicyReport,
    ) -> ValidationReport:
        blocking_issues = [
            ValidationIssue(
                code="jedi_policy_blocker",
                message=reason,
                subject=validation.task_id,
                category=ValidationIssueCategory.PROMOTION_BLOCKER,
                blocks_promotion=True,
            )
            for reason in validation.blocking_reasons
        ]
        gate_issues = [
            ValidationIssue(
                code=f"jedi_gate_{gate.gate}",
                message=gate.reason,
                subject=validation.task_id,
                category=ValidationIssueCategory.PROMOTION_BLOCKER,
                blocks_promotion=gate.decision.value != "allow",
            )
            for gate in policy.gates
            if gate.decision.value != "allow"
        ]
        valid = validation.passed and policy.decision == "allow"
        return ValidationReport(valid=valid, issues=[*blocking_issues, *gate_issues])

    def build_session_events(
        self,
        bundle: JediEvidenceBundle,
        policy: JediPolicyReport,
    ) -> list[SessionEvent]:
        validation = self._require_validation(bundle)
        session_id = validation.session_id or bundle.session_id or self.session_id or validation.task_id
        events = list(validation.session_events)
        if not any(event.event_type == SessionEventType.SAFETY_GATE_EVALUATED for event in events):
            events.append(
                make_session_event(
                    session_id,
                    SessionEventType.SAFETY_GATE_EVALUATED,
                    graph_version=validation.graph_version_id or bundle.graph_version_id,
                    candidate_id=validation.candidate_id or bundle.candidate_id or bundle.run_id,
                    payload={
                        "decision": policy.decision,
                        "reason": policy.reason,
                        "gate_count": len(policy.gates),
                        **self._diagnostics_payload(bundle),
                    },
                )
            )
        return events

    def emit_runtime_evidence(
        self,
        bundle: JediEvidenceBundle,
        policy: JediPolicyReport,
        *,
        session_store: SessionStore,
        audit_log: AuditLog,
        provenance_graph: ProvGraph,
    ) -> dict[str, list[str]]:
        validation = self._require_validation(bundle)
        candidate_id = validation.candidate_id or bundle.candidate_id or bundle.run_id
        graph_version = validation.graph_version_id or bundle.graph_version_id
        session_events = self.build_session_events(bundle, policy)
        audit_refs = list(bundle.audit_refs)
        provenance_refs = list(dict.fromkeys([*validation.provenance_refs, *bundle.run.reference_files]))

        candidate_entity = provenance_graph.add_entity(
            id=f"graph-candidate:{candidate_id}",
            kind="graph_candidate",
            candidate_id=candidate_id,
            graph_version=graph_version,
            task_id=validation.task_id,
        )
        if graph_version is not None:
            version_entity = provenance_graph.add_entity(
                id=f"graph-version:{graph_version}",
                kind="graph_version",
                graph_version=graph_version,
            )
            provenance_graph.relate(
                candidate_entity.id,
                RelationKind.WAS_DERIVED_FROM,
                version_entity.id,
            )
            provenance_refs.append(version_entity.id)

        for event in session_events:
            session_store.append(event)
            event_entity = provenance_graph.add_entity(
                id=f"session-event:{event.event_id}",
                kind="session_event",
                event_type=event.event_type.value,
                session_id=event.session_id,
                candidate_id=event.candidate_id,
                graph_version=event.graph_version,
                payload=event.payload,
                timestamp=event.timestamp.isoformat(),
            )
            provenance_graph.relate(
                event_entity.id,
                RelationKind.WAS_DERIVED_FROM,
                candidate_entity.id,
            )
            provenance_refs.append(event_entity.id)
            record = audit_log.append(
                f"session.{event.event_type.value}",
                actor=self.actor,
                payload={
                    "event_id": event.event_id,
                    "candidate_id": event.candidate_id,
                    "graph_version": event.graph_version,
                    "payload": event.payload,
                },
            )
            audit_refs.append(f"audit-record:{record.record_id}")

        handoff_record = audit_log.append(
            "jedi.governance_handoff",
            actor=self.actor,
            payload={
                "task_id": validation.task_id,
                "run_id": validation.run_id,
                "candidate_id": candidate_id,
                "graph_version": graph_version,
                "policy_decision": policy.decision,
                **self._diagnostics_payload(bundle),
            },
        )
        audit_refs.append(f"audit-record:{handoff_record.record_id}")
        return {
            "audit_refs": list(dict.fromkeys(audit_refs)),
            "provenance_refs": list(dict.fromkeys(provenance_refs)),
        }

    def _require_validation(self, bundle: JediEvidenceBundle) -> JediValidationReport:
        if bundle.validation is None:
            raise ValueError("JEDI evidence bundle requires an attached validation report")
        return bundle.validation
