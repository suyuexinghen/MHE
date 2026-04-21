"""Level 2 A/B shadow tester.

Runs a trial workload against both the baseline graph and the candidate
graph, compares outputs, and emits a gate result. The comparison
function is pluggable so callers can swap in distribution tests, metric
thresholds, or exact-match checks.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from metaharness.core.mutation import MutationProposal
from metaharness.safety.gates import GateDecision, GateResult

Runner = Callable[[MutationProposal, dict[str, Any]], Any]
Comparator = Callable[[Any, Any], tuple[bool, str]]


def _default_comparator(baseline: Any, candidate: Any) -> tuple[bool, str]:
    """Default comparator: exact equality counts as success."""

    if baseline == candidate:
        return True, "outputs match"
    return False, f"divergence: baseline={baseline!r} candidate={candidate!r}"


@dataclass(slots=True)
class ShadowTestResult:
    """Outcome of a shadow comparison for a single trial input."""

    match: bool
    baseline: Any
    candidate: Any
    detail: str = ""


@dataclass(slots=True)
class ABShadowTester:
    """Level 2 safety gate.

    ``baseline_runner`` is invoked against the currently-active graph and
    ``candidate_runner`` is invoked against the pending proposal. The
    comparator decides whether the candidate output is acceptable.
    """

    name: str = "level_2_ab_shadow"
    baseline_runner: Runner | None = None
    candidate_runner: Runner | None = None
    comparator: Comparator = _default_comparator
    history: list[ShadowTestResult] = field(default_factory=list)

    def evaluate(
        self, proposal: MutationProposal, context: dict[str, Any] | None = None
    ) -> GateResult:
        if self.baseline_runner is None or self.candidate_runner is None:
            # When no runners are configured, defer (gate is not applicable).
            return GateResult(
                gate=self.name,
                decision=GateDecision.DEFER,
                reason="no shadow runners configured",
            )
        ctx = context or {}
        trials = list(ctx.get("trials") or [ctx])
        mismatches: list[ShadowTestResult] = []
        for trial in trials:
            baseline = self.baseline_runner(proposal, trial)
            candidate = self.candidate_runner(proposal, trial)
            match, detail = self.comparator(baseline, candidate)
            result = ShadowTestResult(
                match=match, baseline=baseline, candidate=candidate, detail=detail
            )
            self.history.append(result)
            if not match:
                mismatches.append(result)
        if not mismatches:
            return GateResult(
                gate=self.name,
                decision=GateDecision.ALLOW,
                evidence={"trials": len(trials)},
            )
        return GateResult(
            gate=self.name,
            decision=GateDecision.REJECT,
            reason=f"{len(mismatches)}/{len(trials)} shadow mismatch(es)",
            evidence={"first_detail": mismatches[0].detail},
        )
