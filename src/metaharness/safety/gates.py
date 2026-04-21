"""Generic safety gate contract.

Every level in the four-tier safety chain implements :class:`SafetyGate`
and returns a :class:`GateResult`. The :mod:`metaharness.safety.pipeline`
wires them together in strict order.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol

from metaharness.core.mutation import MutationProposal


class GateDecision(str, Enum):
    """Outcome of a single safety-gate evaluation."""

    ALLOW = "allow"
    REJECT = "reject"
    DEFER = "defer"


@dataclass(slots=True)
class GateResult:
    """Result object returned by a :class:`SafetyGate`."""

    gate: str
    decision: GateDecision
    reason: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)

    @property
    def allowed(self) -> bool:
        return self.decision == GateDecision.ALLOW


class SafetyGate(Protocol):
    """Protocol for a single safety-chain level.

    Implementations must be deterministic given the same ``proposal`` and
    ``context`` mapping. The pipeline invokes them in the documented order
    and short-circuits on the first rejection.
    """

    name: str

    def evaluate(
        self, proposal: MutationProposal, context: dict[str, Any] | None = None
    ) -> GateResult: ...
