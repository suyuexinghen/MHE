"""Optional RL enhancement.

Provides a minimal policy-gradient-style wrapper that keeps a running
softmax policy over a discrete action space and updates it with
simple REINFORCE updates. Deliberately light-weight so we don't pull
in heavy ML dependencies.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Hashable


@dataclass(slots=True)
class RLEnhancement:
    """Minimal softmax policy with REINFORCE-style updates.

    The module is *optional*: callers can skip it entirely and rely on
    :class:`BayesianOptimizer` for search. When engaged, it keeps
    preference weights per action and samples proportionally.
    """

    learning_rate: float = 0.1
    temperature: float = 1.0
    seed: int | None = None
    preferences: dict[Hashable, float] = field(default_factory=dict)
    _rng: random.Random = field(init=False)

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)

    # ----------------------------------------------------------- sampling

    def _softmax(self, actions: list[Hashable]) -> list[float]:
        prefs = [self.preferences.get(a, 0.0) / max(self.temperature, 1e-9) for a in actions]
        m = max(prefs) if prefs else 0.0
        exps = [math.exp(p - m) for p in prefs]
        total = sum(exps) or 1.0
        return [e / total for e in exps]

    def sample(self, actions: list[Hashable]) -> Hashable:
        if not actions:
            raise ValueError("no actions to sample from")
        probs = self._softmax(actions)
        r = self._rng.random()
        cumulative = 0.0
        for action, p in zip(actions, probs, strict=True):
            cumulative += p
            if r <= cumulative:
                return action
        return actions[-1]

    def probabilities(self, actions: list[Hashable]) -> dict[Hashable, float]:
        return dict(zip(actions, self._softmax(actions), strict=True))

    # ------------------------------------------------------------ updates

    def update(self, action: Hashable, reward: float, actions: list[Hashable]) -> None:
        """REINFORCE-style preference update for a discrete action."""

        probs = self.probabilities(actions)
        for candidate in actions:
            baseline = probs[candidate]
            indicator = 1.0 if candidate == action else 0.0
            gradient = reward * (indicator - baseline)
            current = self.preferences.get(candidate, 0.0)
            self.preferences[candidate] = current + self.learning_rate * gradient
