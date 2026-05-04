"""Assembly lineage and copy-count companion services."""

from __future__ import annotations

import time
import uuid
from typing import Any

from pydantic import BaseModel, Field


class AssemblyRecord(BaseModel):
    """Recorded assembly fact for a component, candidate, or committed graph."""

    record_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    artifact_ref: str
    artifact_kind: str
    version: str | None = None
    parent_refs: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    component_refs: list[str] = Field(default_factory=list)
    validation_refs: list[str] = Field(default_factory=list)
    graph_version: int | None = None
    candidate_id: str | None = None
    lineage_status: str = "recorded_partial"
    assembly_context: dict[str, Any] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)


class CopyCountRecord(BaseModel):
    """Per-session copy/reuse counters for an assembly artifact."""

    artifact_ref: str
    registered_count: int = 0
    candidate_membership_count: int = 0
    committed_membership_count: int = 0
    dependency_count: int = 0
    graph_reuse_count: int = 0
    invoked_count: int = 0
    external_verified_count: int = 0


class DependencyGraphNode(BaseModel):
    """Node captured in an assembly dependency graph snapshot."""

    node_id: str
    artifact_ref: str
    artifact_kind: str = "component"
    lineage_status: str = "unknown"
    copy_count: int = 0


class DependencyGraphEdge(BaseModel):
    """Directed dependency edge captured for assembly scoring."""

    edge_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    source_ref: str
    target_ref: str
    relation: str = "depends_on"


class DependencyGraphSnapshot(BaseModel):
    """Serializable assembly dependency graph snapshot."""

    snapshot_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    candidate_id: str | None = None
    graph_version: int | None = None
    nodes: list[DependencyGraphNode] = Field(default_factory=list)
    edges: list[DependencyGraphEdge] = Field(default_factory=list)
    parent_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    assembly_index: int = 0
    lineage_completeness: float = 0.0
    history_folding_ratio: float = 0.0
    low_copy_critical_dependency_count: int = 0
    lineage_status: str = "unknown"
    artifact_snapshot_id: str | None = None
    created_at: float = Field(default_factory=time.time)


class AssemblyHealthSummary(BaseModel):
    """WARN-mode health summary for a graph promotion."""

    candidate_id: str
    graph_version: int | None = None
    component_count: int = 0
    edge_count: int = 0
    lineage_completeness: float = 0.0
    new_component_refs: list[str] = Field(default_factory=list)
    low_copy_component_refs: list[str] = Field(default_factory=list)
    assembly_index: int = 0
    history_folding_ratio: float = 0.0
    low_copy_critical_dependency_count: int = 0
    lineage_status: str = "unknown"
    dependency_graph_ref: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class CopyCountIndex:
    """In-memory per-session copy/reuse counter index."""

    def __init__(self) -> None:
        self._records: dict[str, CopyCountRecord] = {}

    def _record(self, artifact_ref: str) -> CopyCountRecord:
        record = self._records.get(artifact_ref)
        if record is None:
            record = CopyCountRecord(artifact_ref=artifact_ref)
            self._records[artifact_ref] = record
        return record

    def mark_registered(self, artifact_ref: str) -> CopyCountRecord:
        record = self._record(artifact_ref)
        record.registered_count += 1
        return record

    def mark_candidate_member(self, artifact_ref: str) -> CopyCountRecord:
        record = self._record(artifact_ref)
        record.candidate_membership_count += 1
        return record

    def mark_committed_member(self, artifact_ref: str) -> CopyCountRecord:
        record = self._record(artifact_ref)
        record.committed_membership_count += 1
        record.graph_reuse_count += 1
        return record

    def mark_dependency(self, artifact_ref: str) -> CopyCountRecord:
        record = self._record(artifact_ref)
        record.dependency_count += 1
        return record

    def mark_invoked(self, artifact_ref: str) -> CopyCountRecord:
        record = self._record(artifact_ref)
        record.invoked_count += 1
        return record

    def mark_external_verified(self, artifact_ref: str) -> CopyCountRecord:
        record = self._record(artifact_ref)
        record.external_verified_count += 1
        return record

    def record_for(self, artifact_ref: str) -> CopyCountRecord:
        return self._record(artifact_ref)

    def records_for(self, artifact_refs: list[str] | None = None) -> list[CopyCountRecord]:
        if artifact_refs is None:
            return list(self._records.values())
        return [self._record(ref) for ref in artifact_refs]


