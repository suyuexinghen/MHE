from __future__ import annotations

from pathlib import Path

import pytest

from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.nektar.contracts import (
    ConvergenceStudySpec,
    FilterOutputSummary,
    NektarMutationAxis,
    NektarProblemSpec,
    NektarRunArtifact,
    NektarValidationReport,
)
from metaharness_ext.nektar.convergence import ConvergenceStudyComponent
from metaharness_ext.nektar.types import NektarSolverFamily


class _FakeExecutor:
    def __init__(self) -> None:
        self.calls: list[int] = []

    def execute_plan(self, plan) -> NektarRunArtifact:
        self.calls.append(int(plan.parameters["NumModes"]))
        run_dir = Path(plan.task_id)
        solver_log = run_dir / "solver.log"
        solver_log.parent.mkdir(parents=True, exist_ok=True)
        solver_log.write_text(
            "Steps: 10       Time: 0.1          CPU Time: 0.05s\n"
            f"L 2 error (variable u) : {1 / int(plan.parameters['NumModes']):.6f}\n"
        )
        field_file = run_dir / "solution.fld"
        field_file.write_text("fld")
        return NektarRunArtifact(
            run_id=f"run::{plan.task_id}",
            task_id=plan.task_id,
            solver_family=plan.solver_family,
            solver_binary=plan.solver_binary,
            session_files=[str(run_dir / "session.xml")],
            field_files=[str(field_file)],
            log_files=[str(solver_log)],
            filter_output=FilterOutputSummary(
                error_norms={"l2_error_u": 1 / int(plan.parameters["NumModes"])},
                metrics={"total_steps": 10},
            ),
            result_summary={"exit_code": 0},
            status="completed",
        )


class _MetricExecutor:
    def __init__(self, metrics: dict[int, float]) -> None:
        self.metrics = metrics
        self.calls: list[int] = []

    def execute_plan(self, plan) -> NektarRunArtifact:
        value = int(plan.parameters["NumModes"])
        metric = self.metrics[value]
        self.calls.append(value)
        run_dir = Path(plan.task_id)
        solver_log = run_dir / "solver.log"
        solver_log.parent.mkdir(parents=True, exist_ok=True)
        solver_log.write_text(
            "Steps: 10       Time: 0.1          CPU Time: 0.05s\n"
            f"L 2 error (variable u) : {metric:.6f}\n"
        )
        field_file = run_dir / "solution.fld"
        field_file.write_text("fld")
        return NektarRunArtifact(
            run_id=f"run::{plan.task_id}",
            task_id=plan.task_id,
            solver_family=plan.solver_family,
            solver_binary=plan.solver_binary,
            session_files=[str(run_dir / "session.xml")],
            field_files=[str(field_file)],
            log_files=[str(solver_log)],
            filter_output=FilterOutputSummary(error_norms={"l2_error_u": metric}, metrics={"total_steps": 10}),
            result_summary={"exit_code": 0},
            status="completed",
        )


class _FakePostprocessor:
    def run_postprocess(self, run: NektarRunArtifact) -> NektarRunArtifact:
        derived = Path(run.task_id) / "solution.vtu"
        derived.write_text("vtu")
        updated = run.model_copy(deep=True)
        updated.derived_files.append(str(derived))
        updated.result_summary["postprocess"] = {"status": "completed"}
        return updated


class _FakeValidator:
    def validate_run(self, run: NektarRunArtifact) -> NektarValidationReport:
        metric = float(run.filter_output.error_norms.get("l2_error_u", 99.0))
        passed = metric <= 0.2
        return NektarValidationReport(
            task_id=run.task_id,
            passed=passed,
            solver_exited_cleanly=True,
            field_files_exist=True,
            error_vs_reference=passed,
            messages=["validated"],
            metrics={"l2_error_u": metric},
        )


class _RaisingExecutor:
    def execute_plan(self, plan) -> NektarRunArtifact:
        raise RuntimeError("compile chain failed")


def _base_problem(task_id: str) -> NektarProblemSpec:
    return NektarProblemSpec(
        task_id=task_id,
        title="helmholtz",
        solver_family=NektarSolverFamily.ADR,
        dimension=2,
        variables=["u"],
    )


