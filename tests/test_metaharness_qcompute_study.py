from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.qcompute.contracts import (
    QComputeBackendSpec,
    QComputeCircuitSpec,
    QComputeExperimentSpec,
    QComputeRunArtifact,
    QComputeRunPlan,
    QComputeStudyAxis,
    QComputeStudySpec,
    QComputeValidationMetrics,
    QComputeValidationReport,
)
from metaharness_ext.qcompute.study import (
    FunctionalBrainProvider,
    QComputeStudyComponent,
    _generate_agentic,
    _generate_bayesian,
    _generate_grid,
    _mutate_spec,
    _schedule_trials,
)
from metaharness_ext.qcompute.types import QComputeValidationStatus


def _build_spec(**overrides) -> QComputeExperimentSpec:
    data: dict = {
        "task_id": "qcompute-study-base",
        "mode": "simulate",
        "backend": QComputeBackendSpec(platform="qiskit_aer", simulator=True, qubit_count=4),
        "circuit": QComputeCircuitSpec(
            ansatz="custom",
            num_qubits=2,
            openqasm=('OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; h q[0]; cx q[0],q[1];'),
        ),
        "noise": None,
        "shots": 64,
    }
    data.update(overrides)
    return QComputeExperimentSpec(**data)


def _build_study_spec(**overrides) -> QComputeStudySpec:
    template = _build_spec()
    axes = [QComputeStudyAxis(parameter_path="shots", values=[64, 128, 256])]
    data: dict = {
        "study_id": "study-1",
        "experiment_template": template,
        "axes": axes,
        "strategy": "grid",
        "objective": "fidelity",
    }
    data.update(overrides)
    return QComputeStudySpec(**data)


async def _activated_study(tmp_path: Path) -> QComputeStudyComponent:
    study = QComputeStudyComponent()
    await study.activate(ComponentRuntime(storage_path=tmp_path))
    return study


class _SleepyExecutor:
    def __init__(self) -> None:
        self._active = 0
        self.max_active = 0
        self._lock = threading.Lock()

    def execute_plan(self, plan: QComputeRunPlan) -> QComputeRunArtifact:
        with self._lock:
            self._active += 1
            self.max_active = max(self.max_active, self._active)
        try:
            time.sleep(0.02)
            return QComputeRunArtifact(
                artifact_id=f"{plan.plan_id}-artifact",
                plan_ref=plan.plan_id,
                backend_actual=plan.target_backend.platform,
                status="completed",
                raw_output_path=f"/tmp/{plan.plan_id}.json",
                shots_requested=plan.execution_params.shots,
                shots_completed=plan.execution_params.shots,
            )
        finally:
            with self._lock:
                self._active -= 1


class _ShotValidator:
    def validate_run(self, artifact, plan, environment_report) -> QComputeValidationReport:
        fidelity = plan.execution_params.shots / 1000
        return QComputeValidationReport(
            task_id=environment_report.task_id,
            plan_ref=plan.plan_id,
            artifact_ref=artifact.artifact_id,
            passed=True,
            status=QComputeValidationStatus.VALIDATED,
            metrics=QComputeValidationMetrics(
                fidelity=fidelity,
                circuit_depth_executed=1000 - plan.execution_params.shots,
            ),
            promotion_ready=True,
        )


@pytest.mark.asyncio
async def test_study_grid_search_runs_all_trials(tmp_path: Path) -> None:
    study = await _activated_study(tmp_path)
    spec = _build_study_spec(
        axes=[QComputeStudyAxis(parameter_path="shots", values=[64, 128, 256])],
    )

    report = study.run_study(spec)

    assert report.study_id == "study-1"
    assert len(report.trials) == 3
    for trial in report.trials:
        assert trial.trial_id.startswith("study-1-")
        assert trial.evidence_bundle is not None
        assert trial.parameter_snapshot is not None


@pytest.mark.asyncio
async def test_study_selects_best_fidelity(tmp_path: Path) -> None:
    study = await _activated_study(tmp_path)
    spec = _build_study_spec(
        axes=[QComputeStudyAxis(parameter_path="shots", values=[64, 256])],
        objective="fidelity",
    )

    report = study.run_study(spec)

    assert report.best_trial_id is not None
    best = next(t for t in report.trials if t.trial_id == report.best_trial_id)
    assert best.trajectory_score is not None


