from pathlib import Path

import pytest
import yaml

from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.jedi.config_compiler import JediConfigCompilerComponent
from metaharness_ext.jedi.contracts import (
    JediDiagnosticSummary,
    JediExecutableSpec,
    JediLocalEnsembleDASpec,
    JediMutationAxis,
    JediRunArtifact,
    JediStudySpec,
    JediValidationReport,
    JediVariationalSpec,
)
from metaharness_ext.jedi.study import JediStudyComponent


class _FakeExecutor:
    def __init__(self, metric_key: str, values: dict[int | str, float]) -> None:
        self.metric_key = metric_key
        self.values = values
        self.calls: list[int | str] = []

    def execute_plan(self, plan):
        config = yaml.safe_load(plan.config_text)
        minimizer = config.get("variational", {}).get("minimizer", {})
        ensemble = config.get("local ensemble DA", {})
        if "algorithm" in minimizer and minimizer.get("algorithm") in self.values:
            axis_value = minimizer["algorithm"]
        elif "iterations" in minimizer and minimizer.get("iterations") in self.values:
            axis_value = int(minimizer["iterations"])
        elif "inflation" in ensemble and ensemble.get("inflation") in self.values:
            axis_value = float(ensemble["inflation"])
        elif "localization_radius" in ensemble and ensemble.get("localization_radius") in self.values:
            axis_value = float(ensemble["localization_radius"])
        elif plan.execution_mode == "validate_only":
            axis_value = "validate_only"
        else:
            axis_value = "real_run"
        self.calls.append(axis_value)
        metric = self.values[axis_value]
        return JediRunArtifact(
            task_id=plan.task_id,
            run_id=plan.run_id,
            application_family=plan.application_family,
            execution_mode=plan.execution_mode,
            command=plan.command,
            return_code=0,
            stdout_path="/tmp/stdout.log",
            stderr_path="/tmp/stderr.log",
            working_directory="/tmp/run",
            status="completed",
            result_summary={"exit_code": 0, self.metric_key: metric},
        )


class _FakeDiagnostics:
    def collect(self, artifact: JediRunArtifact) -> JediDiagnosticSummary:
        metric_value = artifact.result_summary.get("final_cost_function")
        summary = JediDiagnosticSummary(
            final_cost_function=float(metric_value) if isinstance(metric_value, int | float) else None
        )
        summary.messages = [
            f"metric:{key}={value}"
            for key, value in artifact.result_summary.items()
            if key != "exit_code" and isinstance(value, int | float)
        ]
        return summary


class _FakeValidator:
    def __init__(self, *, passed: bool = True) -> None:
        self.passed = passed

    def validate_run_with_diagnostics(
        self,
        artifact: JediRunArtifact,
        diagnostic_summary: JediDiagnosticSummary | None = None,
    ) -> JediValidationReport:
        summary_metrics: dict[str, float | str] = {}
        if diagnostic_summary and diagnostic_summary.final_cost_function is not None:
            summary_metrics["final_cost_function"] = diagnostic_summary.final_cost_function
        if diagnostic_summary:
            for message in diagnostic_summary.messages:
                if not message.startswith("metric:"):
                    continue
                key, value = message.removeprefix("metric:").split("=", 1)
                summary_metrics[key] = float(value)
        return JediValidationReport(
            task_id=artifact.task_id,
            run_id=artifact.run_id,
            passed=self.passed,
            status="executed" if self.passed else "validation_failed",
            summary_metrics=summary_metrics,
            evidence_files=[],
        )


def _build_variational_spec() -> JediVariationalSpec:
    return JediVariationalSpec(
        task_id="jedi-study-task",
        executable=JediExecutableSpec(binary_name="qg4DVar.x", execution_mode="real_run"),
        background_path="/tmp/background.nc",
        observation_paths=["/tmp/obs.ioda"],
        variational={"minimizer": {"algorithm": "RPCG", "iterations": 20}},
    )


def _build_local_ensemble_spec() -> JediLocalEnsembleDASpec:
    return JediLocalEnsembleDASpec(
        task_id="jedi-letkf-study-task",
        executable=JediExecutableSpec(binary_name="qgLETKF.x", execution_mode="real_run"),
        ensemble_paths=["/tmp/ens.000", "/tmp/ens.001"],
        background_path="/tmp/background.nc",
        observation_paths=["/tmp/obs.ioda"],
        ensemble={"inflation": 1.0, "localization_radius": 1200.0},
    )