@pytest.mark.asyncio
async def test_convergence_study_absolute_rule_sweeps_nummodes_without_persisting_report(
    tmp_path: Path,
) -> None:
    component = ConvergenceStudyComponent()
    await component.activate(ComponentRuntime(storage_path=tmp_path))
    executor = _FakeExecutor()
    postprocessor = _FakePostprocessor()
    validator = _FakeValidator()
    spec = ConvergenceStudySpec(
        study_id="study-1",
        task_id="task-1",
        base_problem=_base_problem("task-1"),
        axis=NektarMutationAxis(kind="num_modes", values=[2, 4, 8]),
        metric_key="l2_error_u",
        target_tolerance=0.2,
        min_points=3,
    )

    report = component.run_study(
        spec,
        executor=executor,
        postprocessor=postprocessor,
        validator=validator,
    )

    assert executor.calls == [2, 4, 8]
    assert [trial.axis_value for trial in report.trials] == [2, 4, 8]
    assert report.recommended_value == 8
    assert report.converged is True
    assert report.recommended_reason is not None
    assert report.error_sequence == pytest.approx([0.5, 0.25, 0.125])
    persisted = tmp_path / "nektar_runs" / "task-1" / "studies" / "study-1.json"
    assert not persisted.exists()


@pytest.mark.asyncio
async def test_convergence_study_absolute_rule_requires_target_tolerance(tmp_path: Path) -> None:
    component = ConvergenceStudyComponent()
    await component.activate(ComponentRuntime(storage_path=tmp_path))

    spec = ConvergenceStudySpec(
        study_id="study-bad",
        task_id="task-bad",
        base_problem=_base_problem("task-bad"),
        axis=NektarMutationAxis(kind="num_modes", values=[2, 4, 8]),
        metric_key="l2_error_u",
        min_points=3,
    )

    with pytest.raises(ValueError, match="target_tolerance"):
        component.run_study(
            spec,
            executor=_FakeExecutor(),
            postprocessor=_FakePostprocessor(),
            validator=_FakeValidator(),
        )


@pytest.mark.asyncio
async def test_convergence_study_relative_drop_stops_on_first_match(tmp_path: Path) -> None:
    component = ConvergenceStudyComponent()
    await component.activate(ComponentRuntime(storage_path=tmp_path))
    executor = _MetricExecutor({2: 1.0, 4: 0.7, 8: 0.3})
    spec = ConvergenceStudySpec(
        study_id="study-relative",
        task_id="task-relative",
        base_problem=_base_problem("task-relative"),
        axis=NektarMutationAxis(kind="num_modes", values=[2, 4, 8]),
        metric_key="l2_error_u",
        convergence_rule="relative_drop",
        relative_drop_ratio=0.5,
        min_points=3,
        stop_on_first_pass=True,
        target_tolerance=0.2,
    )

    report = component.run_study(
        spec,
        executor=executor,
        postprocessor=_FakePostprocessor(),
        validator=_FakeValidator(),
    )

    assert executor.calls == [2, 4, 8]
    assert report.recommended_value == 8
    assert report.converged is True
    assert report.drop_ratios == pytest.approx([0.7, 0.4285714286])


@pytest.mark.asyncio
async def test_convergence_study_relative_drop_falls_back_when_threshold_not_met(tmp_path: Path) -> None:
    component = ConvergenceStudyComponent()
    await component.activate(ComponentRuntime(storage_path=tmp_path))
    executor = _MetricExecutor({2: 1.0, 4: 0.8, 8: 0.7})
    spec = ConvergenceStudySpec(
        study_id="study-relative-fallback",
        task_id="task-relative-fallback",
        base_problem=_base_problem("task-relative-fallback"),
        axis=NektarMutationAxis(kind="num_modes", values=[2, 4, 8]),
        metric_key="l2_error_u",
        convergence_rule="relative_drop",
        relative_drop_ratio=0.5,
        min_points=3,
        target_tolerance=0.2,
    )

    report = component.run_study(
        spec,
        executor=executor,
        postprocessor=_FakePostprocessor(),
        validator=_FakeValidator(),
    )

    assert report.recommended_value == 8
    assert report.converged is False
    assert report.recommended_reason == (
        "No adjacent trial pair met the relative_drop threshold; using the best available metric."
    )


@pytest.mark.asyncio
async def test_convergence_study_plateau_detects_stable_drop_ratio(tmp_path: Path) -> None:
    component = ConvergenceStudyComponent()
    await component.activate(ComponentRuntime(storage_path=tmp_path))
    executor = _MetricExecutor({2: 1.0, 4: 0.4, 8: 0.168})
    spec = ConvergenceStudySpec(
        study_id="study-plateau",
        task_id="task-plateau",
        base_problem=_base_problem("task-plateau"),
        axis=NektarMutationAxis(kind="num_modes", values=[2, 4, 8]),
        metric_key="l2_error_u",
        convergence_rule="plateau",
        plateau_tolerance=0.03,
        min_points=3,
        target_tolerance=0.2,
    )

    report = component.run_study(
        spec,
        executor=executor,
        postprocessor=_FakePostprocessor(),
        validator=_FakeValidator(),
    )

    assert report.recommended_value == 8
    assert report.converged is True
    assert report.drop_ratios == pytest.approx([0.4, 0.42])
    assert report.recommended_reason is not None


