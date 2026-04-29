from __future__ import annotations

import pytest

from metaharness_ext.fealpy.contracts import (
    FealpyMeshSpec,
    FealpyProblemSpec,
    FealpyStudyAxis,
    FealpyStudySpec,
    FealpyStudyTrial,
)
from metaharness_ext.fealpy.study import (
    _build_convergence_analysis,
    _build_summary_metrics,
    _compute_drop_ratios,
    _compute_observed_order,
    _generate_parameter_snapshots,
    _mutate_task,
    _recommend_trial,
)


def _task_template() -> FealpyProblemSpec:
    return FealpyProblemSpec(
        task_id="study-test",
        pde_family="poisson",
        example_key=1,
        backend="numpy",
        mesh=FealpyMeshSpec(meshtype="tri", nx=8, ny=8),
        fe_degree=1,
    )


def _study_spec(**overrides) -> FealpyStudySpec:
    defaults = {
        "study_id": "conv-study-1",
        "task_template": _task_template(),
        "axes": [
            FealpyStudyAxis(parameter_path="mesh.nx", values=[4, 8, 16]),
            FealpyStudyAxis(parameter_path="fe_degree", values=[1, 2]),
        ],
        "objective": "l2_error",
        "goal": "minimize",
    }
    defaults.update(overrides)
    return FealpyStudySpec(**defaults)


# ── Parameter snapshot generation ──────────────────────────────────────


def test_generate_snapshots_from_values() -> None:
    spec = _study_spec()
    snapshots = _generate_parameter_snapshots(spec)

    assert len(snapshots) == 6  # 3 mesh sizes × 2 degrees
    expected_keys = {"mesh.nx", "fe_degree"}
    for snapshot in snapshots:
        assert set(snapshot.keys()) == expected_keys

    nx_values = {s["mesh.nx"] for s in snapshots}
    assert nx_values == {4, 8, 16}


def test_generate_snapshots_from_range() -> None:
    spec = _study_spec(
        axes=[
            FealpyStudyAxis(parameter_path="mesh.nx", range=(2.0, 6.0), step=2.0),
        ]
    )
    snapshots = _generate_parameter_snapshots(spec)

    nx_values = {s["mesh.nx"] for s in snapshots}
    assert 2.0 in nx_values
    assert 4.0 in nx_values
    assert 6.0 in nx_values
    assert len(snapshots) == 3


def test_generate_snapshots_single_axis() -> None:
    spec = _study_spec(axes=[FealpyStudyAxis(parameter_path="backend", values=["numpy"])])
    snapshots = _generate_parameter_snapshots(spec)
    assert len(snapshots) == 1
    assert snapshots[0] == {"backend": "numpy"}


def test_generate_snapshots_empty_axes() -> None:
    spec = _study_spec(axes=[])
    snapshots = _generate_parameter_snapshots(spec)
    assert snapshots == []


# ── Task mutation ──────────────────────────────────────────────────────


def test_mutate_task_nested_path() -> None:
    task = _task_template()
    mutated = _mutate_task(task, {"mesh.nx": 32, "fe_degree": 3})

    assert mutated.mesh.nx == 32
    assert mutated.fe_degree == 3
    assert mutated.task_id != task.task_id
    assert "mesh_nx=32" in mutated.task_id
    assert "fe_degree=3" in mutated.task_id


def test_mutate_task_shallow_path() -> None:
    task = _task_template()
    mutated = _mutate_task(task, {"backend": "pytorch"})

    assert mutated.backend == "pytorch"
    assert "backend=pytorch" in mutated.task_id


def test_mutate_task_preserves_original() -> None:
    task = _task_template()
    original_nx = task.mesh.nx
    _mutate_task(task, {"mesh.nx": 64})

    assert task.mesh.nx == original_nx  # original unchanged


# ── Trial recommendation ───────────────────────────────────────────────


def _trial(trial_id: str, metric_value: float, passed: bool = True) -> FealpyStudyTrial:
    return FealpyStudyTrial(
        trial_id=trial_id,
        parameters={"mesh.nx": 8},
        metric_value=metric_value,
        passed=passed,
    )


def test_recommend_best_minimize() -> None:
    trials = [
        _trial("t1", 0.01),
        _trial("t2", 0.001),
        _trial("t3", 0.1),
    ]
    best = _recommend_trial(trials, goal="minimize")
    assert best is not None
    assert best.trial_id == "t2"


