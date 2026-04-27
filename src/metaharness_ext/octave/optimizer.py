from __future__ import annotations

import hashlib
from typing import Any

from pydantic import BaseModel, Field

from metaharness.core.models import (
    BudgetState,
    ConvergenceState,
    PendingConnectionSet,
    ScoredEvidence,
)
from metaharness.core.mutation import MutationProposal
from metaharness_ext.octave.contracts import OctaveStudyAxis, OctaveStudyReport


class OctaveStudyObservation(BaseModel):
    trial_id: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    metric_value: float | None = None
    passed: bool = False


class OctaveProposalEvaluation(BaseModel):
    proposal_id: str
    score: float
    reasons: list[str] = Field(default_factory=list)
    evidence: ScoredEvidence


class OctaveDomainBrainProvider:
    def __init__(self, *, proposer_id: str = "octave_domain_brain") -> None:
        self.proposer_id = proposer_id

    def observations_from_study(self, report: OctaveStudyReport) -> list[OctaveStudyObservation]:
        return [
            OctaveStudyObservation(
                trial_id=trial.trial_id,
                parameters=dict(trial.parameter_snapshot or trial.parameters),
                metric_value=trial.metric_value,
                passed=trial.passed,
            )
            for trial in report.trials
        ]

    def propose(
        self,
        axes: list[OctaveStudyAxis],
        observations: list[OctaveStudyObservation],
        *,
        max_proposals: int = 1,
    ) -> list[MutationProposal]:
        allowed_paths = {axis.path for axis in axes}
        tried = {tuple(sorted(observation.parameters.items())) for observation in observations}
        proposals: list[MutationProposal] = []
        for snapshot in _candidate_snapshots(axes):
            if any(path not in allowed_paths for path in snapshot):
                continue
            if tuple(sorted(snapshot.items())) in tried:
                continue
            proposals.append(self._proposal(snapshot))
            if len(proposals) >= max_proposals:
                break
        return proposals

    def evaluate(
        self,
        proposal: MutationProposal,
        observations: list[OctaveStudyObservation],
        *,
        goal: str = "minimize",
    ) -> OctaveProposalEvaluation:
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
            if proposed.get("octave_parameter_proposal"):
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
                reason="proposal evaluated against Octave study history",
            ),
            reasons=reasons,
            attributes={"proposal_id": proposal.proposal_id, "goal": goal},
        )
        return OctaveProposalEvaluation(
            proposal_id=proposal.proposal_id,
            score=score,
            reasons=reasons,
            evidence=evidence,
        )

    def _proposal(self, snapshot: dict[str, Any]) -> MutationProposal:
        digest = hashlib.sha256(repr(sorted(snapshot.items())).encode()).hexdigest()[:10]
        return MutationProposal(
            proposal_id=f"octave-param-{digest}",
            description="Propose Octave study parameter update",
            pending=PendingConnectionSet(),
            proposer_id=self.proposer_id,
            domain_payload={
                "octave_parameter_proposal": True,
                "parameters": snapshot,
                "whitelist_paths": sorted(snapshot),
                "justification": "deterministic untried Octave study parameter candidate",
            },
        )


def _candidate_snapshots(axes: list[OctaveStudyAxis]) -> list[dict[str, Any]]:
    snapshots: list[dict[str, Any]] = [{}]
    for axis in axes:
        values = _axis_values(axis)
        snapshots = [{**snapshot, axis.path: value} for snapshot in snapshots for value in values]
    return snapshots


def _axis_values(axis: OctaveStudyAxis) -> list[Any]:
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