@pytest.mark.asyncio
async def test_convergence_study_plateau_rejects_nonmonotone_series(tmp_path: Path) -> None:
    component = ConvergenceStudyComponent()
    await component.activate(ComponentRuntime(storage_path=tmp_path))
    executor = _MetricExecutor({2: 1.0, 4: 0.6, 8: 0.8})
    spec = ConvergenceStudySpec(
        study_id="study-plateau-fallback",
        task_id="task-plateau-fallback",
        base_problem=_base_problem("task-plateau-fallback"),
        axis=NektarMutationAxis(kind="num_modes", values=[2, 4, 8]),
        metric_key="l2_error_u",
        convergence_rule="plateau",
        plateau_tolerance=0.1,
        min_points=3,
        target_tolerance=0.2,
    )

    report = component.run_study(
        spec,
        executor=executor,
        postprocessor=_FakePostprocessor(),
        validator=_FakeValidator(),
    )

    assert report.recommended_value == 4
    assert report.converged is False
    assert report.recommended_reason == (
        "Metric sequence is not monotone non-increasing; plateau was not evaluated."
    )


@pytest.mark.asyncio
async def test_convergence_trial_includes_analyzer_outputs_and_observed_order(tmp_path: Path) -> None:
    component = ConvergenceStudyComponent()
    await component.activate(ComponentRuntime(storage_path=tmp_path))
    spec = ConvergenceStudySpec(
        study_id="study-analysis",
        task_id="task-analysis",
        base_problem=_base_problem("task-analysis"),
        axis=NektarMutationAxis(kind="num_modes", values=[2, 4, 8]),
        metric_key="l2_error_u",
        target_tolerance=0.2,
        min_points=3,
    )

    report = component.run_study(
        spec,
        executor=_FakeExecutor(),
        postprocessor=_FakePostprocessor(),
        validator=_FakeValidator(),
    )

    trial = report.trials[0]
    assert trial.solver_log_analysis.exists is True
    assert trial.filter_output_analysis.has_vtu is True
    assert trial.error_summary.status == "reference_error_exceeds_tolerance"
    assert trial.metric_value == pytest.approx(0.5)
    assert report.observed_order is not None


@pytest.mark.asyncio
async def test_convergence_study_handles_trial_failure_without_crashing(tmp_path: Path) -> None:
    component = ConvergenceStudyComponent()
    await component.activate(ComponentRuntime(storage_path=tmp_path))
    spec = ConvergenceStudySpec(
        study_id="study-fail",
        task_id="task-fail",
        base_problem=_base_problem("task-fail"),
        axis=NektarMutationAxis(kind="num_modes", values=[2, 4, 8]),
        metric_key="l2_error_u",
        target_tolerance=0.2,
        min_points=3,
    )

    report = component.run_study(
        spec,
        executor=_RaisingExecutor(),
        postprocessor=_FakePostprocessor(),
        validator=_FakeValidator(),
    )

    assert len(report.trials) == 3
    assert all(trial.status == "failed" for trial in report.trials)
    assert report.recommended_value == 8
    assert report.converged is False
    assert report.observed_order is None


@pytest.mark.asyncio
async def test_convergence_study_applies_postprocess_override(tmp_path: Path) -> None:
    component = ConvergenceStudyComponent()
    await component.activate(ComponentRuntime(storage_path=tmp_path))

    class _CaptureExecutor(_FakeExecutor):
        def __init__(self) -> None:
            super().__init__()
            self.postprocess_plans: list[list[dict[str, object]]] = []

        def execute_plan(self, plan) -> NektarRunArtifact:
            self.postprocess_plans.append(plan.postprocess_plan)
            return super().execute_plan(plan)

    executor = _CaptureExecutor()
    spec = ConvergenceStudySpec(
        study_id="study-override",
        task_id="task-override",
        base_problem=_base_problem("task-override"),
        axis=NektarMutationAxis(kind="num_modes", values=[2, 4, 8]),
        metric_key="l2_error_u",
        target_tolerance=0.2,
        min_points=3,
        postprocess_plan_override=[{"type": "fieldconvert", "output": "custom.vtu"}],
    )

    component.run_study(
        spec,
        executor=executor,
        postprocessor=_FakePostprocessor(),
        validator=_FakeValidator(),
    )

    assert executor.postprocess_plans[0] == [{"type": "fieldconvert", "output": "custom.vtu"}]
