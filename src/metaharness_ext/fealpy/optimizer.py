from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from typing import Any, Literal

from pydantic import BaseModel, Field

from metaharness.core.models import (
    BudgetState,
    ConvergenceState,
    PendingConnectionSet,
    ScoredEvidence,
)
from metaharness.core.mutation import MutationProposal
from metaharness_ext.fealpy.contracts import FealpyStudyAxis, FealpyStudyReport

FealpyOptimizerStrategy = Literal["deterministic", "bayesian", "llm_guided"]

FealpySnapshotOptimizer = Callable[
    [list[dict[str, Any]], list["FealpyStudyObservation"]], list[dict[str, Any]]
]


class FealpyStudyObservation(BaseModel):
    trial_id: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    metric_value: float | None = None
    passed: bool = False


class FealpyProposalEvaluation(BaseModel):
    proposal_id: str
    score: float
    reasons: list[str] = Field(default_factory=list)
    evidence: ScoredEvidence


class FealpyDomainBrainProvider:
    def __init__(
        self,
        *,
        proposer_id: str = "fealpy_domain_brain",
        strategy: FealpyOptimizerStrategy = "deterministic",
        bayesian_optimizer: FealpySnapshotOptimizer | None = None,
        llm_guided_optimizer: FealpySnapshotOptimizer | None = None,
    ) -> None:
        self.proposer_id = proposer_id
        self.strategy = strategy
        self.bayesian_optimizer = bayesian_optimizer
        self.llm_guided_optimizer = llm_guided_optimizer

    def observations_from_study(self, report: FealpyStudyReport) -> list[FealpyStudyObservation]:
        return [
            FealpyStudyObservation(
                trial_id=trial.trial_id,
                parameters=dict(trial.parameters),
                metric_value=trial.metric_value,
                passed=trial.passed,
            )
            for trial in report.trials
        ]

    def propose(
        self,
        axes: list[FealpyStudyAxis],
        observations: list[FealpyStudyObservation],
        *,
        max_proposals: int = 1,
        strategy: FealpyOptimizerStrategy | None = None,
    ) -> list[MutationProposal]:
        selected_strategy = strategy or self.strategy
        allowed_paths = {axis.parameter_path for axis in axes}
        tried = {_snapshot_key(observation.parameters) for observation in observations}
        candidates = [
            snapshot
            for snapshot in _candidate_snapshots(axes)
            if _is_allowed_snapshot(snapshot, allowed_paths)
            and _snapshot_key(snapshot) not in tried
        ]
        ordered = self._ordered_candidates(selected_strategy, candidates, observations)
        proposals: list[MutationProposal] = []
        for snapshot in ordered:
            sanitized = _sanitize_snapshot(snapshot, allowed_paths, candidates, tried)
            if sanitized is None:
                continue
            proposals.append(self._proposal(sanitized, strategy=selected_strategy))
            tried.add(_snapshot_key(sanitized))
            if len(proposals) >= max_proposals:
                break
        return proposals

    def evaluate(
        self,
        proposal: MutationProposal,
        observations: list[FealpyStudyObservation],
        *,
        goal: str = "minimize",
    ) -> FealpyProposalEvaluation:
        metrics = [
            observation.metric_value
            for observation in observations
            if observation.passed and observation.metric_value is not None
        ]
        score = 0.0
        reasons: list[str] = []
        if metrics:
            best = min(metrics) if goal == "minimize" else max(metrics)
            proposed = proposal.domain_payload or {}
            score = 1.0 / (1.0 + abs(float(best))) if goal == "minimize" else float(best)
            reasons.append(f"best_observed={best}")
            if proposed.get("fealpy_parameter_proposal"):
                reasons.append("typed_whitelist_parameter_proposal")
        else:
            reasons.append("no_ready_observations")
        evidence = ScoredEvidence(
            score=score,
            metrics={"ready_observations": float(len(metrics))},
            budget=BudgetState(used=len(observations), exhausted=False),
            convergence=ConvergenceState(
                converged=False,
                criteria_met=["observations_available"] if metrics else [],
                reason="proposal evaluated against fealpy study history",
            ),
            reasons=reasons,
            attributes={"proposal_id": proposal.proposal_id, "goal": goal},
        )
        return FealpyProposalEvaluation(
            proposal_id=proposal.proposal_id,
            score=score,
            reasons=reasons,
            evidence=evidence,
        )

    def _ordered_candidates(
        self,
        strategy: FealpyOptimizerStrategy,
        candidates: list[dict[str, Any]],
        observations: list[FealpyStudyObservation],
    ) -> list[dict[str, Any]]:
        if strategy == "deterministic":
            return candidates
        if strategy == "bayesian":
            if self.bayesian_optimizer is None:
                return candidates
            return [*self.bayesian_optimizer(candidates, observations), *candidates]
        if strategy == "llm_guided":
            if self.llm_guided_optimizer is None:
                return []
            return [*self.llm_guided_optimizer(candidates, observations), *candidates]
        raise ValueError(f"Unsupported fealpy optimizer strategy: {strategy}")

    def _proposal(
        self, snapshot: dict[str, Any], *, strategy: FealpyOptimizerStrategy
    ) -> MutationProposal:
        digest = hashlib.sha256(repr(sorted(snapshot.items())).encode()).hexdigest()[:10]
        return MutationProposal(
            proposal_id=f"fealpy-param-{digest}",
            description="Propose fealpy study parameter update",
            pending=PendingConnectionSet(),
            proposer_id=self.proposer_id,
            domain_payload={
                "fealpy_parameter_proposal": True,
                "strategy": strategy,
                "parameters": snapshot,
                "whitelist_paths": sorted(snapshot),
                "justification": f"{strategy} untried fealpy study parameter candidate",
            },
        )


def _candidate_snapshots(axes: list[FealpyStudyAxis]) -> list[dict[str, Any]]:
    snapshots: list[dict[str, Any]] = [{}]
    for axis in axes:
        values = _axis_values(axis)
        snapshots = [
            {**snapshot, axis.parameter_path: value} for snapshot in snapshots for value in values
        ]
    return snapshots


def _sanitize_snapshot(
    snapshot: dict[str, Any],
    allowed_paths: set[str],
    candidates: list[dict[str, Any]],
    tried: set[str],
) -> dict[str, Any] | None:
    candidate_keys = {_snapshot_key(candidate) for candidate in candidates}
    key = _snapshot_key(snapshot)
    if (
        key not in candidate_keys
        or key in tried
        or not _is_allowed_snapshot(snapshot, allowed_paths)
    ):
        return None
    return dict(snapshot)


def _is_allowed_snapshot(snapshot: dict[str, Any], allowed_paths: set[str]) -> bool:
    return bool(snapshot) and all(path in allowed_paths for path in snapshot)


def _snapshot_key(snapshot: dict[str, Any]) -> str:
    return json.dumps(snapshot, sort_keys=True, separators=(",", ":"), default=repr)


def _axis_values(axis: FealpyStudyAxis) -> list[Any]:
    if axis.values:
        return list(axis.values)
    if axis.range is None:
        return []
    lo, hi = axis.range
    if axis.step is None:
        return [(lo + hi) / 2.0]
    values: list[float] = []
    current = lo
    while current <= hi + 1e-12:
        values.append(current)
        current += axis.step
    return values
