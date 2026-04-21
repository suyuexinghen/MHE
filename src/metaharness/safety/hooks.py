"""Guard / Mutate / Reduce hooks.

Components or pipeline operators register callables that inspect,
transform, or aggregate mutation proposals before they reach the commit
stage. The naming mirrors the roadmap: Guard vetoes, Mutate rewrites,
Reduce collapses multiple proposals.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from metaharness.core.mutation import MutationProposal

GuardHook = Callable[[MutationProposal], bool]
MutateHook = Callable[[MutationProposal], MutationProposal]
ReduceHook = Callable[[list[MutationProposal]], list[MutationProposal]]


@dataclass(slots=True)
class HookRegistry:
    """Holds the three hook families for a pipeline instance."""

    guards: list[GuardHook] = field(default_factory=list)
    mutators: list[MutateHook] = field(default_factory=list)
    reducers: list[ReduceHook] = field(default_factory=list)

    # --------------------------------------------------------- registration

    def add_guard(self, hook: GuardHook) -> None:
        self.guards.append(hook)

    def add_mutator(self, hook: MutateHook) -> None:
        self.mutators.append(hook)

    def add_reducer(self, hook: ReduceHook) -> None:
        self.reducers.append(hook)

    # -------------------------------------------------------------- apply

    def apply_guards(self, proposal: MutationProposal) -> bool:
        return all(hook(proposal) for hook in self.guards)

    def apply_mutators(self, proposal: MutationProposal) -> MutationProposal:
        current = proposal
        for hook in self.mutators:
            current = hook(current)
        return current

    def apply_reducers(self, proposals: list[MutationProposal]) -> list[MutationProposal]:
        current = list(proposals)
        for hook in self.reducers:
            current = list(hook(current))
        return current
