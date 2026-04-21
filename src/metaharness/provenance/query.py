"""Provenance query helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from metaharness.provenance.evidence import ProvGraph, ProvRelation, RelationKind


@dataclass(slots=True)
class ProvenanceQuery:
    """Structured query API over a :class:`ProvGraph`.

    The helpers here intentionally return plain lists of relations or
    ids so callers can feed them into audit reports, UIs, or the
    counter-factual diagnosis module.
    """

    graph: ProvGraph

    # ----------------------------------------------------------- ancestry

    def ancestors_of(self, entity_id: str) -> list[str]:
        """Walk ``wasDerivedFrom`` edges backwards from ``entity_id``."""

        seen: set[str] = set()
        stack = [entity_id]
        while stack:
            current = stack.pop()
            for relation in self.graph.relations:
                if relation.kind != RelationKind.WAS_DERIVED_FROM:
                    continue
                if relation.subject == current and relation.object not in seen:
                    seen.add(relation.object)
                    stack.append(relation.object)
        return sorted(seen)

    def descendants_of(self, entity_id: str) -> list[str]:
        """Walk ``wasDerivedFrom`` edges forwards from ``entity_id``."""

        seen: set[str] = set()
        stack = [entity_id]
        while stack:
            current = stack.pop()
            for relation in self.graph.relations:
                if relation.kind != RelationKind.WAS_DERIVED_FROM:
                    continue
                if relation.object == current and relation.subject not in seen:
                    seen.add(relation.subject)
                    stack.append(relation.subject)
        return sorted(seen)

    # --------------------------------------------------------- attribution

    def activity_for(self, entity_id: str) -> str | None:
        for relation in self.graph.relations:
            if relation.kind == RelationKind.WAS_GENERATED_BY and relation.subject == entity_id:
                return relation.object
        return None

    def agents_for(self, activity_id: str) -> list[str]:
        return [
            r.object
            for r in self.graph.relations
            if r.kind == RelationKind.WAS_ASSOCIATED_WITH and r.subject == activity_id
        ]

    def inputs_of(self, activity_id: str) -> list[str]:
        return [
            r.object
            for r in self.graph.relations
            if r.kind == RelationKind.USED and r.subject == activity_id
        ]

    # ------------------------------------------------------------- filter

    def relations(
        self,
        *,
        subject: str | None = None,
        kind: RelationKind | None = None,
        object: str | None = None,
    ) -> list[ProvRelation]:
        return [
            r
            for r in self.graph.relations
            if (subject is None or r.subject == subject)
            and (kind is None or r.kind == kind)
            and (object is None or r.object == object)
        ]

    def summarize(self, entity_id: str) -> dict[str, Any]:
        """Compact dict summarising everything we know about ``entity_id``."""

        activity = self.activity_for(entity_id)
        return {
            "entity": entity_id,
            "activity": activity,
            "agents": self.agents_for(activity) if activity else [],
            "inputs": self.inputs_of(activity) if activity else [],
            "ancestors": self.ancestors_of(entity_id),
            "descendants": self.descendants_of(entity_id),
        }