@pytest.mark.asyncio
async def test_study_minimizes_variational_iterations_metric(tmp_path: Path) -> None:
    component = JediStudyComponent()
    await component.activate(ComponentRuntime(storage_path=tmp_path))
    compiler = JediConfigCompilerComponent()
    executor = _FakeExecutor("final_cost_function", {10: 9.0, 20: 3.0, 30: 4.0})
    diagnostics = _FakeDiagnostics()
    validator = _FakeValidator()

    spec = JediStudySpec(
        study_id="study-1",
        task_id="jedi-study-task",
        base_task=_build_variational_spec(),
        axis=JediMutationAxis(kind="variational_iterations", values=[10, 20, 30]),
        metric_key="final_cost_function",
        goal="minimize",
    )

    report = component.run_study(
        spec,
        compiler=compiler,
        executor=executor,
        diagnostics=diagnostics,
        validator=validator,
    )

    assert executor.calls == [10, 20, 30]
    assert [trial.axis_value for trial in report.trials] == [10, 20, 30]
    assert report.recommended_value == 20
    assert report.summary_metrics["best_final_cost_function"] == pytest.approx(3.0)


@pytest.mark.asyncio
async def test_study_supports_variational_minimizer_axis(tmp_path: Path) -> None:
    component = JediStudyComponent()
    await component.activate(ComponentRuntime(storage_path=tmp_path))
    compiler = JediConfigCompilerComponent()
    executor = _FakeExecutor("final_cost_function", {"RPCG": 5.0, "DRPCG": 2.5})
    diagnostics = _FakeDiagnostics()
    validator = _FakeValidator()

    spec = JediStudySpec(
        study_id="study-2",
        task_id="jedi-study-task",
        base_task=_build_variational_spec(),
        axis=JediMutationAxis(kind="variational_minimizer", values=["RPCG", "DRPCG"]),
        metric_key="final_cost_function",
        goal="minimize",
    )

    report = component.run_study(
        spec,
        compiler=compiler,
        executor=executor,
        diagnostics=diagnostics,
        validator=validator,
    )

    assert report.recommended_value == "DRPCG"
    assert report.summary_metrics["best_final_cost_function"] == pytest.approx(2.5)


@pytest.mark.asyncio
async def test_study_rejects_invalid_validate_only_axis_value_type(tmp_path: Path) -> None:
    component = JediStudyComponent()
    await component.activate(ComponentRuntime(storage_path=tmp_path))

    spec = JediStudySpec(
        study_id="study-bad",
        task_id="jedi-study-task",
        base_task=_build_variational_spec(),
        axis=JediMutationAxis(kind="validate_only_mode", values=["schema"]),
        metric_key="final_cost_function",
    )

    with pytest.raises(ValueError, match="validate_only_mode values must be strings"):
        component._mutate_task(spec, 1)


@pytest.mark.asyncio
async def test_study_rejects_unknown_axis_at_runtime(tmp_path: Path) -> None:
    component = JediStudyComponent()
    await component.activate(ComponentRuntime(storage_path=tmp_path))
    compiler = JediConfigCompilerComponent()
    executor = _FakeExecutor("final_cost_function", {20: 3.0})
    diagnostics = _FakeDiagnostics()
    validator = _FakeValidator()

    spec = JediStudySpec.model_construct(
        study_id="study-unknown-axis",
        task_id="jedi-study-task",
        base_task=_build_variational_spec(),
        axis=JediMutationAxis.model_construct(kind="unknown_axis", values=[20]),
        metric_key="final_cost_function",
        goal="minimize",
    )

    with pytest.raises(NotImplementedError, match="unknown_axis"):
        component.run_study(
            spec,
            compiler=compiler,
            executor=executor,
            diagnostics=diagnostics,
            validator=validator,
        )


@pytest.mark.asyncio
async def test_study_supports_ensemble_inflation_axis(tmp_path: Path) -> None:
    component = JediStudyComponent()
    await component.activate(ComponentRuntime(storage_path=tmp_path))
    compiler = JediConfigCompilerComponent()
    executor = _FakeExecutor("posterior_spread", {0.8: 4.0, 1.0: 2.0, 1.2: 3.0})
    diagnostics = _FakeDiagnostics()
    validator = _FakeValidator()

    spec = JediStudySpec(
        study_id="study-letkf-1",
        task_id="jedi-letkf-study-task",
        base_task=_build_local_ensemble_spec(),
        axis=JediMutationAxis(kind="ensemble_inflation", values=[0.8, 1.0, 1.2]),
        metric_key="posterior_spread",
        goal="minimize",
    )

    report = component.run_study(
        spec,
        compiler=compiler,
        executor=executor,
        diagnostics=diagnostics,
        validator=validator,
    )

    assert executor.calls == [0.8, 1.0, 1.2]
    assert report.recommended_value == pytest.approx(1.0)
    assert report.summary_metrics["best_posterior_spread"] == pytest.approx(2.0)