class AssemblyLedger:
    """In-memory per-session assembly lineage ledger."""

    def __init__(self) -> None:
        self._records: list[AssemblyRecord] = []
        self._dependency_graphs: dict[str, DependencyGraphSnapshot] = {}

    @property
    def records(self) -> list[AssemblyRecord]:
        return list(self._records)

    def append(self, record: AssemblyRecord) -> AssemblyRecord:
        self._records.append(record)
        return record

    def record_component_registered(
        self,
        component_id: str,
        *,
        manifest_id: str | None = None,
        graph_version: int | None = None,
        source_refs: list[str] | None = None,
        assembly_context: dict[str, Any] | None = None,
    ) -> AssemblyRecord:
        context = dict(assembly_context or {})
        if manifest_id is not None:
            context.setdefault("manifest_id", manifest_id)
        sources = list(source_refs or [])
        if manifest_id is not None and manifest_id != component_id and manifest_id not in sources:
            sources.append(f"manifest:{manifest_id}")
        return self.append(
            AssemblyRecord(
                artifact_ref=component_id,
                artifact_kind="component",
                source_refs=sources,
                graph_version=graph_version,
                lineage_status="component_registered",
                assembly_context=context,
            )
        )

    def record_graph_candidate(
        self,
        candidate_id: str,
        *,
        graph_version: int | None,
        component_refs: list[str],
        edge_refs: list[str],
        parent_refs: list[str] | None = None,
        validation_refs: list[str] | None = None,
        assembly_context: dict[str, Any] | None = None,
    ) -> AssemblyRecord:
        context = dict(assembly_context or {})
        context.setdefault("edge_refs", list(edge_refs))
        return self.append(
            AssemblyRecord(
                artifact_ref=f"graph-candidate:{candidate_id}",
                artifact_kind="graph_candidate",
                parent_refs=list(parent_refs or []),
                component_refs=list(component_refs),
                validation_refs=list(validation_refs or []),
                graph_version=graph_version,
                candidate_id=candidate_id,
                lineage_status="candidate_recorded_partial",
                assembly_context=context,
            )
        )

    def record_graph_committed(
        self,
        candidate_id: str,
        *,
        graph_version: int,
        component_refs: list[str],
        edge_refs: list[str],
        parent_refs: list[str] | None = None,
        validation_refs: list[str] | None = None,
        assembly_context: dict[str, Any] | None = None,
    ) -> AssemblyRecord:
        context = dict(assembly_context or {})
        context.setdefault("edge_refs", list(edge_refs))
        return self.append(
            AssemblyRecord(
                artifact_ref=f"graph-version:{graph_version}",
                artifact_kind="graph_version",
                version=str(graph_version),
                parent_refs=list(parent_refs or []),
                component_refs=list(component_refs),
                validation_refs=list(validation_refs or []),
                graph_version=graph_version,
                candidate_id=candidate_id,
                lineage_status="graph_committed_partial",
                assembly_context=context,
            )
        )

    def records_for_candidate(self, candidate_id: str) -> list[AssemblyRecord]:
        return [record for record in self._records if record.candidate_id == candidate_id]

    def records_for_graph_version(self, graph_version: int) -> list[AssemblyRecord]:
        return [record for record in self._records if record.graph_version == graph_version]

    def records_for_artifact(self, artifact_ref: str) -> list[AssemblyRecord]:
        return [record for record in self._records if record.artifact_ref == artifact_ref]

    def record_dependency_graph(
        self,
        *,
        candidate_id: str | None,
        graph_version: int | None,
        component_refs: list[str],
        dependency_edges: list[tuple[str, str]] | None = None,
        parent_refs: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        copy_count_index: CopyCountIndex | None = None,
    ) -> DependencyGraphSnapshot:
        unique_components = sorted(set(component_refs))
        dependency_edges = list(dependency_edges or [])
        critical_refs = {ref for edge in dependency_edges for ref in edge}
        nodes: list[DependencyGraphNode] = []
        recorded_count = 0
        reused_count = 0
        low_copy_critical_count = 0
        for component_ref in unique_components:
            records = self.records_for_artifact(component_ref)
            lineage_status = "recorded" if records else "unknown"
            if records:
                recorded_count += 1
            copy_count = 0
            if copy_count_index is not None:
                copy_count = copy_count_index.record_for(component_ref).graph_reuse_count
            if copy_count > 0:
                reused_count += 1
            if component_ref in critical_refs and copy_count < 1:
                low_copy_critical_count += 1
            nodes.append(
                DependencyGraphNode(
                    node_id=component_ref,
                    artifact_ref=component_ref,
                    lineage_status=lineage_status,
                    copy_count=copy_count,
                )
            )
        edges = [
            DependencyGraphEdge(source_ref=source_ref, target_ref=target_ref)
            for source_ref, target_ref in dependency_edges
            if source_ref in unique_components and target_ref in unique_components
        ]
        lineage_completeness = recorded_count / len(unique_components) if unique_components else 1.0
        lineage_status = self._lineage_status(lineage_completeness, unique_components)
        snapshot = DependencyGraphSnapshot(
            candidate_id=candidate_id,
            graph_version=graph_version,
            nodes=nodes,
            edges=edges,
            parent_refs=list(parent_refs or []),
            evidence_refs=list(evidence_refs or []),
            assembly_index=self._longest_dependency_path(unique_components, edges),
            lineage_completeness=lineage_completeness,
            history_folding_ratio=reused_count / len(unique_components)
            if unique_components
            else 1.0,
            low_copy_critical_dependency_count=low_copy_critical_count,
            lineage_status=lineage_status,
        )
        self._dependency_graphs[snapshot.snapshot_id] = snapshot
        return snapshot

    def dependency_graphs_for_candidate(self, candidate_id: str) -> list[DependencyGraphSnapshot]:
        return [
            graph
            for graph in self._dependency_graphs.values()
            if graph.candidate_id == candidate_id
        ]

    def dependency_graphs_for_graph_version(
        self, graph_version: int
    ) -> list[DependencyGraphSnapshot]:
        return [
            graph
            for graph in self._dependency_graphs.values()
            if graph.graph_version == graph_version
        ]

    def dependency_graph(self, snapshot_id: str) -> DependencyGraphSnapshot | None:
        return self._dependency_graphs.get(snapshot_id)

    def dependency_graphs(self) -> list[DependencyGraphSnapshot]:
        return list(self._dependency_graphs.values())

    def mark_dependency_graph_persisted(
        self, snapshot_id: str, artifact_snapshot_id: str
    ) -> DependencyGraphSnapshot | None:
        snapshot = self._dependency_graphs.get(snapshot_id)
        if snapshot is None:
            return None
        updated = snapshot.model_copy(update={"artifact_snapshot_id": artifact_snapshot_id})
        self._dependency_graphs[snapshot_id] = updated
        return updated

    def health_summary(
        self,
        *,
        candidate_id: str,
        graph_version: int | None,
        component_refs: list[str],
        edge_count: int,
        copy_count_index: CopyCountIndex | None = None,
        dependency_graph_snapshot: DependencyGraphSnapshot | None = None,
        low_copy_threshold: int = 1,
    ) -> AssemblyHealthSummary:
        unique_components = sorted(set(component_refs))
        component_records = {
            component_ref: self.records_for_artifact(component_ref)
            for component_ref in unique_components
        }
        recorded_components = [ref for ref, records in component_records.items() if records]
        lineage_completeness = (
            len(recorded_components) / len(unique_components) if unique_components else 1.0
        )
        new_component_refs = [ref for ref, records in component_records.items() if not records]
        low_copy_component_refs: list[str] = []
        if copy_count_index is not None:
            for component_ref in unique_components:
                copy_record = copy_count_index.record_for(component_ref)
                if copy_record.graph_reuse_count < low_copy_threshold:
                    low_copy_component_refs.append(component_ref)
        assembly_index = (
            dependency_graph_snapshot.assembly_index if dependency_graph_snapshot else 0
        )
        history_folding_ratio = (
            dependency_graph_snapshot.history_folding_ratio if dependency_graph_snapshot else 0.0
        )
        low_copy_critical_dependency_count = (
            dependency_graph_snapshot.low_copy_critical_dependency_count
            if dependency_graph_snapshot
            else 0
        )
        lineage_status = (
            dependency_graph_snapshot.lineage_status
            if dependency_graph_snapshot
            else self._lineage_status(lineage_completeness, unique_components)
        )
        dependency_graph_ref = (
            dependency_graph_snapshot.snapshot_id if dependency_graph_snapshot else None
        )
        evidence_refs = (
            list(dependency_graph_snapshot.evidence_refs) if dependency_graph_snapshot else []
        )
        if dependency_graph_snapshot and dependency_graph_snapshot.artifact_snapshot_id is not None:
            evidence_refs.append(
                f"artifact-snapshot:{dependency_graph_snapshot.artifact_snapshot_id}"
            )
        warnings: list[str] = []
        if new_component_refs:
            warnings.append("assembly_lineage_missing")
        if low_copy_component_refs:
            warnings.append("low_copy_components")
        if low_copy_critical_dependency_count:
            warnings.append("low_copy_critical_dependencies")
        if lineage_status in {"unknown", "partial"} and unique_components:
            warnings.append(f"assembly_lineage_{lineage_status}")
        return AssemblyHealthSummary(
            candidate_id=candidate_id,
            graph_version=graph_version,
            component_count=len(unique_components),
            edge_count=edge_count,
            lineage_completeness=lineage_completeness,
            new_component_refs=new_component_refs,
            low_copy_component_refs=low_copy_component_refs,
            assembly_index=assembly_index,
            history_folding_ratio=history_folding_ratio,
            low_copy_critical_dependency_count=low_copy_critical_dependency_count,
            lineage_status=lineage_status,
            dependency_graph_ref=dependency_graph_ref,
            evidence_refs=evidence_refs,
            warnings=list(dict.fromkeys(warnings)),
        )

    def _lineage_status(self, lineage_completeness: float, component_refs: list[str]) -> str:
        if not component_refs:
            return "complete"
        if lineage_completeness >= 1.0:
            return "complete"
        if lineage_completeness <= 0.0:
            return "unknown"
        return "partial"

    def _longest_dependency_path(
        self, component_refs: list[str], edges: list[DependencyGraphEdge]
    ) -> int:
        if not component_refs:
            return 0
        successors: dict[str, list[str]] = {component_ref: [] for component_ref in component_refs}
        for edge in edges:
            successors.setdefault(edge.source_ref, []).append(edge.target_ref)
        visiting: set[str] = set()
        visited: dict[str, int] = {}

        def depth(component_ref: str) -> int:
            if component_ref in visited:
                return visited[component_ref]
            if component_ref in visiting:
                return 1
            visiting.add(component_ref)
            child_depths = [depth(child_ref) for child_ref in successors.get(component_ref, [])]
            visiting.remove(component_ref)
            visited[component_ref] = 1 + max(child_depths, default=0)
            return visited[component_ref]

        return max(depth(component_ref) for component_ref in component_refs)
