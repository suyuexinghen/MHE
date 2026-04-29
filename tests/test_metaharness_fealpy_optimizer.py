from __future__ import annotations

import pytest

from metaharness.core.models import (
    PendingConnectionSet,
)
from metaharness.core.mutation import MutationProposal
from metaharness_ext.fealpy.contracts import (
    FealpyStudyAxis,
    FealpyStudyReport,
    FealpyStudyTrial,
)
from metaharness_ext.fealpy.optimizer import (
    FealpyDomainBrainProvider,
    FealpyProposalEvaluation,
    FealpyStudyObservation,
    _axis_values,
    _candidate_snapshots,
    _is_allowed_snapshot,
    _sanitize_snapshot,
    _snapshot_key,
)


def _make_trial(
    trial_id: str,
    metric_value: float | None = None,
    passed: bool = True,
    parameters: dict | None = None,
) -> FealpyStudyTrial:
    return FealpyStudyTrial(
        trial_id=trial_id,
        parameters=parameters or {},
        metric_value=metric_value,
        passed=passed,
    )


def _make_observation(
    trial_id: str,
    metric_value: float | None = None,
    passed: bool = True,
    *,
    params: dict[str, object] | None = None,
) -> FealpyStudyObservation:
    return FealpyStudyObservation(
        trial_id=trial_id,
        parameters=dict(params or {}),
        metric_value=metric_value,
        passed=passed,
    )


def _make_axes() -> list[FealpyStudyAxis]:
    return [
        FealpyStudyAxis(parameter_path="mesh.nx", values=[4, 8, 16]),
        FealpyStudyAxis(parameter_path="fe_degree", values=[1, 2]),
    ]


class TestObservationsFromStudy:
    def test_converts_trials(self):
        report = FealpyStudyReport(
            study_id="s1",
            trials=[
                _make_trial("t1", metric_value=0.01, parameters={"mesh.nx": 4}),
                _make_trial("t2", metric_value=0.005, parameters={"mesh.nx": 8}),
            ],
        )
        provider = FealpyDomainBrainProvider()
        obs = provider.observations_from_study(report)
        assert len(obs) == 2
        assert obs[0].trial_id == "t1"
        assert obs[0].metric_value == 0.01
        assert obs[0].parameters == {"mesh.nx": 4}

    def test_handles_empty(self):
        report = FealpyStudyReport(study_id="s1")
        provider = FealpyDomainBrainProvider()
        obs = provider.observations_from_study(report)
        assert obs == []


class TestPropose:
    def test_deterministic_returns_untried_snapshots(self):
        axes = _make_axes()
        observations = [_make_observation("t1", 0.01, params={"mesh.nx": 4, "fe_degree": 1})]
        provider = FealpyDomainBrainProvider()
        proposals = provider.propose(axes, observations, max_proposals=3)
        assert len(proposals) == 3
        for p in proposals:
            assert p.proposer_id == "fealpy_domain_brain"
            assert p.domain_payload["fealpy_parameter_proposal"] is True
            # None of the proposed snapshots should match the tried one
            params = p.domain_payload["parameters"]
            assert not (params.get("mesh.nx") == 4 and params.get("fe_degree") == 1)

    def test_respects_max_proposals(self):
        axes = _make_axes()
        provider = FealpyDomainBrainProvider()
        proposals = provider.propose(axes, [], max_proposals=2)
        assert len(proposals) == 2

    def test_filters_already_tried_snapshots(self):
        axes = _make_axes()
        # Mark 5 of 6 snapshots as tried
        tried_combos = [
            (4, 1),
            (4, 2),
            (8, 1),
            (8, 2),
            (16, 1),
        ]
        observations = [
            _make_observation(f"t{i}", 0.01, params={"mesh.nx": nx, "fe_degree": deg})
            for i, (nx, deg) in enumerate(tried_combos)
        ]
        provider = FealpyDomainBrainProvider()
        proposals = provider.propose(axes, observations, max_proposals=5)
        assert len(proposals) == 1
        p = proposals[0].domain_payload["parameters"]
        assert p["mesh.nx"] == 16 and p["fe_degree"] == 2

    def test_empty_when_all_tried(self):
        axes = _make_axes()
        observations = [
            _make_observation("t0", 0.01, params={"mesh.nx": nx, "fe_degree": deg})
            for nx in [4, 8, 16]
            for deg in [1, 2]
        ]
        provider = FealpyDomainBrainProvider()
        proposals = provider.propose(axes, observations, max_proposals=5)
        assert proposals == []

    def test_bayesian_falls_back_when_no_optimizer(self):
        axes = _make_axes()
        provider = FealpyDomainBrainProvider(strategy="bayesian")
        proposals = provider.propose(axes, [], max_proposals=3)
        assert len(proposals) == 3

    def test_llm_guided_returns_empty_when_no_optimizer(self):
        axes = _make_axes()
        provider = FealpyDomainBrainProvider(strategy="llm_guided")
        proposals = provider.propose(axes, [], max_proposals=3)
        assert proposals == []

    def test_invalid_strategy_raises_valueerror(self):
        axes = _make_axes()
        provider = FealpyDomainBrainProvider()
        with pytest.raises(ValueError, match="Unsupported fealpy optimizer strategy"):
            provider.propose(axes, [], strategy="invalid")  # type: ignore[arg-type]


