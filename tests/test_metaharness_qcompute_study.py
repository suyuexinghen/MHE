from __future__ import annotations

from pathlib import Path

import pytest

from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.qcompute.contracts import (
    QComputeBackendSpec,
    QComputeCircuitSpec,
    QComputeExperimentSpec,
    QComputeStudyAxis,
    QComputeStudySpec,
)
from metaharness_ext.qcompute.study import (
    QComputeStudyComponent,
    _mutate_spec,
)


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
