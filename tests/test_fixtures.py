"""Tests for evaluation fixtures."""

from __future__ import annotations

from metaharness.fixtures import (
    HotReloadScenario,
    OptimizerScenario,
    SafetyScenario,
    all_hot_reload_scenarios,
    all_optimizer_scenarios,
    all_safety_scenarios,
)


def test_safety_scenarios_all_have_required_fields() -> None:
    scenarios = all_safety_scenarios()
    assert scenarios
    assert all(isinstance(s, SafetyScenario) for s in scenarios)
    for scenario in scenarios:
        assert scenario.scenario_id.startswith("L")
        assert scenario.topology
        assert scenario.expected_outcome


def test_hot_reload_scenarios_cover_success_and_failure() -> None:
    scenarios = all_hot_reload_scenarios()
    assert scenarios
    kinds = {(s.expected_success, s.incoming_fails) for s in scenarios}
    assert (True, False) in kinds
    assert (False, True) in kinds
    assert all(isinstance(s, HotReloadScenario) for s in scenarios)


def test_optimizer_scenarios_have_known_peaks() -> None:
    scenarios = all_optimizer_scenarios()
    assert scenarios
    assert all(isinstance(s, OptimizerScenario) for s in scenarios)
    peaks = {s.scenario_id: s.expected_best for s in scenarios}
    assert peaks["OPT-single-peak"] == "hi"
    assert peaks["OPT-tight-budget"] == "d"
