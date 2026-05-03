from __future__ import annotations

from metaharness.core.graph_versions import CandidateRecord
from metaharness.core.models import GraphSnapshot, SessionEvent, SessionEventType, ValidationReport
from metaharness.observability.events import make_session_event
from metaharness.provenance import AuditLog, ProvGraph, RelationKind
from metaharness_ext.boutpp.contracts import (
    BoutPPEvidenceBundle,
    BoutPPPolicyReport,
    BoutPPValidationReport,
)


class BoutPPGovernanceAdapter:
    def __init__(self, *, session_id: str | None = None, actor: str = "boutpp_governance_adapter") -> None:
        self.session_id = session_id
        self.actor = actor

    def build_core_validation_report(
        self, validation: BoutPPValidationReport, policy: BoutPPPolicyReport
    ) -> ValidationReport:
        issues = list(validation.issues)
        valid = (
            validation.passed
            and not validation.blocks_promotion
            and policy.passed
            and policy.decision == "allow"
            and not any(issue.blocks_promotion for issue in issues)
        )
        return ValidationReport(valid=valid, issues=issues)

    def build_candidate_record(
        self,
        bundle: BoutPPEvidenceBundle,
        policy: BoutPPPolicyReport,
        *,
        snapshot: GraphSnapshot | None = None,
    ) -> CandidateRecord:
        validation = self._require_validation(bundle)
        report = self.build_core_validation_report(validation, policy)
        candidate_snapshot = snapshot or GraphSnapshot(graph_version=self._resolve_graph_version(bundle, validation))
        return CandidateRecord(
            candidate_id=self._resolve_candidate_id(bundle, validation, candidate_snapshot),
            snapshot=candidate_snapshot,
            report=report,
            promoted=report.valid,
        )

    def build_session_events(
        self,
        bundle: BoutPPEvidenceBundle,
        policy: BoutPPPolicyReport,
    ) -> list[SessionEvent]:
        validation = self._require_validation(bundle)
        session_id = self.session_id or validation.task_id
        candidate_id = self._resolve_candidate_id(
            bundle,
            validation,
            GraphSnapshot(graph_version=self._resolve_graph_version(bundle, validation)),
        )
        graph_version = self._resolve_graph_version(bundle, validation) or None
        events = [
            make_session_event(
                session_id,
                SessionEventType.CANDIDATE_VALIDATED,
                graph_version=graph_version,
                candidate_id=candidate_id,
                payload={"valid": validation.passed, "issues": [issue.model_dump(mode="json") for issue in validation.issues]},
            ),
            make_session_event(
                session_id,
                SessionEventType.SAFETY_GATE_EVALUATED,
                graph_version=graph_version,
                candidate_id=candidate_id,
                payload={"decision": policy.decision, "reason": policy.reason, "gate_count": len(policy.gates)},
            ),
        ]
        if policy.decision == "reject":
            events.append(
                make_session_event(
                    session_id,
                    SessionEventType.CANDIDATE_REJECTED,
                    graph_version=graph_version,
                    candidate_id=candidate_id,
                    payload={"decision": policy.decision, "reason": policy.reason},
                )
            )
        return events

    def emit_runtime_evidence(
        self,
        bundle: BoutPPEvidenceBundle,
        policy: BoutPPPolicyReport,
        *,
        audit_log: AuditLog | None = None,
        provenance_graph: ProvGraph | None = None,
    ) -> dict[str, list[str]]:
        validation = self._require_validation(bundle)
        graph_version = self._resolve_graph_version(bundle, validation) or None
        candidate_id = self._resolve_candidate_id(bundle, validation, GraphSnapshot(graph_version=graph_version or 0))
        session_events = self.build_session_events(bundle, policy)
        audit_refs: list[str] = []
        provenance_refs = list(dict.fromkeys([*bundle.evidence_refs, *validation.evidence_refs]))
        if provenance_graph is not None:
            candidate_entity = provenance_graph.add_entity(
                id=f"graph-candidate:{candidate_id}",
                kind="graph_candidate",
                candidate_id=candidate_id,
                graph_version=graph_version,
                task_id=validation.task_id,
            )
            if graph_version is not None:
                version_entity = provenance_graph.add_entity(id=f"graph-version:{graph_version}", kind="graph_version", graph_version=graph_version)
                provenance_graph.relate(candidate_entity.id, RelationKind.WAS_DERIVED_FROM, version_entity.id)
                provenance_refs.append(version_entity.id)
        if audit_log is not None:
            for event in session_events:
                audit_entry = audit_log.record(
                    actor=self.actor,
                    action=event.event_type.value,
                    subject=validation.task_id,
                    details=event.payload,
                )
                audit_refs.append(audit_entry.entry_id)
        return {"audit_refs": audit_refs, "provenance_refs": provenance_refs}

    def _require_validation(self, bundle: BoutPPEvidenceBundle) -> BoutPPValidationReport:
        if bundle.validation is None:
            raise ValueError("validation report is required")
        return bundle.validation

    def _resolve_graph_version(self, bundle: BoutPPEvidenceBundle, validation: BoutPPValidationReport) -> int:
        if bundle.plan is not None and hasattr(bundle.plan, "graph_metadata"):
            graph_version = bundle.plan.graph_metadata.get("graph_version")
            if isinstance(graph_version, int):
                return graph_version
        return validation.summary_metrics.get("graph_version", 0) if isinstance(validation.summary_metrics.get("graph_version", 0), int) else 0

    def _resolve_candidate_id(
        self,
        bundle: BoutPPEvidenceBundle,
        validation: BoutPPValidationReport,
        snapshot: GraphSnapshot,
    ) -> str:
        if bundle.plan is not None:
            return bundle.plan.plan_id
        return f"boutpp-candidate-{validation.artifact_ref}-{snapshot.graph_version}"