@pytest.mark.asyncio
async def test_study_pareto_front(tmp_path: Path) -> None:
    study = await _activated_study(tmp_path)
    spec = _build_study_spec(
        axes=[QComputeStudyAxis(parameter_path="shots", values=[64, 128, 256, 512])],
    )

    report = study.run_study(spec)

    assert len(report.trials) == 4
    assert len(report.pareto_front) >= 1
    for trial_id in report.pareto_front:
        assert any(t.trial_id == trial_id for t in report.trials)


@pytest.mark.asyncio
async def test_study_mutate_spec_shots() -> None:
    template = _build_spec(shots=64)
    mutated = _mutate_spec(template, {"shots": 512})

    assert mutated.shots == 512
    assert template.shots == 64


@pytest.mark.asyncio
async def test_study_mutate_spec_nested_path() -> None:
    template = _build_spec()
    mutated = _mutate_spec(template, {"circuit.transpiler_level": 3})

    assert mutated.circuit.transpiler_level == 3
    assert template.circuit.transpiler_level == 1


@pytest.mark.asyncio
async def test_study_report_structure(tmp_path: Path) -> None:
    study = await _activated_study(tmp_path)
    spec = _build_study_spec()

    report = study.run_study(spec)

    assert report.study_id == "study-1"
    assert isinstance(report.trials, list)
    assert len(report.trials) > 0
    assert report.pareto_front is not None
    assert isinstance(report.convergence_analysis, dict)
    assert "objective" in report.convergence_analysis
    assert report.convergence_analysis["objective"] == "fidelity"
    assert report.convergence_analysis["trial_count"] == len(report.trials)


@pytest.mark.asyncio
async def test_study_max_trials_limits_grid(tmp_path: Path) -> None:
    study = await _activated_study(tmp_path)
    spec = _build_study_spec(
        axes=[QComputeStudyAxis(parameter_path="shots", values=[64, 128, 256, 512])],
        max_trials=2,
    )

    report = study.run_study(spec)

    assert len(report.trials) == 2


@pytest.mark.asyncio
async def test_study_random_strategy(tmp_path: Path) -> None:
    study = await _activated_study(tmp_path)
    spec = _build_study_spec(
        axes=[QComputeStudyAxis(parameter_path="shots", values=[64, 128, 256])],
        strategy="random",
        max_trials=4,
    )

    report = study.run_study(spec)

    assert len(report.trials) == 4
    for trial in report.trials:
        assert "shots" in trial.parameter_snapshot
        assert trial.parameter_snapshot["shots"] in [64, 128, 256]


@pytest.mark.asyncio
async def test_study_parallel_workers_preserves_trial_order_and_best(tmp_path: Path) -> None:
    study = await _activated_study(tmp_path)
    spec = _build_study_spec(
        axes=[QComputeStudyAxis(parameter_path="shots", values=[64, 128, 256, 512])],
        parallel_workers=4,
    )
    executor = _SleepyExecutor()

    report = study.run_study(spec, executor=executor, validator=_ShotValidator())

    assert executor.max_active > 1
    assert [trial.parameter_snapshot["shots"] for trial in report.trials] == [64, 128, 256, 512]
    best = next(trial for trial in report.trials if trial.trial_id == report.best_trial_id)
    assert best.parameter_snapshot["shots"] == 512


@pytest.mark.asyncio
async def test_study_parallel_workers_one_remains_sequential(tmp_path: Path) -> None:
    study = await _activated_study(tmp_path)
    spec = _build_study_spec(
        axes=[QComputeStudyAxis(parameter_path="shots", values=[64, 128, 256])],
        parallel_workers=1,
    )
    executor = _SleepyExecutor()

    report = study.run_study(spec, executor=executor, validator=_ShotValidator())

    assert executor.max_active == 1
    assert [trial.parameter_snapshot["shots"] for trial in report.trials] == [64, 128, 256]


