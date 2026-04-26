"""Thin helpers for recording execution artifacts and lifecycle evidence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from metaharness.core.models import SessionEvent, SessionEventType
from metaharness.observability.events import SessionStore, make_session_event
from metaharness.provenance import (
    ArtifactSnapshot,
    ArtifactSnapshotStore,
    AuditLog,
    ProvGraph,
    RelationKind,
)
from metaharness.sdk.execution import (
    EvidenceBundleProtocol,
    RunArtifactProtocol,
    ValidationOutcomeProtocol,
)


@dataclass(slots=True)
class ExecutionEvidenceRecord:
    """Snapshot and event references produced for one execution result."""

    session_events: list[SessionEvent]
    run_snapshot: ArtifactSnapshot
    validation_snapshot: ArtifactSnapshot
    evidence_snapshot: ArtifactSnapshot
    audit_refs: list[str]
    provenance_refs: list[str]


class ExecutionEvidenceRecorder:
    """Persist execution artifacts and emit session lifecycle evidence."""

    def __init__(
        self,
        *,
        session_store: SessionStore,
        artifact_store: ArtifactSnapshotStore,
        provenance_graph: ProvGraph | None = None,
        audit_log: AuditLog | None = None,
        actor: str = "execution_evidence_recorder",
    ) -> None:
        self.session_store = session_store
        self.artifact_store = artifact_store
        self.provenance_graph = provenance_graph
        self.audit_log = audit_log
        self.actor = actor

    def record(
        self,
        *,
        session_id: str,
        run_artifact: RunArtifactProtocol,
        validation_outcome: ValidationOutcomeProtocol,
        evidence_bundle: EvidenceBundleProtocol,
        candidate_id: str | None = None,
        graph_version: int | None = None,
        policy_decision: str | None = None,
        safety_payload: dict[str, object] | None = None,
    ) -> ExecutionEvidenceRecord:
        resolved_candidate_id = (
            candidate_id
            or self._coerce_identifier(validation_outcome, ("candidate_id", "task_id"))
            or self._coerce_identifier(run_artifact, ("artifact_id",))
        )

        run_snapshot = self.artifact_store.save(
            "run_artifact",
            self._artifact_ref(
                run_artifact, "artifact_id", "run_id", "task_id", fallback_prefix="run-artifact"
            ),
            self._payload_for(run_artifact),
            graph_version=graph_version,
            candidate_id=resolved_candidate_id,
        )
        validation_snapshot = self.artifact_store.save(
            "validation_outcome",
            self._artifact_ref(
                validation_outcome,
                "validation_id",
                "task_id",
                fallback_prefix="validation",
            ),
            self._payload_for(validation_outcome),
            graph_version=graph_version,
            candidate_id=resolved_candidate_id,
            parent_snapshot_id=run_snapshot.snapshot_id,
        )
        evidence_snapshot = self.artifact_store.save(
            "evidence_bundle",
            self._evidence_ref(evidence_bundle),
            self._payload_for(evidence_bundle),
            graph_version=graph_version,
            candidate_id=resolved_candidate_id,
            parent_snapshot_id=validation_snapshot.snapshot_id,
        )

        session_events = [
            self._append_event(
                session_id,
                SessionEventType.CANDIDATE_VALIDATED,
                candidate_id=resolved_candidate_id,
                graph_version=graph_version,
                payload={
                    "status": self._stringify_status(validation_outcome),
                    "run_artifact_ref": run_snapshot.artifact_ref,
                    "validation_snapshot_id": validation_snapshot.snapshot_id,
                    "evidence_snapshot_id": evidence_snapshot.snapshot_id,
                },
            )
        ]

        resolved_policy = policy_decision or self._policy_decision_for_status(validation_outcome)
        if resolved_policy != "allow" or safety_payload is not None:
            session_events.append(
                self._append_event(
                    session_id,
                    SessionEventType.SAFETY_GATE_EVALUATED,
                    candidate_id=resolved_candidate_id,
                    graph_version=graph_version,
                    payload={
                        "decision": resolved_policy,
                        "run_artifact_ref": run_snapshot.artifact_ref,
                        "validation_snapshot_id": validation_snapshot.snapshot_id,
                        "evidence_snapshot_id": evidence_snapshot.snapshot_id,
                        **dict(safety_payload or {}),
                    },
                )
            )
        if resolved_policy == "reject":
            session_events.append(
                self._append_event(
                    session_id,
                    SessionEventType.CANDIDATE_REJECTED,
                    candidate_id=resolved_candidate_id,
                    graph_version=graph_version,
                    payload={
                        "status": self._stringify_status(validation_outcome),
                        "run_artifact_ref": run_snapshot.artifact_ref,
                        "validation_snapshot_id": validation_snapshot.snapshot_id,
                        "evidence_snapshot_id": evidence_snapshot.snapshot_id,
                    },
                )
            )

        provenance_refs = self._record_provenance(
            run_snapshot=run_snapshot,
            validation_snapshot=validation_snapshot,
            evidence_snapshot=evidence_snapshot,
            session_events=session_events,
        )
        audit_refs = self._record_audit(
            run_snapshot=run_snapshot,
            validation_snapshot=validation_snapshot,
            evidence_snapshot=evidence_snapshot,
            session_events=session_events,
        )

        return ExecutionEvidenceRecord(
            session_events=session_events,
            run_snapshot=run_snapshot,
            validation_snapshot=validation_snapshot,
            evidence_snapshot=evidence_snapshot,
            audit_refs=audit_refs,
            provenance_refs=provenance_refs,
        )

    def _append_event(
        self,
        session_id: str,
        event_type: SessionEventType,
        *,
        candidate_id: str | None,
        graph_version: int | None,
        payload: dict[str, object],
    ) -> SessionEvent:
        event = make_session_event(
            session_id,
            event_type,
            graph_version=graph_version,
            candidate_id=candidate_id,
            payload=payload,
        )
        self.session_store.append(event)
        return event

    def _record_provenance(
        self,
        *,
        run_snapshot: ArtifactSnapshot,
        validation_snapshot: ArtifactSnapshot,
        evidence_snapshot: ArtifactSnapshot,
        session_events: list[SessionEvent],
    ) -> list[str]:
        if self.provenance_graph is None:
            return []

        refs = [
            self.provenance_graph.add_entity(
                id=f"artifact-snapshot:{run_snapshot.snapshot_id}",
                kind="artifact_snapshot",
                artifact_kind=run_snapshot.artifact_kind,
                artifact_ref=run_snapshot.artifact_ref,
                graph_version=run_snapshot.graph_version,
                candidate_id=run_snapshot.candidate_id,
            ).id,
            self.provenance_graph.add_entity(
                id=f"artifact-snapshot:{validation_snapshot.snapshot_id}",
                kind="artifact_snapshot",
                artifact_kind=validation_snapshot.artifact_kind,
                artifact_ref=validation_snapshot.artifact_ref,
                graph_version=validation_snapshot.graph_version,
                candidate_id=validation_snapshot.candidate_id,
            ).id,
            self.provenance_graph.add_entity(
                id=f"artifact-snapshot:{evidence_snapshot.snapshot_id}",
                kind="artifact_snapshot",
                artifact_kind=evidence_snapshot.artifact_kind,
                artifact_ref=evidence_snapshot.artifact_ref,
                graph_version=evidence_snapshot.graph_version,
                candidate_id=evidence_snapshot.candidate_id,
            ).id,
        ]
        self.provenance_graph.relate(refs[1], RelationKind.WAS_DERIVED_FROM, refs[0])
        self.provenance_graph.relate(refs[2], RelationKind.WAS_DERIVED_FROM, refs[1])
        for event in session_events:
            event_ref = self.provenance_graph.add_entity(
                id=f"session-event:{event.event_id}",
                kind="session_event",
                event_type=event.event_type.value,
                session_id=event.session_id,
                candidate_id=event.candidate_id,
                graph_version=event.graph_version,
                payload=event.payload,
                timestamp=event.timestamp.isoformat(),
            ).id
            self.provenance_graph.relate(event_ref, RelationKind.WAS_DERIVED_FROM, refs[2])
            refs.append(event_ref)
        return refs

    def _record_audit(
        self,
        *,
        run_snapshot: ArtifactSnapshot,
        validation_snapshot: ArtifactSnapshot,
        evidence_snapshot: ArtifactSnapshot,
        session_events: list[SessionEvent],
    ) -> list[str]:
        if self.audit_log is None:
            return []

        refs: list[str] = []
        snapshot_record = self.audit_log.append(
            "execution.artifact_snapshots_recorded",
            actor=self.actor,
            payload={
                "run_snapshot_id": run_snapshot.snapshot_id,
                "validation_snapshot_id": validation_snapshot.snapshot_id,
                "evidence_snapshot_id": evidence_snapshot.snapshot_id,
                "candidate_id": evidence_snapshot.candidate_id,
                "graph_version": evidence_snapshot.graph_version,
            },
        )
        refs.append(f"audit-record:{snapshot_record.record_id}")
        for event in session_events:
            event_record = self.audit_log.append(
                f"session.{event.event_type.value}",
                actor=self.actor,
                payload={
                    "event_id": event.event_id,
                    "candidate_id": event.candidate_id,
                    "graph_version": event.graph_version,
                    "payload": event.payload,
                },
            )
            refs.append(f"audit-record:{event_record.record_id}")
        return refs

    def _artifact_ref(self, value: object, *attribute_names: str, fallback_prefix: str) -> str:
        for attribute_name in attribute_names:
            identifier = self._coerce_identifier(value, (attribute_name,))
            if identifier is not None:
                return identifier
        return f"{fallback_prefix}:{id(value)}"

    def _evidence_ref(self, evidence_bundle: EvidenceBundleProtocol) -> str:
        bundle_id = self._coerce_identifier(evidence_bundle, ("bundle_id",))
        if bundle_id is not None:
            return bundle_id
        run_id = self._coerce_identifier(evidence_bundle, ("run_id", "task_id"))
        if run_id is not None:
            return f"evidence:{run_id}"
        return f"evidence:{id(evidence_bundle)}"

    def _coerce_identifier(self, value: object, attribute_names: tuple[str, ...]) -> str | None:
        for attribute_name in attribute_names:
            raw = getattr(value, attribute_name, None)
            if isinstance(raw, str) and raw:
                return raw
            if raw is not None:
                return str(raw)
        return None

    def _payload_for(self, value: object) -> dict[str, Any]:
        if hasattr(value, "model_dump"):
            dumped = value.model_dump(mode="json")
            if isinstance(dumped, dict):
                return dumped
        if isinstance(value, dict):
            return dict(value)
        raw_dict = getattr(value, "__dict__", None)
        if isinstance(raw_dict, dict):
            return dict(raw_dict)
        return {"value": repr(value)}

    def _stringify_status(self, validation_outcome: ValidationOutcomeProtocol) -> str:
        status = getattr(validation_outcome, "status", None)
        return str(status) if status is not None else "unknown"

    def _policy_decision_for_status(self, validation_outcome: ValidationOutcomeProtocol) -> str:
        status = self._stringify_status(validation_outcome).lower()
        if status in {"validated", "executed", "completed", "passed", "success", "allow"}:
            return "allow"
        if status in {"environment_invalid", "rejected", "reject"}:
            return "reject"
        return "defer"
