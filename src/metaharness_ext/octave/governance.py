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
from metaharness_ext.octave.contracts import (
    OctaveEvidenceBundle,
    OctavePolicyReport,
    OctaveValidationReport,
)


class OctaveGovernanceAdapter:
    def __init__(
        self,
        *,
        session_id: str | None = None,
        actor: str = "octave_governance_adapter",
    ) -> None:
        self.session_id = session_id
        self.actor = actor

    def build_core_validation_report(
        self,
        validation: OctaveValidationReport,
        policy: OctavePolicyReport,
    ) -> ValidationReport:
        issues = list(validation.issues)
        issues.extend(self._policy_gate_issues(validation, policy))
        valid = (
            validation.passed
            and not validation.blocks_promotion
            and validation.governance_state == "ready"
            and policy.passed
            and policy.decision == "allow"
            and not any(issue.blocks_promotion for issue in issues)
        )
        return ValidationReport(valid=valid, issues=issues)

    def build_candidate_record(
        self,
        bundle: OctaveEvidenceBundle,
        policy: OctavePolicyReport,
        *,
        snapshot: GraphSnapshot | None = None,
    ) -> CandidateRecord:
        validation = self._require_validation(bundle)
        report = self.build_core_validation_report(validation, policy)
        candidate_snapshot = snapshot or GraphSnapshot(
            graph_version=self._resolve_graph_version(bundle, validation)
        )
        return CandidateRecord(
            candidate_id=self._resolve_candidate_id(bundle, validation, candidate_snapshot),
            snapshot=candidate_snapshot,
            report=report,
            promoted=report.valid,
        )

    def build_session_events(
        self,
        bundle: OctaveEvidenceBundle,
        policy: OctavePolicyReport,
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
                payload={
                    "valid": validation.passed,
                    "issues": [issue.model_dump(mode="json") for issue in validation.issues],
                },
            ),
            make_session_event(
                session_id,
                SessionEventType.SAFETY_GATE_EVALUATED,
                graph_version=graph_version,
                candidate_id=candidate_id,
                payload={
                    "decision": policy.decision,
                    "reason": policy.reason,
                    "gate_count": len(policy.gates),
                    "run_status": bundle.artifact.status if bundle.artifact is not None else None,
                    "validation_status": validation.status.value,
                },
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
        bundle: OctaveEvidenceBundle,
        policy: OctavePolicyReport,
        *,
        session_store: SessionStore | None = None,
        audit_log: AuditLog | None = None,
        provenance_graph: ProvGraph | None = None,
    ) -> dict[str, list[str]]:
        validation = self._require_validation(bundle)
        graph_version = self._resolve_graph_version(bundle, validation) or None
        candidate_id = self._resolve_candidate_id(
            bundle,
            validation,
            GraphSnapshot(graph_version=graph_version or 0),
        )
        session_events = self.build_session_events(bundle, policy)
        audit_refs: list[str] = []
        provenance_refs = list(
            dict.fromkeys(
                [
                    *bundle.evidence_refs,
                    *validation.evidence_refs,
                    f"octave://run/{validation.task_id}/{validation.run_id}",
                    f"octave://artifact/{validation.artifact_ref}",
                    *(f"octave://file/{path}" for path in validation.evidence_files),
                ]
            )
        )

        candidate_entity = None
        if provenance_graph is not None:
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

            if bundle.artifact is not None and bundle.artifact.raw_output_path is not None:
                raw_entity = provenance_graph.add_entity(
                    id=f"octave-raw-output:{bundle.artifact.artifact_id}",
                    kind="octave_raw_output",
                    path=bundle.artifact.raw_output_path,
                )
                provenance_graph.relate(
                    candidate_entity.id, RelationKind.WAS_DERIVED_FROM, raw_entity.id
                )
                provenance_refs.append(raw_entity.id)

        for event in session_events:
            if session_store is not None:
                session_store.append(event)
            if provenance_graph is not None and candidate_entity is not None:
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
            if audit_log is not None:
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

        if audit_log is not None:
            handoff_record = audit_log.append(
                "octave.governance_handoff",
                actor=self.actor,
                payload={
                    "task_id": validation.task_id,
                    "run_id": validation.run_id,
                    "artifact_id": validation.artifact_ref,
                    "candidate_id": candidate_id,
                    "graph_version": graph_version,
                    "policy_decision": policy.decision,
                    "validation_status": validation.status.value,
                    "governance_state": validation.governance_state,
                },
            )
            audit_refs.append(f"audit-record:{handoff_record.record_id}")
        return {
            "audit_refs": list(dict.fromkeys(audit_refs)),
            "provenance_refs": list(dict.fromkeys(provenance_refs)),
        }

    def record_with_artifact_store(
        self,
        bundle: OctaveEvidenceBundle,
        policy: OctavePolicyReport,
        *,
        session_store: SessionStore | None = None,
        audit_log: AuditLog | None = None,
        provenance_graph: ProvGraph | None = None,
        artifact_store: object | None = None,
    ) -> dict[str, list[str]]:
        refs = self.emit_runtime_evidence(
            bundle,
            policy,
            session_store=session_store,
            audit_log=audit_log,
            provenance_graph=provenance_graph,
        )
        artifact_refs: list[str] = []
        if artifact_store is not None and bundle.artifact is not None:
            snapshot = {
                "artifact_id": bundle.artifact.artifact_id,
                "task_id": bundle.task_id,
                "run_id": bundle.run_id,
                "output_files": list(bundle.artifact.output_files),
                "log_files": list(bundle.artifact.log_files),
            }
            for method_name in ("record", "append", "save"):
                method = getattr(artifact_store, method_name, None)
                if callable(method):
                    recorded = method(snapshot)
                    artifact_refs.append(str(recorded or snapshot["artifact_id"]))
                    break
        return {**refs, "artifact_refs": artifact_refs}

    def _policy_gate_issues(
        self,
        validation: OctaveValidationReport,
        policy: OctavePolicyReport,
    ) -> list[ValidationIssue]:
        return [
            ValidationIssue(
                code=f"octave_gate_{gate.gate}",
                message=gate.reason,
                subject=validation.task_id,
                category=ValidationIssueCategory.PROMOTION_BLOCKER,
                blocks_promotion=gate.decision.value != "allow",
            )
            for gate in policy.gates
            if gate.decision.value != "allow"
        ]

    def _resolve_graph_version(
        self,
        bundle: OctaveEvidenceBundle,
        validation: OctaveValidationReport,
    ) -> int:
        metadata = bundle.metadata
        plan = bundle.plan
        raw_graph_version = (
            metadata.get("graph_version")
            or metadata.get("graph_version_id")
            or (plan.graph_metadata.get("graph_version") if plan else None)
            or 0
        )
        try:
            return int(raw_graph_version)
        except (TypeError, ValueError):
            return 0

    def _resolve_candidate_id(
        self,
        bundle: OctaveEvidenceBundle,
        validation: OctaveValidationReport,
        snapshot: GraphSnapshot,
    ) -> str:
        metadata = bundle.metadata
        plan = bundle.plan
        raw_candidate_id = (
            metadata.get("candidate_id")
            or (plan.promotion_metadata.get("candidate_id") if plan else None)
            or snapshot.graph_version
            and f"octave-candidate-v{snapshot.graph_version}"
            or validation.artifact_ref
        )
        return str(raw_candidate_id)

    def _require_validation(self, bundle: OctaveEvidenceBundle) -> OctaveValidationReport:
        if bundle.validation is None:
            raise ValueError("Octave evidence bundle requires an attached validation report")
        return bundle.validation