def test_study_bayesian_strategy_generates_trials() -> None:
    spec = _build_study_spec(
        axes=[QComputeStudyAxis(parameter_path="shots", values=[64, 128, 256])],
        strategy="bayesian",
    )

    grid = _generate_grid(spec)

    assert len(grid) == 3
    assert grid == [{"shots": 128}, {"shots": 256}, {"shots": 64}]


def test_study_bayesian_respects_max_trials() -> None:
    spec = _build_study_spec(
        axes=[QComputeStudyAxis(parameter_path="shots", values=[64, 128, 256, 512])],
        strategy="bayesian",
        max_trials=2,
    )

    grid = _generate_bayesian(spec)

    assert len(grid) == 2
    assert grid == [{"shots": 256}, {"shots": 512}]


def test_study_agentic_strategy() -> None:
    """Agentic strategy generates proposals via FunctionalBrainProvider."""
    brain = FunctionalBrainProvider(seed=42)
    axes = [QComputeStudyAxis(parameter_path="shots", values=[64, 128, 256])]

    # First call: random initialization
    proposals = brain.propose(axes, best_params=None, n_proposals=3)
    assert len(proposals) == 3
    for p in proposals:
        assert "shots" in p
        assert p["shots"] in [64, 128, 256]

    # Second call: perturbation of best params
    best = proposals[0]
    refined = brain.propose(axes, best_params=best, n_proposals=2)
    assert len(refined) == 2
    for params in refined:
        assert isinstance(params["shots"], int)


def test_study_agentic_generates_integer_shots() -> None:
    spec = _build_study_spec(
        axes=[QComputeStudyAxis(parameter_path="shots", values=[64, 128, 256])],
        strategy="agentic",
        max_trials=5,
    )

    grid = _generate_agentic(spec)

    assert len(grid) == 5
    for params in grid:
        assert isinstance(params["shots"], int)
        _mutate_spec(spec.experiment_template, params)


@pytest.mark.asyncio
async def test_study_agentic_runs_integer_shots(tmp_path: Path) -> None:
    study = await _activated_study(tmp_path)
    spec = _build_study_spec(
        axes=[QComputeStudyAxis(parameter_path="shots", values=[64, 128, 256])],
        strategy="agentic",
        max_trials=5,
    )

    report = study.run_study(spec, validator=_ShotValidator())

    assert len(report.trials) == 5
    for trial in report.trials:
        assert isinstance(trial.parameter_snapshot["shots"], int)


def test_study_agentic_respects_max_trials() -> None:
    """Agentic strategy does not exceed max_trials."""
    axes = [QComputeStudyAxis(parameter_path="shots", values=[64, 128, 256])]
    spec = _build_study_spec(
        axes=axes,
        strategy="agentic",
        max_trials=5,
    )

    grid = _generate_agentic(spec)
    assert len(grid) == 5
    for params in grid:
        assert "shots" in params


def test_study_quota_aware_scheduling_simulator_first() -> None:
    """When mixing sim + real backends, simulator trials run first."""
    axes = [
        QComputeStudyAxis(
            parameter_path="backend.platform",
            values=["qiskit_aer", "quafu", "qiskit_aer", "quafu"],
        ),
    ]
    spec = _build_study_spec(axes=axes, strategy="grid")

    grid = [
        {"backend.platform": "quafu"},
        {"backend.platform": "qiskit_aer"},
        {"backend.platform": "quafu"},
        {"backend.platform": "qiskit_aer"},
    ]
    scheduled = _schedule_trials(grid, spec)

    # All simulator trials should come first
    platforms = [p["backend.platform"] for p in scheduled]
    last_sim_idx = max(i for i, p in enumerate(platforms) if p == "qiskit_aer")
    first_real_idx = min(i for i, p in enumerate(platforms) if p == "quafu")
    assert last_sim_idx < first_real_idx


def test_study_quota_aware_no_reorder_single_backend() -> None:
    """When all trials use the same backend, order is preserved."""
    axes = [QComputeStudyAxis(parameter_path="shots", values=[64, 128, 256])]
    spec = _build_study_spec(axes=axes, strategy="grid")

    grid = [{"shots": 64}, {"shots": 128}, {"shots": 256}]
    scheduled = _schedule_trials(grid, spec)

    assert scheduled == grid
