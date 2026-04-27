"""HarnessRuntime boot orchestrator.

Wires discovery -> static validation -> dependency resolution ->
registration -> graph staging into a single entry point.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from metaharness.core.connection_engine import ConnectionEngine
from metaharness.core.event_bus import (
    AFTER_COMMIT_GRAPH,
    BEFORE_COMMIT_GRAPH,
    CANDIDATE_DEFERRED,
    CANDIDATE_REJECTED,
    EventBus,
)
from metaharness.core.graph_versions import (
    CandidateRecord,
    ExternalCandidateReview,
    ExternalCandidateReviewState,
    GraphVersionManager,
    GraphVersionStore,
)
from metaharness.core.lifecycle_tracker import LifecycleTracker
from metaharness.core.models import (
    PendingConnectionSet,
    PromotionContext,
    SessionEvent,
    SessionEventType,
)
from metaharness.core.mutation import MutationSubmitter
from metaharness.core.port_index import PortIndex, RouteTable
from metaharness.hotreload.migration import MigrationAdapterRegistry
from metaharness.identity import InMemoryIdentityBoundary
from metaharness.observability.events import InMemorySessionStore, SessionStore, make_session_event
from metaharness.provenance import ArtifactSnapshotStore, AuditLog, ProvGraph, RelationKind
from metaharness.safety import SafetyPipeline, parse_sandbox_tier
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.dependency import resolve_boot_order
from metaharness.sdk.discovery import ComponentDiscovery, DiscoveryResult
from metaharness.sdk.lifecycle import ComponentPhase
from metaharness.sdk.loader import declare_component, validate_manifest_static
from metaharness.sdk.manifest import ComponentManifest
from metaharness.sdk.registry import ComponentRegistry, filter_enabled
from metaharness.sdk.runtime import ComponentRuntime, RuntimeServices


@dataclass(slots=True)
class BootReport:
    """Summary of a single boot run."""

    discovery: DiscoveryResult
    booted_ids: list[str]
    skipped_ids: list[str] = field(default_factory=list)
    overridden_ids: list[str] = field(default_factory=list)
    validation_issues: dict[str, list[str]] = field(default_factory=dict)
    active_graph_version: int | None = None


@dataclass(slots=True)
class RecoveredSession:
    """Durable context reconstructed for a harness session."""

    session_id: str
    events: list[SessionEvent]
    checkpoint_index: int | None = None
    latest_event: SessionEvent | None = None
    active_graph_version: int | None = None
    rollback_graph_version: int | None = None
    candidate_ids: list[str] = field(default_factory=list)


class HarnessRuntime:
    """Top-level orchestrator that turns discovery results into a running graph.

    The runtime itself remains deliberately thin: it composes discovery,
    loader, dependency resolver, registry, connection engine, graph version
    manager, and the mutation submitter. Components wired by :meth:`boot`
    are ready to participate in candidate graph staging immediately.
    """

    def __init__(
        self,
        discovery: ComponentDiscovery,
        *,
        registry: ComponentRegistry | None = None,
        version_store: GraphVersionStore | None = None,
        event_bus: EventBus | None = None,
        runtime_factory: Callable[[ComponentManifest], ComponentRuntime] | None = None,
        enabled_overrides: dict[str, dict[str, object]] | None = None,
        instance_suffix: str = ".primary",
        session_id: str = "runtime-session",
        session_store: SessionStore | None = None,
        trace_collector: Any | None = None,
        audit_log: AuditLog | None = None,
        provenance_graph: ProvGraph | None = None,
        artifact_store: ArtifactSnapshotStore | None = None,
        resource_quota: Any | None = None,
    ) -> None:
        self.discovery = discovery
        self.registry = registry or ComponentRegistry()
        self.version_manager = GraphVersionManager(version_store or GraphVersionStore())
        self.engine = ConnectionEngine(self.registry, self.version_manager.store)
        self.event_bus = event_bus or EventBus()
        self.lifecycle = LifecycleTracker()
        self.submitter = MutationSubmitter(engine=self.engine)
        self.safety_pipeline = SafetyPipeline()
        self.migration_adapters = MigrationAdapterRegistry()
        self.components: dict[str, HarnessComponent] = {}
        self._default_identity_boundary = InMemoryIdentityBoundary()
        self._runtime_factory = runtime_factory
        self._enabled_overrides = enabled_overrides or {}
        self._instance_suffix = instance_suffix
        self.session_id = session_id
        self.session_store = session_store or InMemorySessionStore()
        self.trace_collector = trace_collector
        self.audit_log = audit_log or AuditLog()
        self.provenance_graph = provenance_graph or ProvGraph()
        self.artifact_store = artifact_store or ArtifactSnapshotStore()
        self.resource_quota = resource_quota
        self.recovered_session = self._recover_session(session_id)

    @classmethod
    def wake(
        cls,
        session_id: str,
        discovery: ComponentDiscovery,
        *,
        registry: ComponentRegistry | None = None,
        version_store: GraphVersionStore | None = None,
        event_bus: EventBus | None = None,
        runtime_factory: Callable[[ComponentManifest], ComponentRuntime] | None = None,
        enabled_overrides: dict[str, dict[str, object]] | None = None,
        instance_suffix: str = ".primary",
        session_store: SessionStore | None = None,
        trace_collector: Any | None = None,
        audit_log: AuditLog | None = None,
        provenance_graph: ProvGraph | None = None,
        artifact_store: ArtifactSnapshotStore | None = None,
        resource_quota: Any | None = None,
    ) -> "HarnessRuntime":
        return cls(
            discovery,
            registry=registry,
            version_store=version_store,
            event_bus=event_bus,
            runtime_factory=runtime_factory,
            enabled_overrides=enabled_overrides,
            instance_suffix=instance_suffix,
            session_id=session_id,
            session_store=session_store,
            trace_collector=trace_collector,
            audit_log=audit_log,
            provenance_graph=provenance_graph,
            artifact_store=artifact_store,
            resource_quota=resource_quota,
        )

    def _recover_session(self, session_id: str) -> RecoveredSession:
        events = self.session_store.get_events(session_id)
        latest_event = events[-1] if events else None
        committed_events = [
            event for event in events if event.event_type == SessionEventType.GRAPH_COMMITTED
        ]
        active_graph_version = (
            committed_events[-1].payload.get("committed_graph_version")
            if committed_events
            else None
        )
        rollback_graph_version = (
            committed_events[-1].payload.get("rollback_target") if committed_events else None
        )
        candidate_ids = list(
            dict.fromkeys(event.candidate_id for event in events if event.candidate_id is not None)
        )
        return RecoveredSession(
            session_id=session_id,
            events=events,
            checkpoint_index=self.session_store.latest_checkpoint_index(session_id),
            latest_event=latest_event,
            active_graph_version=(
                active_graph_version if isinstance(active_graph_version, int) else None
            ),
            rollback_graph_version=(
                rollback_graph_version if isinstance(rollback_graph_version, int) else None
            ),
            candidate_ids=candidate_ids,
        )

    def refresh_recovered_session(self) -> RecoveredSession:
        self.recovered_session = self._recover_session(self.session_id)
        return self.recovered_session

    def session_events(
        self,
        *,
        after_index: int | None = None,
        event_type: SessionEventType | None = None,
    ) -> list[SessionEvent]:
        return self.session_store.get_events(
            self.session_id,
            after_index=after_index,
            event_type=event_type,
        )

    def _instance_id(self, manifest: ComponentManifest) -> str:
        base = manifest.resolved_id()
        if not self._instance_suffix or base.endswith(self._instance_suffix):
            return base
        return f"{base}{self._instance_suffix}"

    def _serialize_validation_report(self, promotion: PromotionContext) -> dict[str, object]:
        return {
            "valid": promotion.validation_report.valid,
            "issues": [
                issue.model_dump(mode="json") for issue in promotion.validation_report.issues
            ],
        }

    def _serialize_safety_result(self, safety_result: Any) -> dict[str, object]:
        return {
            "allowed": safety_result.allowed,
            "rejected_by": safety_result.rejected_by,
            "rejected_reason": safety_result.rejected_reason,
            "results": [
                {
                    "gate": result.gate,
                    "decision": result.decision.value,
                    "reason": result.reason,
                    "evidence": dict(result.evidence),
                }
                for result in safety_result.results
            ],
        }

    def _append_runtime_evidence(
        self,
        event_type: SessionEventType,
        promotion: PromotionContext,
        *,
        graph_version: int | None = None,
        payload: dict[str, object] | None = None,
    ) -> None:
        event = make_session_event(
            self.session_id,
            event_type,
            graph_version=graph_version,
            candidate_id=promotion.candidate_id,
            payload=payload,
        )
        self.session_store.append(event)

        event_entity = self.provenance_graph.add_entity(
            id=f"session-event:{event.event_id}",
            kind="session_event",
            event_type=event.event_type.value,
            session_id=event.session_id,
            candidate_id=event.candidate_id,
            graph_version=event.graph_version,
            payload=event.payload,
            timestamp=event.timestamp.isoformat(),
        )
        candidate_entity = self.provenance_graph.add_entity(
            id=f"graph-candidate:{promotion.candidate_id}",
            kind="graph_candidate",
            candidate_id=promotion.candidate_id,
            proposed_graph_version=promotion.proposed_graph_version,
            rollback_target=promotion.rollback_target,
        )
        self.provenance_graph.relate(
            event_entity.id,
            RelationKind.WAS_DERIVED_FROM,
            candidate_entity.id,
        )
        if graph_version is not None:
            version_entity = self.provenance_graph.add_entity(
                id=f"graph-version:{graph_version}",
                kind="graph_version",
                graph_version=graph_version,
            )
            self.provenance_graph.relate(
                event_entity.id,
                RelationKind.WAS_DERIVED_FROM,
                version_entity.id,
            )

        self.audit_log.append(
            f"session.{event_type.value}",
            actor="harness_runtime",
            payload={
                "event_id": event.event_id,
                "session_id": event.session_id,
                "candidate_id": event.candidate_id,
                "graph_version": event.graph_version,
                "payload": event.payload,
            },
        )

    # ------------------------------------------------------------------ boot

    def boot(self) -> BootReport:
        """Run the full discovery -> registration pipeline.

        Returns a :class:`BootReport` summarising what happened. Does not
        commit a graph - callers use :meth:`commit_graph` afterwards to
        stage and commit a specific topology.
        """

        resolution = self.discovery.resolve()
        winners = [found.manifest for found in resolution.winners]
        overridden_ids = [found.identity for found in resolution.overridden]
        enabled = filter_enabled(winners, config=self._enabled_overrides)
        skipped_ids = [m.resolved_id() for m in winners if m not in enabled]

        validation_issues: dict[str, list[str]] = {}
        valid_manifests: list[ComponentManifest] = []
        for manifest in enabled:
            issues = validate_manifest_static(manifest)
            if issues:
                validation_issues[manifest.resolved_id()] = issues
                continue
            valid_manifests.append(manifest)

        ordered = resolve_boot_order(valid_manifests)

        booted_ids: list[str] = []
        for manifest in ordered:
            component_id = self._instance_id(manifest)
            runtime = (
                self._runtime_factory(manifest)
                if self._runtime_factory
                else ComponentRuntime(
                    event_bus=self.event_bus,
                    identity_boundary=self._default_identity_boundary,
                )
            )
            services = RuntimeServices(
                event_bus=runtime.event_bus or self.event_bus,
                session_store=runtime.session_store or self.session_store,
                artifact_store=runtime.artifact_store or self.artifact_store,
                audit_log=runtime.audit_log or self.audit_log,
                provenance_graph=runtime.provenance_graph or self.provenance_graph,
                identity_boundary=runtime.identity_boundary or self._default_identity_boundary,
                trace_store=runtime.trace_store or self.trace_collector,
                metrics=runtime.metrics,
                graph_reader=runtime.graph_reader,
                mutation_submitter=runtime.mutation_submitter or self.submitter,
                resource_quota=runtime.resource_quota or self.resource_quota,
            )
            runtime.services = services
            if runtime.event_bus is None:
                runtime.event_bus = services.event_bus
            if runtime.session_store is None:
                runtime.session_store = services.session_store
            if runtime.artifact_store is None:
                runtime.artifact_store = services.artifact_store
            if runtime.audit_log is None:
                runtime.audit_log = services.audit_log
            if runtime.provenance_graph is None:
                runtime.provenance_graph = services.provenance_graph
            if runtime.identity_boundary is None:
                runtime.identity_boundary = services.identity_boundary
            if runtime.trace_store is None:
                runtime.trace_store = services.trace_store
            if runtime.mutation_submitter is None:
                runtime.mutation_submitter = services.mutation_submitter
            if runtime.resource_quota is None:
                runtime.resource_quota = services.resource_quota
            if runtime.migration_adapters is None:
                runtime.migration_adapters = self.migration_adapters
            component, api = declare_component(component_id, manifest, runtime=runtime)
            declarations = api._commit()
            self.registry.register(component_id, manifest, declarations)
            self.migration_adapters.register_declarations(
                component_id=component_id,
                declarations=declarations,
            )
            asyncio.run(component.activate(runtime))
            self.components[component_id] = component
            for record in declarations.connection_handlers:
                handler = record.handler
                if callable(handler):
                    self.engine.register_handler(record.target, handler)
            self.lifecycle.record(component_id, ComponentPhase.DISCOVERED)
            self.lifecycle.record(component_id, ComponentPhase.VALIDATED_STATIC)
            self.lifecycle.record(component_id, ComponentPhase.ASSEMBLED)
            booted_ids.append(component_id)

        return BootReport(
            discovery=resolution,
            booted_ids=booted_ids,
            skipped_ids=skipped_ids,
            overridden_ids=overridden_ids,
            validation_issues=validation_issues,
            active_graph_version=self.version_manager.active_version,
        )

    def _enforce_promotion_policies(self, pending: PendingConnectionSet) -> None:
        """Enforce declared manifest policies at graph promotion boundaries."""

        default_runtime = None
        if self.components:
            first_component = next(iter(self.components.values()))
            default_runtime = getattr(first_component, "_runtime", None)
        for node in pending.nodes:
            registered = self.registry.components.get(node.component_id)
            if registered is None:
                continue
            manifest = registered.manifest
            policy = manifest.policy
            if policy.credentials.requires_subject and not manifest.safety.protected:
                raise ValueError(
                    f"Candidate graph '{manifest.resolved_id()}' requires identity-bound credentials "
                    "but is not protected"
                )
            declared_tier = policy.sandbox.tier
            if declared_tier is None or default_runtime is None:
                continue
            tier = parse_sandbox_tier(declared_tier)
            default_runtime.require_sandbox_tier(tier)

    def _policy_reviewer(self) -> Callable[[PromotionContext], Any] | None:
        policy_component = self.components.get("policy.primary")
        if policy_component is None:
            return None
        if hasattr(policy_component, "evaluate_promotion"):
            return policy_component.evaluate_promotion
        if hasattr(policy_component, "review_graph_promotion"):
            return policy_component.review_graph_promotion
        return None

    def deferred_candidates(self) -> list[CandidateRecord]:
        """Return candidates still awaiting deferred review."""

        return self.version_manager.deferred_candidates

    def defer_candidate(self, candidate: CandidateRecord) -> CandidateRecord:
        """Persist a candidate as awaiting deferred review."""

        deferred_candidate = candidate.model_copy(update={"promoted": False, "deferred": True})
        self.version_manager.save_candidate(deferred_candidate)
        return deferred_candidate

    def review_external_candidate(self, candidate: CandidateRecord) -> CandidateRecord:
        """Attach runtime review state to an externally-produced candidate."""

        if candidate.external_review is not None:
            return candidate
        blocking_issues = [issue for issue in candidate.report.issues if issue.blocks_promotion]
        reason = (
            "; ".join(f"{issue.code}:{issue.subject}" for issue in blocking_issues)
            if blocking_issues
            else (None if candidate.promoted else "candidate_not_promoted")
        )
        return candidate.model_copy(
            update={
                "external_review": ExternalCandidateReview(
                    state=(
                        ExternalCandidateReviewState.ADOPTED
                        if candidate.promoted
                        else ExternalCandidateReviewState.REJECTED
                    ),
                    reason=reason,
                )
            }
        )

    def ingest_candidate_record(
        self,
        candidate: CandidateRecord,
        *,
        emit_runtime_evidence: bool = True,
    ) -> CandidateRecord:
        """Record an externally-produced candidate in runtime promotion stores."""

        reviewed_candidate = self.review_external_candidate(candidate)
        graph_version = reviewed_candidate.snapshot.graph_version
        promotion = PromotionContext(
            candidate_id=reviewed_candidate.candidate_id,
            candidate_snapshot=reviewed_candidate.snapshot,
            validation_report=reviewed_candidate.report,
            proposed_graph_version=graph_version,
            rollback_target=self.version_manager.active_version,
        )
        effective_graph_version = graph_version if graph_version > 0 else None
        review = reviewed_candidate.external_review
        source = review.source if review is not None else "external_candidate_record"
        if emit_runtime_evidence:
            self._append_runtime_evidence(
                SessionEventType.CANDIDATE_CREATED,
                promotion,
                graph_version=effective_graph_version,
                payload={
                    "node_ids": [node.component_id for node in reviewed_candidate.snapshot.nodes],
                    "edge_ids": [edge.connection_id for edge in reviewed_candidate.snapshot.edges],
                    "rollback_target": self.version_manager.active_version,
                    "source": source,
                },
            )
            self._append_runtime_evidence(
                SessionEventType.CANDIDATE_VALIDATED,
                promotion,
                graph_version=effective_graph_version,
                payload=self._serialize_validation_report(promotion),
            )
            self._append_runtime_evidence(
                SessionEventType.SAFETY_GATE_EVALUATED,
                promotion,
                graph_version=effective_graph_version,
                payload={
                    "allowed": reviewed_candidate.promoted,
                    "rejected_by": None if reviewed_candidate.promoted else review.reviewer,
                    "rejected_reason": None if reviewed_candidate.promoted else review.reason,
                    "results": [],
                },
            )
        self.version_manager.save_candidate(reviewed_candidate)
        if not reviewed_candidate.promoted:
            blocking_issues = [
                issue for issue in reviewed_candidate.report.issues if issue.blocks_promotion
            ]
            self._append_runtime_evidence(
                SessionEventType.CANDIDATE_REJECTED,
                promotion,
                graph_version=effective_graph_version,
                payload={
                    "reason": review.reason,
                    "blocking_issues": [issue.model_dump(mode="json") for issue in blocking_issues],
                    "safety": {
                        "allowed": False,
                        "rejected_by": review.reviewer,
                        "rejected_reason": review.reason,
                        "results": [],
                    },
                },
            )
            self.event_bus.publish(CANDIDATE_REJECTED, promotion)
        return reviewed_candidate

    def review_deferred_candidate(self, candidate_id: str) -> CandidateRecord:
        """Re-run promotion safety review for a deferred candidate."""

        candidate = next(
            (
                stored
                for stored in reversed(self.version_manager.candidates)
                if stored.candidate_id == candidate_id and stored.deferred
            ),
            None,
        )
        if candidate is None:
            raise ValueError(f"Deferred candidate '{candidate_id}' is not available")
        promotion = PromotionContext(
            candidate_id=candidate.candidate_id,
            candidate_snapshot=candidate.snapshot,
            validation_report=candidate.report,
            proposed_graph_version=candidate.snapshot.graph_version,
            rollback_target=self.version_manager.active_version,
        )
        blocking_issues = [issue for issue in candidate.report.issues if issue.blocks_promotion]
        safety_result = self.safety_pipeline.evaluate_graph_promotion(
            promotion,
            reviewer=self._policy_reviewer(),
        )
        self._append_runtime_evidence(
            SessionEventType.SAFETY_GATE_EVALUATED,
            promotion,
            graph_version=candidate.snapshot.graph_version,
            payload=self._serialize_safety_result(safety_result),
        )
        if blocking_issues or not safety_result.allowed:
            deferred = not blocking_issues and any(
                result.decision.value == "defer" for result in safety_result.results
            )
            event_type = (
                SessionEventType.CANDIDATE_DEFERRED
                if deferred
                else SessionEventType.CANDIDATE_REJECTED
            )
            reason = (
                "; ".join(f"{issue.code}:{issue.subject}" for issue in blocking_issues)
                if blocking_issues
                else (
                    safety_result.rejected_reason
                    or ("safety_deferred" if deferred else "safety_rejected")
                )
            )
            reviewed_candidate = candidate.model_copy(
                update={"promoted": False, "deferred": deferred}
            )
            self.version_manager.update_candidate(reviewed_candidate)
            self._append_runtime_evidence(
                event_type,
                promotion,
                graph_version=candidate.snapshot.graph_version,
                payload={
                    "reason": reason,
                    "blocking_issues": [issue.model_dump(mode="json") for issue in blocking_issues],
                    "safety": self._serialize_safety_result(safety_result),
                },
            )
            self.event_bus.publish(
                CANDIDATE_DEFERRED if deferred else CANDIDATE_REJECTED, promotion
            )
            return reviewed_candidate

        self.version_manager.cutover(candidate.snapshot)
        self.engine.load_graph(candidate.snapshot)
        version = candidate.snapshot.graph_version
        self.registry.record_graph_version(version)
        commit_report = (
            candidate.report
            if candidate.report.valid
            else candidate.report.model_copy(update={"valid": True})
        )
        promotion = promotion.model_copy(update={"validation_report": commit_report})
        reviewed_candidate = candidate.model_copy(
            update={"report": commit_report, "promoted": True, "deferred": False}
        )
        self.version_manager.update_candidate(reviewed_candidate)
        self._append_runtime_evidence(
            SessionEventType.GRAPH_COMMITTED,
            promotion,
            graph_version=version,
            payload={
                "committed_graph_version": version,
                "rollback_target": promotion.rollback_target,
                "validation": self._serialize_validation_report(promotion),
                "safety": self._serialize_safety_result(safety_result),
            },
        )
        self.event_bus.publish(AFTER_COMMIT_GRAPH, promotion)
        return reviewed_candidate

    def commit_graph(
        self, pending: PendingConnectionSet, *, candidate_id: str = "boot-graph"
    ) -> int:
        """Stage, validate, and commit a graph using the booted registry."""

        self._enforce_promotion_policies(pending)
        candidate, report = self.engine.stage(pending)
        proposed_version = candidate.graph_version
        rollback_target = self.version_manager.active_version
        affected_protected_components = sorted(
            {
                issue.subject
                for issue in report.issues
                if issue.category.value == "protected_component"
            }
        )
        promotion = PromotionContext(
            candidate_id=candidate_id,
            candidate_snapshot=candidate,
            validation_report=report,
            proposed_graph_version=proposed_version,
            rollback_target=rollback_target,
            affected_protected_components=affected_protected_components,
        )

        self._append_runtime_evidence(
            SessionEventType.CANDIDATE_CREATED,
            promotion,
            graph_version=proposed_version,
            payload={
                "node_ids": [node.component_id for node in candidate.nodes],
                "edge_ids": [edge.connection_id for edge in candidate.edges],
                "rollback_target": rollback_target,
            },
        )
        self._append_runtime_evidence(
            SessionEventType.CANDIDATE_VALIDATED,
            promotion,
            graph_version=proposed_version,
            payload=self._serialize_validation_report(promotion),
        )

        blocking_issues = [issue for issue in report.issues if issue.blocks_promotion]
        safety_result = self.safety_pipeline.evaluate_graph_promotion(
            promotion,
            reviewer=self._policy_reviewer(),
        )
        self._append_runtime_evidence(
            SessionEventType.SAFETY_GATE_EVALUATED,
            promotion,
            graph_version=proposed_version,
            payload=self._serialize_safety_result(safety_result),
        )
        if blocking_issues or not safety_result.allowed:
            deferred = not blocking_issues and any(
                result.decision.value == "defer" for result in safety_result.results
            )
            self.engine.discard_candidate(candidate_id, candidate, report, deferred=deferred)
            event_type = (
                SessionEventType.CANDIDATE_DEFERRED
                if deferred
                else SessionEventType.CANDIDATE_REJECTED
            )
            for node in candidate.nodes:
                phase = self.lifecycle.phase(node.component_id)
                if phase != ComponentPhase.COMMITTED:
                    self.lifecycle.record(node.component_id, ComponentPhase.VALIDATED_DYNAMIC)
                if not deferred:
                    self.lifecycle.record(node.component_id, ComponentPhase.FAILED)
            rejection_reason = (
                "; ".join(f"{issue.code}:{issue.subject}" for issue in blocking_issues)
                if blocking_issues
                else (
                    safety_result.rejected_reason
                    or ("safety_deferred" if deferred else "safety_rejected")
                )
            )
            self._append_runtime_evidence(
                event_type,
                promotion,
                graph_version=proposed_version,
                payload={
                    "reason": rejection_reason,
                    "blocking_issues": [issue.model_dump(mode="json") for issue in blocking_issues],
                    "safety": self._serialize_safety_result(safety_result),
                },
            )
            self.event_bus.publish(
                CANDIDATE_DEFERRED if deferred else CANDIDATE_REJECTED,
                promotion,
            )
            if blocking_issues:
                reason = "; ".join(f"{issue.code}:{issue.subject}" for issue in blocking_issues)
            else:
                reason = safety_result.rejected_reason or (
                    "safety_deferred" if deferred else "safety_rejected"
                )
            outcome = "deferred" if deferred else "failed"
            raise ValueError(f"Candidate graph '{candidate_id}' {outcome} promotion gate: {reason}")

        self.event_bus.publish(BEFORE_COMMIT_GRAPH, promotion)

        commit_report = report if report.valid else report.model_copy(update={"valid": True})
        version = self.engine.commit(candidate_id, candidate, commit_report)
        self.registry.record_graph_version(version)
        for node in candidate.nodes:
            phase = self.lifecycle.phase(node.component_id)
            if phase == ComponentPhase.COMMITTED:
                continue
            self.lifecycle.record(node.component_id, ComponentPhase.VALIDATED_DYNAMIC)
            self.lifecycle.record(node.component_id, ComponentPhase.ACTIVATED)
            self.lifecycle.record(node.component_id, ComponentPhase.COMMITTED)
        self._append_runtime_evidence(
            SessionEventType.GRAPH_COMMITTED,
            promotion,
            graph_version=version,
            payload={
                "committed_graph_version": version,
                "rollback_target": rollback_target,
                "validation": self._serialize_validation_report(promotion),
                "safety": self._serialize_safety_result(safety_result),
            },
        )
        self.event_bus.publish(AFTER_COMMIT_GRAPH, promotion)
        return version

    # ---------------------------------------------------------------- indexes

    def build_port_index(self) -> PortIndex:
        return PortIndex.from_registry(self.registry)

    def build_route_table(self) -> RouteTable | None:
        snapshot = self.version_manager.active_snapshot()
        if snapshot is None:
            return None
        return RouteTable.build(snapshot, self.build_port_index())


def bundled_discovery(root: Path) -> ComponentDiscovery:
    """Convenience factory for a discovery instance pointed at ``root``."""

    return ComponentDiscovery(bundled=root)