@pytest.mark.asyncio
async def test_study_supports_ensemble_localization_radius_axis(tmp_path: Path) -> None:
    component = JediStudyComponent()
    await component.activate(ComponentRuntime(storage_path=tmp_path))
    compiler = JediConfigCompilerComponent()
    executor = _FakeExecutor("posterior_spread", {800.0: 5.0, 1200.0: 3.0, 1600.0: 4.0})
    diagnostics = _FakeDiagnostics()
    validator = _FakeValidator()

    spec = JediStudySpec(
        study_id="study-letkf-2",
        task_id="jedi-letkf-study-task",
        base_task=_build_local_ensemble_spec(),
        axis=JediMutationAxis(kind="ensemble_localization_radius", values=[800.0, 1200.0, 1600.0]),
        metric_key="posterior_spread",
        goal="minimize",
    )

    report = component.run_study(
        spec,
        compiler=compiler,
        executor=executor,
        diagnostics=diagnostics,
        validator=validator,
    )

    assert executor.calls == [800.0, 1200.0, 1600.0]
    assert report.recommended_value == pytest.approx(1200.0)
    assert report.summary_metrics["best_posterior_spread"] == pytest.approx(3.0)


@pytest.mark.asyncio
async def test_study_supports_maximize_goal(tmp_path: Path) -> None:
    component = JediStudyComponent()
    await component.activate(ComponentRuntime(storage_path=tmp_path))
    compiler = JediConfigCompilerComponent()
    executor = _FakeExecutor("posterior_spread", {0.8: 4.0, 1.0: 2.0, 1.2: 5.0})
    diagnostics = _FakeDiagnostics()
    validator = _FakeValidator()

    spec = JediStudySpec(
        study_id="study-letkf-max",
        task_id="jedi-letkf-study-task",
        base_task=_build_local_ensemble_spec(),
        axis=JediMutationAxis(kind="ensemble_inflation", values=[0.8, 1.0, 1.2]),
        metric_key="posterior_spread",
        goal="maximize",
    )

    report = component.run_study(
        spec,
        compiler=compiler,
        executor=executor,
        diagnostics=diagnostics,
        validator=validator,
    )

    assert report.recommended_value == pytest.approx(1.2)
    assert report.summary_metrics["best_posterior_spread"] == pytest.approx(5.0)


@pytest.mark.asyncio
async def test_study_returns_no_recommendation_when_all_trials_fail(tmp_path: Path) -> None:
    component = JediStudyComponent()
    await component.activate(ComponentRuntime(storage_path=tmp_path))
    compiler = JediConfigCompilerComponent()
    executor = _FakeExecutor("final_cost_function", {10: 9.0, 20: 3.0, 30: 4.0})
    diagnostics = _FakeDiagnostics()
    validator = _FakeValidator(passed=False)

    spec = JediStudySpec(
        study_id="study-all-fail",
        task_id="jedi-study-task",
        base_task=_build_variational_spec(),
        axis=JediMutationAxis(kind="variational_iterations", values=[10, 20, 30]),
        metric_key="final_cost_function",
        goal="minimize",
    )

    report = component.run_study(
        spec,
        compiler=compiler,
        executor=executor,
        diagnostics=diagnostics,
        validator=validator,
    )

    assert report.recommended_value is None
    assert report.recommended_trial_id is None
    assert report.messages == ["No passing trial produced the requested metric."]
    assert "best_final_cost_function" not in report.summary_metrics


@pytest.mark.asyncio
async def test_study_continues_when_one_trial_raises(tmp_path: Path) -> None:
    component = JediStudyComponent()
    await component.activate(ComponentRuntime(storage_path=tmp_path))
    compiler = JediConfigCompilerComponent()
    diagnostics = _FakeDiagnostics()
    validator = _FakeValidator()

    class _ExplodingExecutor(_FakeExecutor):
        def execute_plan(self, plan):
            config = yaml.safe_load(plan.config_text)
            iterations = int(config["variational"]["minimizer"]["iterations"])
            if iterations == 20:
                raise RuntimeError("transient launcher failure")
            return super().execute_plan(plan)

    executor = _ExplodingExecutor("final_cost_function", {10: 9.0, 30: 4.0})
    spec = JediStudySpec(
        study_id="study-partial-failure",
        task_id="jedi-study-task",
        base_task=_build_variational_spec(),
        axis=JediMutationAxis(kind="variational_iterations", values=[10, 20, 30]),
        metric_key="final_cost_function",
        goal="minimize",
    )

    report = component.run_study(
        spec,
        compiler=compiler,
        executor=executor,
        diagnostics=diagnostics,
        validator=validator,
    )

    assert [trial.axis_value for trial in report.trials] == [10, 20, 30]
    failed_trial = report.trials[1]
    assert failed_trial.passed is False
    assert failed_trial.metric_value is None
    assert failed_trial.validation.status == "runtime_failed"
    assert failed_trial.messages == ["Study trial failed: transient launcher failure"]
    assert report.recommended_value == 30
    assert report.summary_metrics["best_final_cost_function"] == pytest.approx(4.0)


def test_study_axis_requires_values() -> None:
    with pytest.raises(ValueError, match="axis.values"):
        JediMutationAxis(kind="variational_iterations", values=[])
