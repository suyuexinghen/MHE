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
from metaharness_ext.deepmd.contracts import (
    DeepMDEvidenceBundle,
    DeepMDPolicyReport,
    DeepMDValidationReport,
)


class DeepMDGovernanceAdapter:
    def __init__(
        self,
        *,
        session_id: str | None = None,
        actor: str = "deepmd_governance_adapter",
    ) -> None:
        self.session_id = session_id
        self.actor = actor

    def build_core_validation_report(
        self,
        validation: DeepMDValidationReport,
        policy: DeepMDPolicyReport,
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
        bundle: DeepMDEvidenceBundle,
        policy: DeepMDPolicyReport,
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
        bundle: DeepMDEvidenceBundle,
        policy: DeepMDPolicyReport,
    ) -> list[SessionEvent]:
        validation = self._require_validation(bundle)
        session_id = self.session_id or validation.task_id
        candidate_id = self._resolve_candidate_id(
            bundle,
            validation,
            GraphSnapshot(graph_version=self._resolve_graph_version(bundle, validation)),
        )
        return [
            make_session_event(
                session_id,
                SessionEventType.CANDIDATE_VALIDATED,
                graph_version=self._resolve_graph_version(bundle, validation) or None,
                candidate_id=candidate_id,
                payload={
                    "valid": validation.passed,
                    "issues": [issue.model_dump(mode="json") for issue in validation.issues],
                },
            ),
            make_session_event(
                session_id,
                SessionEventType.SAFETY_GATE_EVALUATED,
                graph_version=self._resolve_graph_version(bundle, validation) or None,
                candidate_id=candidate_id,
                payload={
                    "decision": policy.decision,
                    "reason": policy.reason,
                    "gate_count": len(policy.gates),
                    "execution_mode": bundle.execution_mode,
                    "application_family": bundle.application_family,
                },
            ),
        ]

    def emit_runtime_evidence(
        self,
        bundle: DeepMDEvidenceBundle,
        policy: DeepMDPolicyReport,
        *,
        session_store: SessionStore,
        audit_log: AuditLog,
        provenance_graph: ProvGraph,
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
                    *bundle.provenance_refs,
                    *validation.evidence_refs,
                    f"provenance://deepmd/validation/{validation.task_id}",
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
            "deepmd.governance_handoff",
            actor=self.actor,
            payload={
                "task_id": validation.task_id,
                "run_id": validation.run_id,
                "candidate_id": candidate_id,
                "graph_version": graph_version,
                "policy_decision": policy.decision,
                "execution_mode": bundle.execution_mode,
                "application_family": bundle.application_family,
            },
        )
        audit_refs.append(f"audit-record:{handoff_record.record_id}")
        return {
            "audit_refs": list(dict.fromkeys(audit_refs)),
            "provenance_refs": list(dict.fromkeys(provenance_refs)),
        }

    def _policy_gate_issues(
        self,
        validation: DeepMDValidationReport,
        policy: DeepMDPolicyReport,
    ) -> list[ValidationIssue]:
        return [
            ValidationIssue(
                code=f"deepmd_gate_{gate.gate}",
                message=gate.reason,
                subject=validation.task_id,
                category=ValidationIssueCategory.PROMOTION_BLOCKER,
                blocks_promotion=True,
            )
            for gate in policy.gates
            if gate.decision.value != "allow"
        ]

    def _resolve_graph_version(
        self,
        bundle: DeepMDEvidenceBundle,
        validation: DeepMDValidationReport,
    ) -> int:
        metadata = bundle.metadata
        raw_graph_version = (
            metadata.get("graph_version")
            or metadata.get("graph_version_id")
            or validation.summary_metrics.get("graph_version")
            or validation.summary_metrics.get("graph_version_id")
            or 0
        )
        try:
            return int(raw_graph_version)
        except (TypeError, ValueError):
            return 0

    def _resolve_candidate_id(
        self,
        bundle: DeepMDEvidenceBundle,
        validation: DeepMDValidationReport,
        snapshot: GraphSnapshot,
    ) -> str:
        metadata = bundle.metadata
        raw_candidate_id = (
            metadata.get("candidate_id")
            or validation.summary_metrics.get("candidate_id")
            or snapshot.graph_version
            and f"deepmd-candidate-v{snapshot.graph_version}"
            or bundle.run_id
        )
        return str(raw_candidate_id)

    def _require_validation(self, bundle: DeepMDEvidenceBundle) -> DeepMDValidationReport:
        if bundle.validation is None:
            raise ValueError("DeepMD evidence bundle requires an attached validation report")
        return bundle.validation
