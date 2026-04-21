"""Evaluation fixtures for Meta-Harness subsystems.

These fixtures are *scenarios* used by the evaluation harness
(`scripts/eval.py`) to exercise the safety chain, hot-reload
orchestration, and optimizer loop against known-good workloads.
They are *not* pytest fixtures - they are plain data objects that
tests, benchmarks, and documentation can all share.
"""

from metaharness.fixtures.hot_reload_scenarios import (
    HotReloadScenario,
    all_hot_reload_scenarios,
)
from metaharness.fixtures.optimizer_scenarios import (
    OptimizerScenario,
    all_optimizer_scenarios,
)
from metaharness.fixtures.safety_scenarios import (
    SafetyScenario,
    all_safety_scenarios,
)

__all__ = [
    "HotReloadScenario",
    "OptimizerScenario",
    "SafetyScenario",
    "all_hot_reload_scenarios",
    "all_optimizer_scenarios",
    "all_safety_scenarios",
]
