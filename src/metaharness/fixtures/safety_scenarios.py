"""Evaluation scenarios for the safety chain."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class SafetyScenario:
    """Scenario description for a safety-chain evaluation run."""

    scenario_id: str
    description: str
    topology: str  # path fragment relative to examples/graphs, without extension
    proposal_mutation: dict[str, Any] = field(default_factory=dict)
    expected_outcome: str = "allow"  # "allow" | "reject:<gate>"
    context: dict[str, Any] = field(default_factory=dict)


def all_safety_scenarios() -> list[SafetyScenario]:
    """Canonical set of safety scenarios bundled with the tree."""

    return [
        SafetyScenario(
            scenario_id="L1-happy-path",
            description="A well-formed proposal passes Level 1 sandbox validation.",
            topology="minimal-happy-path",
            expected_outcome="allow",
        ),
        SafetyScenario(
            scenario_id="L1-missing-required-input",
            description="Proposal drops a required input, so Level 1 rejects it.",
            topology="minimal-happy-path",
            proposal_mutation={"drop_edges": ["c1"]},
            expected_outcome="reject:level_1_sandbox_validator",
        ),
        SafetyScenario(
            scenario_id="L2-shadow-divergence",
            description="Shadow run diverges from baseline, Level 2 rejects.",
            topology="minimal-happy-path",
            expected_outcome="reject:level_2_ab_shadow",
            context={"trials": [{"value": "a"}]},
        ),
        SafetyScenario(
            scenario_id="L3-policy-veto",
            description="Policy veto marks the proposal as non-compliant.",
            topology="minimal-happy-path",
            proposal_mutation={"force_invalid": True},
            expected_outcome="reject:level_3_policy_veto",
        ),
        SafetyScenario(
            scenario_id="L4-post-commit-rollback",
            description="Post-commit health probe fails, auto rollback engages.",
            topology="minimal-happy-path",
            expected_outcome="rollback",
        ),
    ]
