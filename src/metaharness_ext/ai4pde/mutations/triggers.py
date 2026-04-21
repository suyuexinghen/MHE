from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from metaharness_ext.ai4pde.contracts import (
    BudgetRecord,
    ScientificEvidenceBundle,
    ValidationBundle,
)


class MutationSignal(BaseModel):
    signal: Literal[
        "repeated_partial",
        "benchmark_plateau",
        "repeated_failure_family",
        "baseline_divergence_widening",
        "cost_too_high",
    ]
    severity: str
    reason: str


def evaluate_triggers(
    *,
    validation_bundle: ValidationBundle,
    evidence_bundle: ScientificEvidenceBundle,
    budget: BudgetRecord,
    repeated_partial_count: int = 0,
    plateau_detected: bool = False,
    repeated_failure_count: int = 0,
) -> list[MutationSignal]:
    signals: list[MutationSignal] = []
    if repeated_partial_count >= 2 or validation_bundle.next_action.value == "retry":
        signals.append(
            MutationSignal(
                signal="repeated_partial",
                severity="medium",
                reason="validation requests retry or partial outcomes are repeating",
            )
        )
    if plateau_detected:
        signals.append(
            MutationSignal(
                signal="benchmark_plateau",
                severity="medium",
                reason="benchmark progress has plateaued",
            )
        )
    if repeated_failure_count >= 2 or bool(validation_bundle.violations):
        signals.append(
            MutationSignal(
                signal="repeated_failure_family",
                severity="high",
                reason="violations or failure family repeats across runs",
            )
        )
    if validation_bundle.reference_comparison.get("status") == "worse_than_baseline":
        signals.append(
            MutationSignal(
                signal="baseline_divergence_widening",
                severity="high",
                reason="candidate path diverges from baseline",
            )
        )
    if budget.gpu_hours > 8.0 or budget.hpc_quota > 1.0:
        signals.append(
            MutationSignal(
                signal="cost_too_high",
                severity="high",
                reason="budget consumption exceeds green/yellow envelope",
            )
        )
    if evidence_bundle.graph_metadata.get("graph_family") == "ai4pde-minimal" and not signals:
        return []
    return signals
