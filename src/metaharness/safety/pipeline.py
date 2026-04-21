"""Sequential four-level safety gate pipeline.

Runs Guard -> Mutate hooks first, then walks the ordered list of
:class:`SafetyGate` instances. The first reject short-circuits the
pipeline. Results are collected into a :class:`SafetyPipelineResult`
for auditing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from metaharness.core.mutation import MutationProposal
from metaharness.safety.gates import GateDecision, GateResult, SafetyGate
from metaharness.safety.hooks import HookRegistry


@dataclass(slots=True)
class SafetyPipelineResult:
    """Record of a full pipeline execution against a single proposal."""

    proposal: MutationProposal
    allowed: bool
    results: list[GateResult] = field(default_factory=list)
    rejected_by: str | None = None
    rejected_reason: str | None = None
    guard_vetoed: bool = False
    mutated: bool = False


class SafetyPipeline:
    """Runs the safety chain in strict order.

    Gates are consulted in list order; reducers run over a list of
    proposals once before the per-proposal gating begins. Callers can
    subclass or extend this with additional levels without touching the
    core gates.
    """

    def __init__(
        self,
        gates: list[SafetyGate] | None = None,
        *,
        hooks: HookRegistry | None = None,
    ) -> None:
        self.gates: list[SafetyGate] = list(gates or [])
        self.hooks = hooks or HookRegistry()

    # ---------------------------------------------------------- structure

    def add_gate(self, gate: SafetyGate) -> None:
        self.gates.append(gate)

    # ------------------------------------------------------------- evaluate

    def evaluate(
        self,
        proposal: MutationProposal,
        context: dict[str, Any] | None = None,
    ) -> SafetyPipelineResult:
        result = SafetyPipelineResult(proposal=proposal, allowed=True)

        if not self.hooks.apply_guards(proposal):
            result.allowed = False
            result.guard_vetoed = True
            result.rejected_by = "guard_hook"
            result.rejected_reason = "vetoed by guard hook"
            return result

        mutated = self.hooks.apply_mutators(proposal)
        if mutated is not proposal:
            result.mutated = True
            result.proposal = mutated

        for gate in self.gates:
            gate_result = gate.evaluate(result.proposal, context)
            result.results.append(gate_result)
            if gate_result.decision == GateDecision.REJECT:
                result.allowed = False
                result.rejected_by = gate.name
                result.rejected_reason = gate_result.reason
                return result
        return result

    def evaluate_batch(
        self,
        proposals: list[MutationProposal],
        context: dict[str, Any] | None = None,
    ) -> list[SafetyPipelineResult]:
        reduced = self.hooks.apply_reducers(proposals)
        return [self.evaluate(p, context) for p in reduced]