class TestEvaluate:
    def test_minimize_scores_against_best(self):
        observations = [
            _make_observation("t1", 0.01),
            _make_observation("t2", 0.005),
            _make_observation("t3", 0.02),
        ]
        proposal = MutationProposal(
            proposal_id="p1",
            description="test",
            pending=PendingConnectionSet(),
            domain_payload={"fealpy_parameter_proposal": True, "parameters": {"mesh.nx": 8}},
        )
        provider = FealpyDomainBrainProvider()
        result = provider.evaluate(proposal, observations, goal="minimize")
        assert isinstance(result, FealpyProposalEvaluation)
        assert result.proposal_id == "p1"
        assert result.score > 0
        assert "best_observed=0.005" in result.reasons
        assert "typed_whitelist_parameter_proposal" in result.reasons

    def test_maximize_scores_against_best(self):
        observations = [
            _make_observation("t1", 0.01),
            _make_observation("t2", 0.05),
        ]
        proposal = MutationProposal(
            proposal_id="p2",
            description="test",
            pending=PendingConnectionSet(),
            domain_payload={"fealpy_parameter_proposal": True, "parameters": {}},
        )
        provider = FealpyDomainBrainProvider()
        result = provider.evaluate(proposal, observations, goal="maximize")
        assert result.score == 0.05
        assert "best_observed=0.05" in result.reasons

    def test_no_ready_observations_returns_zero(self):
        observations = [
            _make_observation("t1", passed=False),
            _make_observation("t2", metric_value=None, passed=True),
        ]
        proposal = MutationProposal(
            proposal_id="p3",
            description="test",
            pending=PendingConnectionSet(),
        )
        provider = FealpyDomainBrainProvider()
        result = provider.evaluate(proposal, observations)
        assert result.score == 0.0
        assert "no_ready_observations" in result.reasons


class TestCandidateSnapshots:
    def test_cartesian_product(self):
        axes = [
            FealpyStudyAxis(parameter_path="a", values=[1, 2]),
            FealpyStudyAxis(parameter_path="b", values=[3, 4]),
        ]
        snapshots = _candidate_snapshots(axes)
        assert len(snapshots) == 4
        keys = [_snapshot_key(s) for s in snapshots]
        assert len(set(keys)) == 4


class TestAxisValues:
    def test_from_explicit_values(self):
        axis = FealpyStudyAxis(parameter_path="x", values=[1, 2, 3])
        assert _axis_values(axis) == [1, 2, 3]

    def test_from_range_with_step(self):
        axis = FealpyStudyAxis(parameter_path="x", range=(0, 4), step=2)
        assert _axis_values(axis) == [0, 2, 4]

    def test_from_range_without_step_returns_midpoint(self):
        axis = FealpyStudyAxis(parameter_path="x", range=(0, 10))
        result = _axis_values(axis)
        assert len(result) == 1
        assert result[0] == 5.0

    def test_empty_for_no_values_and_no_range(self):
        axis = FealpyStudyAxis(parameter_path="x")
        assert _axis_values(axis) == []


class TestHelpers:
    def test_snapshot_key_is_deterministic(self):
        assert _snapshot_key({"b": 2, "a": 1}) == _snapshot_key({"a": 1, "b": 2})

    def test_snapshot_key_differs_for_different_values(self):
        assert _snapshot_key({"a": 1}) != _snapshot_key({"a": 2})

    def test_is_allowed_snapshot(self):
        assert _is_allowed_snapshot({"a": 1, "b": 2}, {"a", "b", "c"}) is True

    def test_is_allowed_snapshot_rejects_missing_path(self):
        assert _is_allowed_snapshot({"a": 1, "z": 2}, {"a", "b"}) is False

    def test_is_allowed_snapshot_rejects_empty(self):
        assert _is_allowed_snapshot({}, {"a"}) is False

    def test_sanitize_returns_none_for_tried(self):
        snapshot = {"a": 1}
        result = _sanitize_snapshot(snapshot, {"a"}, [snapshot], {_snapshot_key(snapshot)})
        assert result is None

    def test_sanitize_returns_dict_for_untried(self):
        snapshot = {"a": 1}
        result = _sanitize_snapshot(snapshot, {"a"}, [snapshot], set())
        assert result == snapshot
