"""Minimal PROV-O compatible evidence object model.

We model the W3C PROV core triad (Entity, Activity, Agent) plus the
small relation vocabulary needed to explain candidate graph commits:
``used``, ``wasGeneratedBy``, ``wasAttributedTo``, ``wasDerivedFrom``,
and ``wasAssociatedWith``.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class RelationKind(str, Enum):
    USED = "used"
    WAS_GENERATED_BY = "wasGeneratedBy"
    WAS_ATTRIBUTED_TO = "wasAttributedTo"
    WAS_DERIVED_FROM = "wasDerivedFrom"
    WAS_ASSOCIATED_WITH = "wasAssociatedWith"


@dataclass(slots=True)
class ProvEntity:
    """A thing whose provenance we want to explain (a graph, a plan, ...)."""

    id: str
    kind: str = "entity"
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ProvActivity:
    """A time-bounded action that used or generated entities."""

    id: str
    kind: str = "activity"
    started_at: float = field(default_factory=lambda: time.time())
    ended_at: float | None = None
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ProvAgent:
    """An actor (component, user, service) responsible for an activity."""

    id: str
    kind: str = "agent"
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ProvRelation:
    """A PROV relation triple ``(subject, kind, object)``."""

    subject: str
    kind: RelationKind
    object: str
    attributes: dict[str, Any] = field(default_factory=dict)


class ProvGraph:
    """In-memory PROV graph.

    Nodes (entities, activities, agents) are keyed by id. Relations are
    appended in order and can be queried by subject/object/kind. The
    graph is intentionally minimal so it can be combined with the
    :class:`~metaharness.provenance.merkle.MerkleTree` for auditability.
    """

    def __init__(self) -> None:
        self.entities: dict[str, ProvEntity] = {}
        self.activities: dict[str, ProvActivity] = {}
        self.agents: dict[str, ProvAgent] = {}
        self.relations: list[ProvRelation] = []

    # -------------------------------------------------------- construction

    def add_entity(
        self, *, id: str | None = None, kind: str = "entity", **attributes: Any
    ) -> ProvEntity:
        eid = id or uuid.uuid4().hex
        entity = ProvEntity(id=eid, kind=kind, attributes=dict(attributes))
        self.entities[eid] = entity
        return entity

    def add_activity(
        self, *, id: str | None = None, kind: str = "activity", **attributes: Any
    ) -> ProvActivity:
        aid = id or uuid.uuid4().hex
        activity = ProvActivity(id=aid, kind=kind, attributes=dict(attributes))
        self.activities[aid] = activity
        return activity

    def add_agent(
        self, *, id: str | None = None, kind: str = "agent", **attributes: Any
    ) -> ProvAgent:
        aid = id or uuid.uuid4().hex
        agent = ProvAgent(id=aid, kind=kind, attributes=dict(attributes))
        self.agents[aid] = agent
        return agent

    def relate(
        self,
        subject: str,
        kind: RelationKind,
        obj: str,
        **attributes: Any,
    ) -> ProvRelation:
        relation = ProvRelation(subject=subject, kind=kind, object=obj, attributes=dict(attributes))
        self.relations.append(relation)
        return relation

    # ---------------------------------------------------------- inspection

    def relations_for(self, node_id: str) -> list[ProvRelation]:
        return [r for r in self.relations if r.subject == node_id or r.object == node_id]

    def by_kind(self, kind: RelationKind) -> list[ProvRelation]:
        return [r for r in self.relations if r.kind == kind]

    def to_dict(self) -> dict[str, Any]:
        return {
            "entities": {eid: asdict(entity) for eid, entity in self.entities.items()},
            "activities": {aid: asdict(act) for aid, act in self.activities.items()},
            "agents": {aid: asdict(agent) for aid, agent in self.agents.items()},
            "relations": [
                {
                    "subject": r.subject,
                    "kind": r.kind.value,
                    "object": r.object,
                    "attributes": r.attributes,
                }
                for r in self.relations
            ],
        }
