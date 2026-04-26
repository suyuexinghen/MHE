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
from metaharness.provenance import ArtifactSnapshotStore, AuditLog, ProvGraph, RelationKind
from metaharness_ext.qcompute.contracts import (
    QComputeEvidenceBundle,
    QComputePolicyReport,
    QComputeValidationReport,
)


class QComputeGovernanceAdapter:
    def __init__(
        self,
        *,
        session_id: str | None = None,
        actor: str = "qcompute_governance_adapter",
    ) -> None:
        self.session_id = session_id
        self.actor = actor

    def build_core_validation_report(
        self,
        validation: QComputeValidationReport,
        policy: QComputePolicyReport,
    ) -> ValidationReport:
        issues = list(validation.issues)
        issues.extend(self._policy_gate_issues(validation, policy))
        valid = (
            validation.passed
            and validation.promotion_ready
            and policy.passed
            and policy.decision == "allow"
            and not any(issue.blocks_promotion for issue in issues)
        )
        return ValidationReport(valid=valid, issues=issues)

    def build_candidate_record(
        self,
        bundle: QComputeEvidenceBundle,
        policy: QComputePolicyReport,
        *,
        snapshot: GraphSnapshot | None = None,
    ) -> CandidateRecord:
        validation = bundle.validation_report
        report = self.build_core_validation_report(validation, policy)
        candidate_snapshot = snapshot or GraphSnapshot(
            graph_version=self._resolve_graph_version(bundle)
        )
        return CandidateRecord(
            candidate_id=self._resolve_candidate_id(bundle, candidate_snapshot),
            snapshot=candidate_snapshot,
            report=report,
            promoted=report.valid,
        )

    def build_session_events(
        self,
        bundle: QComputeEvidenceBundle,
        policy: QComputePolicyReport,
    ) -> list[SessionEvent]:
        validation = bundle.validation_report
        session_id = self.session_id or validation.task_id
        graph_version = self._resolve_graph_version(bundle)
        candidate_id = self._resolve_candidate_id(
            bundle, GraphSnapshot(graph_version=graph_version)
        )
        events = [
            make_session_event(
                session_id,
                SessionEventType.CANDIDATE_VALIDATED,
                graph_version=graph_version or None,
                candidate_id=candidate_id,
                payload={
                    "valid": validation.passed,
                    "promotion_ready": validation.promotion_ready,
                    "status": validation.status.value,
                    "issues": [issue.model_dump(mode="json") for issue in validation.issues],
                },
            ),
            make_session_event(
                session_id,
                SessionEventType.SAFETY_GATE_EVALUATED,
                graph_version=graph_version or None,
                candidate_id=candidate_id,
                payload={
                    "decision": policy.decision,
                    "reason": policy.reason,
                    "gate_count": len(policy.gates),
                    "backend": bundle.run_artifact.backend_actual,
                    "fidelity": validation.metrics.fidelity,
                },
            ),
        ]
        if policy.decision == "reject":
            events.append(
                make_session_event(
                    session_id,
                    SessionEventType.CANDIDATE_REJECTED,
                    graph_version=graph_version or None,
                    candidate_id=candidate_id,
                    payload={"decision": policy.decision, "reason": policy.reason},
                )
            )
        return events

    def emit_runtime_evidence(
        self,
        bundle: QComputeEvidenceBundle,
        policy: QComputePolicyReport,
        *,
        session_store: SessionStore,
        audit_log: AuditLog,
        provenance_graph: ProvGraph,
    ) -> dict[str, list[str]]:
        validation = bundle.validation_report
        graph_version = self._resolve_graph_version(bundle) or None
        candidate_id = self._resolve_candidate_id(
            bundle, GraphSnapshot(graph_version=graph_version or 0)
        )
        audit_refs: list[str] = []
        provenance_refs = list(
            dict.fromkeys(
                [
                    *bundle.provenance_refs,
                    *validation.provenance_refs,
                    *validation.evidence_refs,
                    f"provenance://qcompute/validation/{validation.task_id}",
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

        if bundle.run_artifact.raw_output_path is not None:
            raw_entity = provenance_graph.add_entity(
                id=f"qcompute-raw-output:{bundle.run_artifact.artifact_id}",
                kind="qcompute_raw_output",
                path=bundle.run_artifact.raw_output_path,
            )
            provenance_graph.relate(
                candidate_entity.id, RelationKind.WAS_DERIVED_FROM, raw_entity.id
            )
            provenance_refs.append(raw_entity.id)

        for event in self.build_session_events(bundle, policy):
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
                event_entity.id, RelationKind.WAS_DERIVED_FROM, candidate_entity.id
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
            "qcompute.governance_handoff",
            actor=self.actor,
            payload={
                "task_id": validation.task_id,
                "artifact_id": validation.artifact_ref,
                "candidate_id": candidate_id,
                "graph_version": graph_version,
                "policy_decision": policy.decision,
                "validation_status": validation.status.value,
            },
        )
        audit_refs.append(f"audit-record:{handoff_record.record_id}")
        return {
            "audit_refs": list(dict.fromkeys(audit_refs)),
            "provenance_refs": list(dict.fromkeys(provenance_refs)),
        }

    def record_with_artifact_store(
        self,
        bundle: QComputeEvidenceBundle,
        policy: QComputePolicyReport,
        *,
        session_store: SessionStore,
        audit_log: AuditLog,
        provenance_graph: ProvGraph,
        artifact_store: ArtifactSnapshotStore | None = None,
    ) -> dict[str, list[str]]:
        """Emit runtime evidence AND optionally persist artifact snapshots via core recorder."""
        # Step 1: Always emit via existing method
        refs = self.emit_runtime_evidence(
            bundle,
            policy,
            session_store=session_store,
            audit_log=audit_log,
            provenance_graph=provenance_graph,
        )

        # Step 2: If artifact_store provided, also record via core ExecutionEvidenceRecorder
        if artifact_store is not None:
            from metaharness.core.execution import ExecutionEvidenceRecorder

            validation = bundle.validation_report
            candidate_id = self._resolve_candidate_id(
                bundle, GraphSnapshot(graph_version=self._resolve_graph_version(bundle))
            )
            graph_version = self._resolve_graph_version(bundle)

            recorder = ExecutionEvidenceRecorder(
                session_store=session_store,
                artifact_store=artifact_store,
                provenance_graph=provenance_graph,
                audit_log=audit_log,
                actor=f"{self.actor}_recorder",
            )
            record = recorder.record(
                session_id=self.session_id or validation.task_id,
                run_artifact=bundle.run_artifact,
                validation_outcome=validation,
                evidence_bundle=bundle,
                candidate_id=candidate_id,
                graph_version=graph_version,
                policy_decision=policy.decision,
                safety_payload={
                    "reason": policy.reason,
                    "gate_count": len(policy.gates),
                    "backend": bundle.run_artifact.backend_actual,
                    "fidelity": validation.metrics.fidelity,
                },
            )
            # Merge recorder's refs with emit refs
            refs["audit_refs"] = list(
                dict.fromkeys(
                    [
                        *refs.get("audit_refs", []),
                        *record.audit_refs,
                    ]
                )
            )
            refs["provenance_refs"] = list(
                dict.fromkeys(
                    [
                        *refs.get("provenance_refs", []),
                        *record.provenance_refs,
                    ]
                )
            )

        return refs

    def _policy_gate_issues(
        self,
        validation: QComputeValidationReport,
        policy: QComputePolicyReport,
    ) -> list[ValidationIssue]:
        return [
            ValidationIssue(
                code=f"qcompute_gate_{gate.gate}",
                message=gate.reason,
                subject=validation.task_id,
                category=ValidationIssueCategory.PROMOTION_BLOCKER,
                blocks_promotion=gate.decision.value != "allow",
            )
            for gate in policy.gates
            if gate.decision.value != "allow"
        ]

    def _resolve_graph_version(self, bundle: QComputeEvidenceBundle) -> int:
        identity = bundle.run_artifact.candidate_identity
        raw_graph_version = (
            identity.proposed_graph_version
            or identity.graph_version_id
            or bundle.metadata.get("proposed_graph_version")
            or bundle.metadata.get("graph_version_id")
            or 0
        )
        try:
            return int(raw_graph_version)
        except (TypeError, ValueError):
            return 0

    def _resolve_candidate_id(self, bundle: QComputeEvidenceBundle, snapshot: GraphSnapshot) -> str:
        identity = bundle.run_artifact.candidate_identity
        raw_candidate_id = (
            identity.candidate_id
            or bundle.metadata.get("candidate_id")
            or (snapshot.graph_version and f"qcompute-candidate-v{snapshot.graph_version}")
            or bundle.run_artifact.artifact_id
        )
        return str(raw_candidate_id)
