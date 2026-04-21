"""GIN-style graph state encoder.

A minimal pure-Python approximation of a Graph Isomorphism Network
(GIN) aggregation: each node embeds its own features and then repeats
``layers`` rounds of summed-neighbor-plus-self aggregation followed by
a deterministic non-linear mix. We deliberately avoid adding torch as
a dependency; this module is a reference encoder good enough for
ranking and pruning candidate actions.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    from metaharness.core.models import GraphSnapshot


@dataclass(slots=True)
class NodeFeatures:
    """Dense feature vector for a single node."""

    node_id: str
    vector: list[float]


@dataclass(slots=True)
class GraphEmbedding:
    """Result of encoding one graph."""

    nodes: dict[str, NodeFeatures]
    graph_vector: list[float] = field(default_factory=list)


class GINEncoder:
    """Deterministic GIN-like encoder.

    Node feature vectors are produced by hashing the component id /
    type / payload declarations; aggregation sums neighbor vectors with
    a small ``epsilon`` self-weight to preserve the GIN identity. The
    output is a per-node embedding plus a pooled graph-level vector.
    """

    def __init__(self, *, dim: int = 16, layers: int = 2, epsilon: float = 0.1) -> None:
        if dim <= 0:
            raise ValueError("dim must be positive")
        if layers <= 0:
            raise ValueError("layers must be positive")
        self.dim = dim
        self.layers = layers
        self.epsilon = epsilon

    def _hash_vector(self, token: str) -> list[float]:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        vec = [((digest[i % len(digest)] / 255.0) * 2.0) - 1.0 for i in range(self.dim)]
        return vec

    @staticmethod
    def _activate(vec: list[float]) -> list[float]:
        # Tanh keeps values bounded without pulling in a heavy dependency.
        return [math.tanh(v) for v in vec]

    @staticmethod
    def _add(a: list[float], b: list[float]) -> list[float]:
        return [x + y for x, y in zip(a, b, strict=True)]

    @staticmethod
    def _scale(a: list[float], s: float) -> list[float]:
        return [x * s for x in a]

    def encode(self, snapshot: GraphSnapshot) -> GraphEmbedding:
        # Seed feature vectors from component id + type.
        features: dict[str, list[float]] = {}
        for node in snapshot.nodes:
            token = f"{node.component_id}|{node.component_type}|{node.implementation}"
            features[node.component_id] = self._hash_vector(token)

        neighbors: dict[str, list[str]] = {n.component_id: [] for n in snapshot.nodes}
        for edge in snapshot.edges:
            src = edge.source.rpartition(".")[0]
            dst = edge.target.rpartition(".")[0]
            if src in neighbors and dst in neighbors:
                neighbors[src].append(dst)
                neighbors[dst].append(src)

        # Message-passing layers.
        for _ in range(self.layers):
            next_features: dict[str, list[float]] = {}
            for node_id, vec in features.items():
                agg = [0.0] * self.dim
                for nbr_id in neighbors.get(node_id, []):
                    agg = self._add(agg, features[nbr_id])
                combined = self._add(agg, self._scale(vec, 1.0 + self.epsilon))
                next_features[node_id] = self._activate(combined)
            features = next_features

        node_embeddings = {
            node_id: NodeFeatures(node_id=node_id, vector=vec) for node_id, vec in features.items()
        }

        graph_vector: list[float]
        if features:
            graph_vector = [0.0] * self.dim
            for vec in features.values():
                graph_vector = self._add(graph_vector, vec)
            graph_vector = self._scale(graph_vector, 1.0 / max(1, len(features)))
        else:
            graph_vector = [0.0] * self.dim

        return GraphEmbedding(nodes=node_embeddings, graph_vector=graph_vector)
