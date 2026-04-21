"""Runtime-authoritative graph models for Meta-Harness."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from metaharness.sdk.contracts import ConnectionPolicy, RouteMode
from metaharness.sdk.lifecycle import ComponentPhase
from metaharness.sdk.manifest import ComponentManifest


class ComponentNode(BaseModel):
    """A component instance in a graph snapshot."""

    component_id: str
    component_type: str
    implementation: str
    version: str
    phase: ComponentPhase = ComponentPhase.DISCOVERED
    protected: bool = False
    manifest: ComponentManifest | None = None
    config: dict[str, str] = Field(default_factory=dict)


class ConnectionEdge(BaseModel):
    """A directed connection between component ports."""

    connection_id: str
    source: str
    target: str
    payload: str
    mode: RouteMode
    policy: ConnectionPolicy = ConnectionPolicy.REQUIRED


class PendingConnection(BaseModel):
    """A single proposed edge staged before commit.

    ``PendingConnection`` is the per-edge unit the roadmap calls out; several
    of these roll up into a :class:`PendingConnectionSet` together with node
    and mutation metadata before validation.
    """

    connection_id: str
    source: str
    target: str
    payload: str
    mode: RouteMode = RouteMode.SYNC
    policy: ConnectionPolicy = ConnectionPolicy.REQUIRED

    def to_edge(self) -> ConnectionEdge:
        return ConnectionEdge(
            connection_id=self.connection_id,
            source=self.source,
            target=self.target,
            payload=self.payload,
            mode=self.mode,
            policy=self.policy,
        )


class MutationType(str, Enum):
    """High-level taxonomy of mutation proposals."""

    PARAM = "param"
    CONNECTION = "connection"
    TEMPLATE = "template"
    CODE = "code"
    POLICY = "policy"


class PendingMutation(BaseModel):
    """A candidate mutation against the active graph."""

    mutation_id: str
    description: str
    type: MutationType = MutationType.CONNECTION
    target: str | None = None
    justification: str = ""
    target_graph_version: int | None = None


class PendingConnectionSet(BaseModel):
    """Pending graph changes before validation and commit."""

    nodes: list[ComponentNode] = Field(default_factory=list)
    edges: list[ConnectionEdge] = Field(default_factory=list)
    mutations: list[PendingMutation] = Field(default_factory=list)

    def add_pending_connection(self, pending: PendingConnection) -> None:
        """Append a :class:`PendingConnection` as a concrete edge."""

        self.edges.append(pending.to_edge())


class ValidationIssue(BaseModel):
    """A validation problem found in a candidate graph."""

    code: str
    message: str
    subject: str


class ValidationReport(BaseModel):
    """Validation outcome for a candidate graph."""

    valid: bool
    issues: list[ValidationIssue] = Field(default_factory=list)


class GraphSnapshot(BaseModel):
    """An immutable graph snapshot candidate or active version."""

    graph_version: int
    nodes: list[ComponentNode] = Field(default_factory=list)
    edges: list[ConnectionEdge] = Field(default_factory=list)


class GraphState(BaseModel):
    """Active and rollback pointers for committed graphs."""

    active_graph_version: int | None = None
    rollback_graph_version: int | None = None
    archived_graph_versions: list[int] = Field(default_factory=list)
