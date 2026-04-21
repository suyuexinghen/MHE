"""Phase A: local parameter search.

Performs grid or random search over a parameter schema around the
current baseline. Intended for small, fast tweaks to component
parameters (e.g. retry count, concurrency) without changing the
graph topology.
"""

from __future__ import annotations

import itertools
import random
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any

Parameters = dict[str, Any]
Objective = Callable[[Parameters], float]


@dataclass(slots=True)
class ParameterTrial:
    """One trial run in the local parameter search."""

    params: Parameters
    score: float


@dataclass(slots=True)
class LocalParameterSearch:
    """Grid or random search over a parameter schema.

    ``schema`` maps each parameter name to an iterable of candidate
    values. ``strategy`` chooses ``"grid"`` or ``"random"``; random
    search draws ``random_samples`` points uniformly from the full grid.
    """

    schema: dict[str, Iterable[Any]] = field(default_factory=dict)
    strategy: str = "grid"
    random_samples: int = 16
    rng_seed: int | None = None
    history: list[ParameterTrial] = field(default_factory=list)

    def _grid(self) -> list[Parameters]:
        keys = list(self.schema.keys())
        combos = [list(v) for v in self.schema.values()]
        return [dict(zip(keys, values, strict=True)) for values in itertools.product(*combos)]

    def _random(self) -> list[Parameters]:
        rng = random.Random(self.rng_seed)
        keys = list(self.schema.keys())
        values = [list(v) for v in self.schema.values()]
        total = 1
        for vs in values:
            total *= max(1, len(vs))
        if total == 0:
            return []
        # Enumerate the grid once for fair sampling even when dimensions differ.
        grid = [dict(zip(keys, combo, strict=True)) for combo in itertools.product(*values)]
        k = min(self.random_samples, len(grid))
        rng.shuffle(grid)
        return grid[:k]

    def candidates(self) -> list[Parameters]:
        if not self.schema:
            return []
        if self.strategy == "random":
            return self._random()
        return self._grid()

    def run(self, objective: Objective) -> ParameterTrial:
        best: ParameterTrial | None = None
        for params in self.candidates():
            score = objective(params)
            trial = ParameterTrial(params=dict(params), score=score)
            self.history.append(trial)
            if best is None or trial.score > best.score:
                best = trial
        if best is None:
            return ParameterTrial(params={}, score=float("-inf"))
        return best
