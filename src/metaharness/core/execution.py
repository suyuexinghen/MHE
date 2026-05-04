"""Thin helpers for recording execution artifacts and lifecycle evidence."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from metaharness.core.execution_modes import ExecutionMode, InstantiationRecord
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
    AsyncExecutorProtocol,
    EvidenceBundleProtocol,
    ExecutionStatus,
    JobHandle,
    PollingStrategy,
    RunArtifactProtocol,
    RunPlanProtocol,
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
    instantiation_snapshot: ArtifactSnapshot | None = None


@dataclass(slots=True)
class ExecutionLifecycleResult:
    """Events and final artifact produced by one executor lifecycle."""

    job_handle: JobHandle
    run_artifact: RunArtifactProtocol | Any | None
    session_events: list[SessionEvent]


class ExecutionLifecycleService:
    """Coordinate async executor lifecycle state with session evidence events."""

    def __init__(
        self,
        *,
        executor: AsyncExecutorProtocol,
        session_store: SessionStore,
        polling_strategy: PollingStrategy | None = None,
    ) -> None:
        self.executor = executor
        self.session_store = session_store
        self.polling_strategy = polling_strategy

    async def run(
        self,
        *,
        session_id: str,
        plan: RunPlanProtocol | Any,
        candidate_id: str | None = None,
        graph_version: int | None = None,
        timeout: float | None = None,
    ) -> ExecutionLifecycleResult:
        job_handle = await self.executor.submit(plan)
        session_events = [
            self._append_event(
                session_id,
                SessionEventType.TASK_SUBMITTED,
                job_handle=job_handle,
                candidate_id=candidate_id,
                graph_version=graph_version,
                payload={"plan_ref": self._plan_ref(plan)},
            )
        ]

        try:
            final_status = await self._poll_until_terminal(
                job_handle,
                session_id,
                session_events,
                candidate_id=candidate_id,
                graph_version=graph_version,
            )
            if final_status == ExecutionStatus.CANCELLED:
                self._sync_handle(job_handle, final_status)
                session_events.append(
                    self._append_event(
                        session_id,
                        SessionEventType.TASK_CANCELLED,
                        job_handle=job_handle,
                        candidate_id=candidate_id,
                        graph_version=graph_version,
                    )
                )
                return ExecutionLifecycleResult(job_handle, None, session_events)
            if final_status in {ExecutionStatus.FAILED, ExecutionStatus.TIMEOUT}:
                self._sync_handle(job_handle, final_status)
                session_events.append(
                    self._append_event(
                        session_id,
                        SessionEventType.TASK_FAILED,
                        job_handle=job_handle,
                        candidate_id=candidate_id,
                        graph_version=graph_version,
                    )
                )
                return ExecutionLifecycleResult(job_handle, None, session_events)

            run_artifact = await self.executor.await_result(job_handle.job_id, timeout=timeout)
            self._sync_handle(job_handle, ExecutionStatus.COMPLETED)
            session_events.append(
                self._append_event(
                    session_id,
                    SessionEventType.TASK_COMPLETED,
                    job_handle=job_handle,
                    candidate_id=candidate_id,
                    graph_version=graph_version,
                    payload={"artifact_ref": self._artifact_ref(run_artifact)},
                )
            )
            return ExecutionLifecycleResult(job_handle, run_artifact, session_events)
        except asyncio.CancelledError:
            await self.cancel(
                session_id=session_id,
                job_handle=job_handle,
                candidate_id=candidate_id,
                graph_version=graph_version,
            )
            raise
        except Exception as exc:
            self._sync_handle(job_handle, ExecutionStatus.FAILED)
            session_events.append(
                self._append_event(
                    session_id,
                    SessionEventType.TASK_FAILED,
                    job_handle=job_handle,
                    candidate_id=candidate_id,
                    graph_version=graph_version,
                    payload={"error": str(exc)},
                )
            )
            raise

    async def cancel(
        self,
        *,
        session_id: str,
        job_handle: JobHandle,
        candidate_id: str | None = None,
        graph_version: int | None = None,
    ) -> SessionEvent:
        await self.executor.cancel(job_handle.job_id)
        self._sync_handle(job_handle, ExecutionStatus.CANCELLED)
        return self._append_event(
            session_id,
            SessionEventType.TASK_CANCELLED,
            job_handle=job_handle,
            candidate_id=candidate_id,
            graph_version=graph_version,
        )

    async def _poll_until_terminal(
        self,
        job_handle: JobHandle,
        session_id: str,
        session_events: list[SessionEvent],
        *,
        candidate_id: str | None,
        graph_version: int | None,
    ) -> ExecutionStatus:
        attempt = 1
        total_wait = 0.0
        while True:
            status = await self.executor.poll(job_handle.job_id)
            self._sync_handle(job_handle, status)
            if status == ExecutionStatus.RUNNING and not any(
                event.event_type == SessionEventType.TASK_RUNNING for event in session_events
            ):
                session_events.append(
                    self._append_event(
                        session_id,
                        SessionEventType.TASK_RUNNING,
                        job_handle=job_handle,
                        candidate_id=candidate_id,
                        graph_version=graph_version,
                    )
                )
            if status in {
                ExecutionStatus.COMPLETED,
                ExecutionStatus.FAILED,
                ExecutionStatus.TIMEOUT,
                ExecutionStatus.CANCELLED,
            }:
                return status
            delay = self._next_delay(attempt, total_wait)
            if delay is None:
                return ExecutionStatus.TIMEOUT
            await asyncio.sleep(delay)
            total_wait += delay
            attempt += 1

    def _next_delay(self, attempt: int, total_wait: float) -> float | None:
        if self.polling_strategy is None:
            return 0.0
        remaining = self.polling_strategy.max_total_wait - total_wait
        if remaining <= 0:
            return None
        return min(self.polling_strategy.next_delay(attempt), remaining)

    def _append_event(
        self,
        session_id: str,
        event_type: SessionEventType,
        *,
        job_handle: JobHandle,
        candidate_id: str | None = None,
        graph_version: int | None = None,
        payload: dict[str, object] | None = None,
    ) -> SessionEvent:
        event_payload = {
            "job_id": job_handle.job_id,
            "backend": job_handle.backend,
            "status": job_handle.status.value,
            **dict(payload or {}),
        }
        event = make_session_event(
            session_id,
            event_type,
            graph_version=graph_version,
            candidate_id=candidate_id,
            payload=event_payload,
        )
        self.session_store.append(event)
        return event

    def _sync_handle(self, job_handle: JobHandle, status: ExecutionStatus) -> None:
        job_handle.status = status
        if status in {
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.TIMEOUT,
            ExecutionStatus.CANCELLED,
        }:
            job_handle.completed_at = datetime.now(timezone.utc)

    def _plan_ref(self, plan: object) -> str | None:
        return self._coerce_identifier(plan, ("plan_id", "task_id", "experiment_ref"))

    def _artifact_ref(self, artifact: object) -> str | None:
        return self._coerce_identifier(artifact, ("artifact_id", "run_id", "task_id"))

    def _coerce_identifier(self, value: object, attribute_names: tuple[str, ...]) -> str | None:
        for attribute_name in attribute_names:
            raw = getattr(value, attribute_name, None)
            if isinstance(raw, str) and raw:
                return raw
            if raw is not None:
                return str(raw)
        return None


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
        execution_mode: ExecutionMode | str | None = None,
        native_execution_mode: object | None = None,
        instantiation_record: InstantiationRecord | dict[str, Any] | None = None,
        external_evidence_refs: list[str] | None = None,
        extension_family: str | None = None,
    ) -> ExecutionEvidenceRecord:
        resolved_candidate_id = (
            candidate_id
            or self._coerce_identifier(validation_outcome, ("candidate_id", "task_id"))
            or self._coerce_identifier(run_artifact, ("artifact_id",))
        )
        native_mode = self._native_execution_mode(
            native_execution_mode,
            run_artifact,
            validation_outcome,
            evidence_bundle,
        )
        normalized_mode = ExecutionMode.normalize(
            execution_mode or native_mode,
            extension_family=extension_family,
        )
        external_refs = list(external_evidence_refs or [])
        execution_context = self._execution_context(
            normalized_mode,
            native_mode,
            external_refs,
            extension_family,
        )

        run_snapshot = self.artifact_store.save(
            "run_artifact",
            self._artifact_ref(
                run_artifact, "artifact_id", "run_id", "task_id", fallback_prefix="run-artifact"
            ),
            self._payload_for(run_artifact, execution_context=execution_context),
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
            self._payload_for(validation_outcome, execution_context=execution_context),
            graph_version=graph_version,
            candidate_id=resolved_candidate_id,
            parent_snapshot_id=run_snapshot.snapshot_id,
        )
        evidence_snapshot = self.artifact_store.save(
            "evidence_bundle",
            self._evidence_ref(evidence_bundle),
            self._payload_for(evidence_bundle, execution_context=execution_context),
            graph_version=graph_version,
            candidate_id=resolved_candidate_id,
            parent_snapshot_id=validation_snapshot.snapshot_id,
        )
        resolved_instantiation = self._instantiation_record(
            instantiation_record,
            execution_mode=normalized_mode,
            native_execution_mode=native_mode,
            candidate_id=resolved_candidate_id,
            graph_version=graph_version,
            run_snapshot=run_snapshot,
            validation_snapshot=validation_snapshot,
            evidence_snapshot=evidence_snapshot,
            external_evidence_refs=external_refs,
            extension_family=extension_family,
        )
        instantiation_snapshot = self._save_instantiation_record(
            resolved_instantiation,
            parent_snapshot_id=evidence_snapshot.snapshot_id,
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
                    **execution_context,
                },
            )
        ]
        if instantiation_snapshot is not None and resolved_instantiation is not None:
            session_events.append(
                self._append_event(
                    session_id,
                    SessionEventType.INSTANTIATION_RECORDED,
                    candidate_id=resolved_candidate_id,
                    graph_version=graph_version,
                    payload={
                        "instantiation_record_id": resolved_instantiation.record_id,
                        "instantiation_snapshot_id": instantiation_snapshot.snapshot_id,
                        "execution_mode": resolved_instantiation.execution_mode.value,
                        "native_execution_mode": resolved_instantiation.native_execution_mode,
                        "reconciliation_status": resolved_instantiation.reconciliation_status,
                        "external_evidence_refs": resolved_instantiation.external_evidence_refs,
                    },
                )
            )
        if execution_context or instantiation_snapshot is not None:
            session_events.append(
                self._append_event(
                    session_id,
                    SessionEventType.EXECUTION_RECONCILED,
                    candidate_id=resolved_candidate_id,
                    graph_version=graph_version,
                    payload={
                        "run_artifact_ref": run_snapshot.artifact_ref,
                        "validation_snapshot_id": validation_snapshot.snapshot_id,
                        "evidence_snapshot_id": evidence_snapshot.snapshot_id,
                        "instantiation_snapshot_id": instantiation_snapshot.snapshot_id
                        if instantiation_snapshot is not None
                        else None,
                        **execution_context,
                    },
                )
            )

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
            instantiation_snapshot=instantiation_snapshot,
            session_events=session_events,
        )
        audit_refs = self._record_audit(
            run_snapshot=run_snapshot,
            validation_snapshot=validation_snapshot,
            evidence_snapshot=evidence_snapshot,
            instantiation_snapshot=instantiation_snapshot,
            session_events=session_events,
        )

        return ExecutionEvidenceRecord(
            session_events=session_events,
            run_snapshot=run_snapshot,
            validation_snapshot=validation_snapshot,
            evidence_snapshot=evidence_snapshot,
            audit_refs=audit_refs,
            provenance_refs=provenance_refs,
            instantiation_snapshot=instantiation_snapshot,
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
        instantiation_snapshot: ArtifactSnapshot | None,
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
        if instantiation_snapshot is not None:
            instantiation_ref = self.provenance_graph.add_entity(
                id=f"artifact-snapshot:{instantiation_snapshot.snapshot_id}",
                kind="artifact_snapshot",
                artifact_kind=instantiation_snapshot.artifact_kind,
                artifact_ref=instantiation_snapshot.artifact_ref,
                graph_version=instantiation_snapshot.graph_version,
                candidate_id=instantiation_snapshot.candidate_id,
            ).id
            self.provenance_graph.relate(instantiation_ref, RelationKind.WAS_DERIVED_FROM, refs[2])
            refs.append(instantiation_ref)
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
        instantiation_snapshot: ArtifactSnapshot | None,
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
                "instantiation_snapshot_id": instantiation_snapshot.snapshot_id
                if instantiation_snapshot is not None
                else None,
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

    def _native_execution_mode(self, explicit: object | None, *values: object) -> str | None:
        if explicit is not None:
            return str(explicit)
        for value in values:
            for attribute_name in ("native_execution_mode", "execution_mode", "mode"):
                raw = getattr(value, attribute_name, None)
                if raw is not None:
                    return str(raw)
        return None

    def _execution_context(
        self,
        execution_mode: ExecutionMode,
        native_execution_mode: str | None,
        external_evidence_refs: list[str],
        extension_family: str | None,
    ) -> dict[str, object]:
        if (
            execution_mode == ExecutionMode.UNKNOWN
            and native_execution_mode is None
            and not external_evidence_refs
            and extension_family is None
        ):
            return {}
        return {
            "execution_mode": execution_mode.value,
            "native_execution_mode": native_execution_mode,
            "external_evidence_refs": list(external_evidence_refs),
            "extension_family": extension_family,
        }

    def _instantiation_record(
        self,
        instantiation_record: InstantiationRecord | dict[str, Any] | None,
        *,
        execution_mode: ExecutionMode,
        native_execution_mode: str | None,
        candidate_id: str | None,
        graph_version: int | None,
        run_snapshot: ArtifactSnapshot,
        validation_snapshot: ArtifactSnapshot,
        evidence_snapshot: ArtifactSnapshot,
        external_evidence_refs: list[str],
        extension_family: str | None,
    ) -> InstantiationRecord | None:
        if isinstance(instantiation_record, InstantiationRecord):
            record = instantiation_record
        elif isinstance(instantiation_record, dict):
            record = InstantiationRecord.model_validate(instantiation_record)
        elif (
            execution_mode == ExecutionMode.UNKNOWN
            and native_execution_mode is None
            and not external_evidence_refs
            and extension_family is None
        ):
            return None
        else:
            record = InstantiationRecord(
                execution_mode=execution_mode,
                native_execution_mode=native_execution_mode,
                candidate_id=candidate_id,
                graph_version=graph_version,
                attributes={"extension_family": extension_family} if extension_family else {},
            )
        evidence_refs = list(
            dict.fromkeys(
                [
                    *record.evidence_refs,
                    f"artifact-snapshot:{run_snapshot.snapshot_id}",
                    f"artifact-snapshot:{validation_snapshot.snapshot_id}",
                    f"artifact-snapshot:{evidence_snapshot.snapshot_id}",
                    *external_evidence_refs,
                ]
            )
        )
        reconciliation_status = self._reconciliation_status(
            execution_mode, external_evidence_refs, record.reconciliation_status
        )
        return record.model_copy(
            update={
                "execution_mode": execution_mode,
                "native_execution_mode": native_execution_mode or record.native_execution_mode,
                "candidate_id": candidate_id or record.candidate_id,
                "graph_version": graph_version
                if graph_version is not None
                else record.graph_version,
                "action_ref": record.action_ref or run_snapshot.artifact_ref,
                "run_artifact_ref": record.run_artifact_ref or run_snapshot.artifact_ref,
                "validation_ref": record.validation_ref or validation_snapshot.artifact_ref,
                "evidence_refs": evidence_refs,
                "external_evidence_refs": list(
                    dict.fromkeys([*record.external_evidence_refs, *external_evidence_refs])
                ),
                "reconciliation_status": reconciliation_status,
            }
        )

    def _save_instantiation_record(
        self,
        instantiation_record: InstantiationRecord | None,
        *,
        parent_snapshot_id: str,
    ) -> ArtifactSnapshot | None:
        if instantiation_record is None:
            return None
        return self.artifact_store.save(
            "instantiation_record",
            f"instantiation-record:{instantiation_record.record_id}",
            instantiation_record.model_dump(mode="json"),
            graph_version=instantiation_record.graph_version,
            candidate_id=instantiation_record.candidate_id,
            parent_snapshot_id=parent_snapshot_id,
        )

    def _reconciliation_status(
        self,
        execution_mode: ExecutionMode,
        external_evidence_refs: list[str],
        fallback: str,
    ) -> str:
        if external_evidence_refs:
            return "external_evidence_attached"
        if execution_mode == ExecutionMode.EXTERNAL_VERIFIED:
            return "external_verification_claimed"
        if execution_mode == ExecutionMode.INSTANTIATED:
            return "instantiation_claim_recorded"
        if execution_mode == ExecutionMode.UNKNOWN:
            return fallback
        return "simulation_boundary_recorded"

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

    def _payload_for(
        self, value: object, *, execution_context: dict[str, object] | None = None
    ) -> dict[str, Any]:
        if hasattr(value, "model_dump"):
            dumped = value.model_dump(mode="json")
            if isinstance(dumped, dict):
                payload = dumped
            else:
                payload = {"value": repr(value)}
        elif isinstance(value, dict):
            payload = dict(value)
        else:
            raw_dict = getattr(value, "__dict__", None)
            if isinstance(raw_dict, dict):
                payload = dict(raw_dict)
            else:
                payload = {"value": repr(value)}
        if execution_context:
            payload.setdefault("execution_reconciliation", dict(execution_context))
        return payload

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
