"""Runtime-authoritative graph models for Meta-Harness."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

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


class ValidationIssueCategory(str, Enum):
    """Classification of a validation issue's domain."""

    SEMANTIC = "semantic"
    PROTECTED_COMPONENT = "protected_component"
    READINESS = "readiness"
    PROMOTION_BLOCKER = "promotion_blocker"


class ValidationIssue(BaseModel):
    """A validation problem found in a candidate graph."""

    code: str
    message: str
    subject: str
    category: ValidationIssueCategory = ValidationIssueCategory.SEMANTIC
    blocks_promotion: bool = False


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


class BudgetState(BaseModel):
    """Budget consumption snapshot attached to a scored evaluation."""

    used: int = 0
    limit: int | None = None
    remaining: int | None = None
    exhausted: bool = False


class ConvergenceState(BaseModel):
    """Convergence snapshot attached to a scored evaluation."""

    converged: bool = False
    criteria_met: list[str] = Field(default_factory=list)
    reason: str = ""


class ScoredEvidence(BaseModel):
    """Unified scored evidence record for evaluation and optimizer paths.

    The shape is intentionally additive: callers can keep consuming the legacy
    scalar ``score`` while newer paths inspect decomposed metrics, safety,
    budget, convergence, and provenance references from one payload.
    """

    score: float = 0.0
    metrics: dict[str, float] = Field(default_factory=dict)
    safety_score: float | None = None
    budget: BudgetState | None = None
    convergence: ConvergenceState | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_legacy_payload(cls, payload: dict[str, Any]) -> "ScoredEvidence":
        """Lift older dict payloads into the shared protocol."""

        raw_score = payload.get("score", 0.0)
        try:
            score = float(raw_score)
        except (TypeError, ValueError):
            score = 0.0
        attributes = {k: v for k, v in payload.items() if k != "score"}
        return cls(score=score, attributes=attributes)

    def as_legacy_payload(self) -> dict[str, str]:
        """Render the backward-compatible payload used by older components."""

        payload = {"score": str(self.score)}
        payload.update({key: str(value) for key, value in self.attributes.items()})
        return payload


# ---------------------------------------------------------------------------
# Promotion context — the unified record for a candidate graph promotion attempt
# ---------------------------------------------------------------------------


class PromotionContext(BaseModel):
    """Everything the runtime needs to evaluate a candidate graph promotion."""

    candidate_id: str
    candidate_snapshot: GraphSnapshot
    validation_report: ValidationReport
    proposed_graph_version: int
    rollback_target: int | None = None
    actor: str | None = None
    affected_protected_components: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Session event / store — CMA-inspired append-only session log
# ---------------------------------------------------------------------------


class SessionEventType(str, Enum):
    """Types of events recorded in a harness session."""

    CANDIDATE_CREATED = "candidate_created"
    CANDIDATE_VALIDATED = "candidate_validated"
    CANDIDATE_DEFERRED = "candidate_deferred"
    CANDIDATE_REJECTED = "candidate_rejected"
    GRAPH_COMMITTED = "graph_committed"
    GRAPH_ROLLED_BACK = "graph_rolled_back"
    ENVIRONMENT_PROBED = "environment_probed"
    TASK_SUBMITTED = "task_submitted"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_RETRIED = "task_retried"
    CHECKPOINT_SAVED = "checkpoint_saved"
    SAFETY_GATE_EVALUATED = "safety_gate_evaluated"
    HOT_SWAP_INITIATED = "hot_swap_initiated"
    HOT_SWAP_COMPLETED = "hot_swap_completed"
    HOT_SWAP_ROLLED_BACK = "hot_swap_rolled_back"


class SessionEvent(BaseModel):
    """A single immutable event in the harness session log."""

    event_id: str
    session_id: str
    event_type: SessionEventType
    graph_version: int | None = None
    candidate_id: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: dict[str, object] = Field(default_factory=dict)
