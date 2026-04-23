from __future__ import annotations

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.jedi.capabilities import CAP_JEDI_STUDY
from metaharness_ext.jedi.config_compiler import JediConfigCompilerComponent
from metaharness_ext.jedi.contracts import (
    JediLocalEnsembleDASpec,
    JediStudyReport,
    JediStudySpec,
    JediStudyTrial,
    JediValidationReport,
    JediVariationalSpec,
)
from metaharness_ext.jedi.diagnostics import JediDiagnosticsCollectorComponent
from metaharness_ext.jedi.executor import JediExecutorComponent
from metaharness_ext.jedi.slots import JEDI_STUDY_SLOT
from metaharness_ext.jedi.validator import JediValidatorComponent


class JediStudyComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(JEDI_STUDY_SLOT)
        api.declare_input("study", "JediStudySpec")
        api.declare_output("report", "JediStudyReport", mode="sync")
        api.provide_capability(CAP_JEDI_STUDY)

    def run_study(
        self,
        spec: JediStudySpec,
        *,
        compiler: JediConfigCompilerComponent,
        executor: JediExecutorComponent,
        diagnostics: JediDiagnosticsCollectorComponent,
        validator: JediValidatorComponent,
    ) -> JediStudyReport:
        self._validate_axis(spec)
        trials: list[JediStudyTrial] = []
        for value in spec.axis.values:
            trial_task = self._mutate_task(spec, value)
            plan = compiler.build_plan(trial_task)
            run = executor.execute_plan(plan)
            diagnostic_summary = diagnostics.collect(run)
            validation = validator.validate_run_with_diagnostics(run, diagnostic_summary)
            metric_value = self._extract_metric(validation, spec.metric_key)
            trials.append(
                JediStudyTrial(
                    trial_id=run.run_id,
                    task_id=run.task_id,
                    axis_kind=spec.axis.kind,
                    axis_value=value,
                    mutated_parameters=self._mutated_parameters(spec.axis.kind, value),
                    run=run,
                    diagnostics=diagnostic_summary,
                    validation=validation,
                    metric_value=metric_value,
                    passed=validation.passed,
                    messages=list(validation.messages),
                )
            )

        recommended = self._recommend_trial(trials, goal=spec.goal)
        summary_metrics: dict[str, float | str] = {"trial_count": float(len(trials))}
        if recommended is not None and recommended.metric_value is not None:
            summary_metrics[f"best_{spec.metric_key}"] = recommended.metric_value

        return JediStudyReport(
            study_id=spec.study_id,
            task_id=spec.task_id,
            axis_kind=spec.axis.kind,
            metric_key=spec.metric_key,
            trials=trials,
            recommended_value=recommended.axis_value if recommended is not None else None,
            recommended_trial_id=recommended.trial_id if recommended is not None else None,
            recommended_reason=(
                f"Selected the {'lowest' if spec.goal == 'minimize' else 'highest'} passing {spec.metric_key}."
                if recommended is not None
                else "No passing trial produced the requested metric."
            ),
            summary_metrics=summary_metrics,
            messages=[] if recommended is not None else ["No passing trial produced the requested metric."],
        )

    def _validate_axis(self, spec: JediStudySpec) -> None:
        supported_axes = {
            "variational_minimizer",
            "variational_iterations",
            "validate_only_mode",
            "ensemble_inflation",
            "ensemble_localization_radius",
        }
        if spec.axis.kind not in supported_axes:
            raise NotImplementedError(f"Axis {spec.axis.kind} is not supported")

    def _mutate_task(self, spec: JediStudySpec, value: str | int | float) -> JediVariationalSpec | JediLocalEnsembleDASpec:
        task = spec.base_task.model_copy(deep=True)
        task.task_id = f"{spec.task_id}__study__{spec.axis.kind}__{value}"

        if isinstance(task, JediVariationalSpec):
            if spec.axis.kind == "variational_minimizer":
                if not isinstance(value, str):
                    raise ValueError("variational_minimizer values must be strings")
                task.variational = {
                    **task.variational,
                    "minimizer": {**task.variational.get("minimizer", {}), "algorithm": value},
                }
                return task

            if spec.axis.kind == "variational_iterations":
                if not isinstance(value, int):
                    raise ValueError("variational_iterations values must be integers")
                task.variational = {
                    **task.variational,
                    "minimizer": {**task.variational.get("minimizer", {}), "iterations": value},
                }
                return task

            if not isinstance(value, str):
                raise ValueError("validate_only_mode values must be strings")
            task.executable.execution_mode = value
            return task

        if spec.axis.kind == "ensemble_inflation":
            if not isinstance(value, int | float):
                raise ValueError("ensemble_inflation values must be numeric")
            task.ensemble = {**task.ensemble, "inflation": float(value)}
            return task

        if spec.axis.kind == "ensemble_localization_radius":
            if not isinstance(value, int | float):
                raise ValueError("ensemble_localization_radius values must be numeric")
            task.ensemble = {**task.ensemble, "localization_radius": float(value)}
            return task

        raise NotImplementedError(f"Axis {spec.axis.kind} is not supported for {type(task).__name__}")

    def _mutated_parameters(self, axis_kind: str, value: str | int | float) -> dict[str, int | float | str]:
        return {axis_kind: value}

    def _extract_metric(self, validation: JediValidationReport, metric_key: str) -> float | None:
        value = validation.summary_metrics.get(metric_key)
        if isinstance(value, int | float):
            return float(value)
        return None

    def _recommend_trial(self, trials: list[JediStudyTrial], *, goal: str) -> JediStudyTrial | None:
        candidates = [trial for trial in trials if trial.passed and trial.metric_value is not None]
        if not candidates:
            return None
        reverse = goal == "maximize"
        return sorted(candidates, key=lambda trial: trial.metric_value, reverse=reverse)[0]
