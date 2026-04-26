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
from metaharness_ext.ai4pde.contracts import ScientificEvidenceBundle, ValidationBundle


class AI4PDEGovernanceAdapter:
    def __init__(
        self,
        *,
        session_id: str | None = None,
        actor: str = "ai4pde_governance_adapter",
    ) -> None:
        self.session_id = session_id
        self.actor = actor

    def build_core_validation_report(self, validation: ValidationBundle) -> ValidationReport:
        issues = [
            ValidationIssue(
                code=f"ai4pde_{violation}",
                message=violation.replace("_", " "),
                subject=validation.task_id,
                category=ValidationIssueCategory.PROMOTION_BLOCKER,
                blocks_promotion=True,
            )
            for violation in validation.violations
        ]
        return ValidationReport(
            valid=validation.next_action.value == "accept" and not issues,
            issues=issues,
        )

    def build_candidate_record(
        self,
        bundle: ScientificEvidenceBundle,
        *,
        validation: ValidationBundle | None = None,
        snapshot: GraphSnapshot | None = None,
    ) -> CandidateRecord:
        validation = validation or self._validation_from_bundle(bundle)
        graph_version = validation.graph_version_id or bundle.graph_version_id
        candidate_snapshot = snapshot or GraphSnapshot(graph_version=graph_version)
        report = self.build_core_validation_report(validation)
        return CandidateRecord(
            candidate_id=self._resolve_candidate_id(bundle, validation),
            snapshot=candidate_snapshot,
            report=report,
            promoted=report.valid,
        )

    def build_session_events(
        self,
        bundle: ScientificEvidenceBundle,
        *,
        validation: ValidationBundle | None = None,
    ) -> list[SessionEvent]:
        validation = validation or self._validation_from_bundle(bundle)
        session_id = self.session_id or validation.task_id
        candidate_id = self._resolve_candidate_id(bundle, validation)
        events = [
            event.model_copy(update={"session_id": session_id})
            for event in validation.session_events
        ]
        if not any(event.event_type == SessionEventType.SAFETY_GATE_EVALUATED for event in events):
            events.append(
                make_session_event(
                    session_id,
                    SessionEventType.SAFETY_GATE_EVALUATED,
                    graph_version=validation.graph_version_id,
                    candidate_id=candidate_id,
                    payload={
                        "decision": validation.next_action.value,
                        "violations": list(validation.violations),
                        "solver_family": bundle.solver_config.get("solver_family"),
                        "graph_family": bundle.graph_metadata.get("graph_family"),
                    },
                )
            )
        return events

    def emit_runtime_evidence(
        self,
        bundle: ScientificEvidenceBundle,
        *,
        validation: ValidationBundle,
        session_store: SessionStore,
        audit_log: AuditLog,
        provenance_graph: ProvGraph,
    ) -> dict[str, list[str]]:
        candidate_id = self._resolve_candidate_id(bundle, validation)
        graph_version = validation.graph_version_id or bundle.graph_version_id
        session_events = self.build_session_events(bundle, validation=validation)
        audit_refs: list[str] = []
        provenance_refs = list(
            dict.fromkeys(
                [
                    *bundle.provenance_refs,
                    *(
                        validation.scored_evidence.evidence_refs
                        if validation.scored_evidence is not None
                        else []
                    ),
                    f"provenance://ai4pde/validation/{validation.task_id}",
                ]
            )
        )

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
            "ai4pde.governance_handoff",
            actor=self.actor,
            payload={
                "task_id": validation.task_id,
                "candidate_id": candidate_id,
                "graph_version": graph_version,
                "next_action": validation.next_action.value,
                "solver_family": bundle.solver_config.get("solver_family"),
                "graph_family": bundle.graph_metadata.get("graph_family"),
            },
        )
        audit_refs.append(f"audit-record:{handoff_record.record_id}")
        return {
            "audit_refs": list(dict.fromkeys(audit_refs)),
            "provenance_refs": list(dict.fromkeys(provenance_refs)),
        }

    def handoff_candidate_record(
        self,
        runtime: object | None,
        bundle: ScientificEvidenceBundle,
        *,
        validation: ValidationBundle,
        snapshot: GraphSnapshot | None = None,
    ) -> CandidateRecord:
        candidate_record = self.build_candidate_record(
            bundle,
            validation=validation,
            snapshot=snapshot,
        )
        if runtime is None or not hasattr(runtime, "ingest_candidate_record"):
            return candidate_record
        refs = self.emit_runtime_evidence(
            bundle,
            validation=validation,
            session_store=runtime.session_store,
            audit_log=runtime.audit_log,
            provenance_graph=runtime.provenance_graph,
        )
        bundle.provenance_refs[:] = list(
            dict.fromkeys([*bundle.provenance_refs, *refs["provenance_refs"]])
        )
        if validation.scored_evidence is not None:
            validation.scored_evidence.evidence_refs = list(
                dict.fromkeys([*validation.scored_evidence.evidence_refs, *refs["audit_refs"]])
            )
        return runtime.ingest_candidate_record(candidate_record, emit_runtime_evidence=False)

    def _resolve_candidate_id(
        self,
        bundle: ScientificEvidenceBundle,
        validation: ValidationBundle,
    ) -> str:
        return (
            validation.candidate_identity.candidate_id
            or bundle.candidate_identity.candidate_id
            or bundle.task_id
        )

    def _validation_from_bundle(self, bundle: ScientificEvidenceBundle) -> ValidationBundle:
        payload = bundle.provenance.get("validation_bundle")
        if payload is None:
            raise ValueError(
                "AI4PDE evidence bundle requires embedded validation bundle provenance"
            )
        return ValidationBundle.model_validate(payload)