def test_recommend_best_maximize() -> None:
    trials = [
        _trial("t1", 0.5),
        _trial("t2", 0.9),
        _trial("t3", 0.1),
    ]
    best = _recommend_trial(trials, goal="maximize")
    assert best is not None
    assert best.trial_id == "t2"


def test_recommend_skips_failed() -> None:
    trials = [
        _trial("t1", 0.001, passed=False),
        _trial("t2", 0.01, passed=True),
    ]
    best = _recommend_trial(trials, goal="minimize")
    assert best is not None
    assert best.trial_id == "t2"


def test_recommend_no_valid_trials() -> None:
    trials = [
        _trial("t1", 0.01, passed=False),
        _trial("t2", 0.001, passed=False),
    ]
    best = _recommend_trial(trials, goal="minimize")
    assert best is None


# ── Convergence analysis ───────────────────────────────────────────────


def test_convergence_analysis() -> None:
    trials = [
        _trial("t1", 0.1),
        _trial("t2", 0.01),
        _trial("t3", 0.001),
    ]
    analysis = _build_convergence_analysis(trials, "l2_error", "minimize")

    assert analysis["trial_count"] == 3
    assert analysis["ready_count"] == 3
    assert analysis["best_score"] == 0.001
    assert analysis["worst_score"] == 0.1
    assert analysis["score_range"] > 0


def test_convergence_analysis_no_ready() -> None:
    trials = [_trial("t1", 0.01, passed=False)]
    analysis = _build_convergence_analysis(trials, "l2_error", "minimize")

    assert analysis["ready_count"] == 0
    assert "best_score" not in analysis


def test_drop_ratios_decreasing() -> None:
    """Successive decreasing metric values produce drop ratios < 1."""
    trials = [
        _trial("t1", 0.1),
        _trial("t2", 0.05),
        _trial("t3", 0.01),
    ]
    ratios = _compute_drop_ratios(trials)
    assert len(ratios) == 2
    assert ratios[0] == pytest.approx(0.5)  # 0.05 / 0.1
    assert ratios[1] == pytest.approx(0.2)  # 0.01 / 0.05


def test_drop_ratios_too_few_trials() -> None:
    """Fewer than 2 valid trials produce an empty list."""
    assert _compute_drop_ratios([]) == []
    assert _compute_drop_ratios([_trial("t1", 0.1)]) == []


def test_drop_ratios_skips_failed() -> None:
    """Failed trials are excluded from drop ratio computation."""
    trials = [
        _trial("t1", 0.1),
        _trial("t2", 0.01, passed=False),
        _trial("t3", 0.05),
    ]
    ratios = _compute_drop_ratios(trials)
    assert ratios == [0.5]  # only t1→t3


def test_observed_order_from_doubling_mesh() -> None:
    """Halving element size → expected order ~2 for P1."""
    trials = [
        _trial("t1", 0.04),  # h
        _trial("t2", 0.01),  # h/2 → error drops by 4×
    ]
    order = _compute_observed_order(trials)
    assert order is not None
    assert 1.5 < order < 2.5


def test_observed_order_insufficient() -> None:
    """Less than 2 valid trials returns None."""
    assert _compute_observed_order([]) is None
    assert _compute_observed_order([_trial("t1", 0.1)]) is None


def test_convergence_analysis_includes_drop_ratios_and_order() -> None:
    trials = [
        _trial("t1", 0.1),
        _trial("t2", 0.01),
        _trial("t3", 0.001),
    ]
    analysis = _build_convergence_analysis(trials, "l2_error", "minimize")
    assert "drop_ratios" in analysis
    assert "observed_order" in analysis
    assert len(analysis["drop_ratios"]) == 2


# ── Summary metrics ────────────────────────────────────────────────────


def test_build_summary_metrics() -> None:
    trials = [
        _trial("t1", 0.01),
        _trial("t2", 0.001),
    ]
    best = _trial("t2", 0.001)
    summary = _build_summary_metrics(trials, "l2_error", best)

    assert summary["trial_count"] == 2
    assert summary["ready_count"] == 2
    assert summary["best_l2_error"] == 0.001


def test_build_summary_metrics_no_best() -> None:
    summary = _build_summary_metrics([], "l2_error", None)

    assert summary["trial_count"] == 0
    assert summary["ready_count"] == 0
