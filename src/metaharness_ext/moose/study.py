from __future__ import annotations

import copy
import itertools
from typing import Any

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.moose.capabilities import CAP_MOOSE_STUDY_RUN
from metaharness_ext.moose.contracts import (
    MooseProblemSpec,
    MooseStudyReport,
    MooseStudySpec,
    MooseStudyTrial,
)
from metaharness_ext.moose.slots import MOOSE_STUDY_SLOT


class MooseStudyComponent(HarnessComponent):
    """Runs parameter sweeps over MOOSE problem specs."""

    def __init__(self, compiler: Any = None, executor: Any = None, validator: Any = None):
        self._compiler = compiler
        self._executor = executor
        self._validator = validator

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(MOOSE_STUDY_SLOT)
        api.declare_input("study", "MooseStudySpec")
        api.declare_output("report", "MooseStudyReport", mode="sync")
        api.provide_capability(CAP_MOOSE_STUDY_RUN)

    def run_study(self, study_spec: MooseStudySpec) -> MooseStudyReport:
        if self._compiler is None or self._executor is None or self._validator is None:
            raise ValueError("MooseStudyComponent requires compiler, executor, and validator")
        snapshots = self._generate_snapshots(study_spec)
        trials: list[MooseStudyTrial] = []

        for index, snapshot in enumerate(snapshots):
            trial_id = f"{study_spec.study_id}-trial-{index}"
            try:
                spec = self._apply_snapshot(study_spec.task_template, snapshot)
                trial = self._run_trial(trial_id, spec, snapshot, study_spec.objective)
            except Exception as error:
                trial = MooseStudyTrial(
                    trial_id=trial_id, parameters=snapshot, passed=False, messages=[str(error)]
                )
            trials.append(trial)
            if study_spec.max_trials and len(trials) >= study_spec.max_trials:
                break

        return self._build_report(study_spec, trials)

    def _generate_snapshots(self, study_spec: MooseStudySpec) -> list[dict]:
        if not study_spec.axes:
            return [{}]

        values_per_axis: list[list] = []
        for axis in study_spec.axes:
            if axis.values:
                values_per_axis.append(axis.values)
            elif axis.range and axis.step:
                start, end = axis.range
                values: list[float] = []
                value = start
                while value <= end + 1e-12:
                    values.append(value)
                    value += axis.step
                values_per_axis.append(values)
            else:
                values_per_axis.append([None])

        axis_paths = [axis.parameter_path for axis in study_spec.axes]
        combinations = itertools.product(*values_per_axis)
        return [dict(zip(axis_paths, combo)) for combo in combinations]

    def _apply_snapshot(self, spec: MooseProblemSpec, snapshot: dict) -> MooseProblemSpec:
        mutated = copy.deepcopy(spec)
        for path, value in snapshot.items():
            parts = path.split(".")
            obj = mutated
            for part in parts[:-1]:
                obj = getattr(obj, part)
            setattr(obj, parts[-1], value)
        return mutated

    def _run_trial(
        self,
        trial_id: str,
        spec: MooseProblemSpec,
        snapshot: dict,
        objective: str,
    ) -> MooseStudyTrial:
        plan = self._compiler.compile(
            spec, run_id=trial_id, workspace_dir=f".runs/moose/studies/{trial_id}"
        )
        artifact = self._executor.execute_plan(plan)
        validation = self._validator.validate_run(artifact, plan)
        summary_metrics = {**artifact.summary_metrics, **validation.summary_metrics}
        metric_value = summary_metrics.get(objective)
        if metric_value is not None and not isinstance(metric_value, (int, float)):
            metric_value = None
        return MooseStudyTrial(
            trial_id=trial_id,
            parameters=snapshot,
            plan_ref=plan.plan_id,
            artifact_ref=artifact.artifact_id,
            validation_ref=validation.artifact_ref,
            metric_value=float(metric_value) if metric_value is not None else None,
            passed=validation.passed,
            messages=[*validation.messages],
        )

    def _build_report(
        self, study_spec: MooseStudySpec, trials: list[MooseStudyTrial]
    ) -> MooseStudyReport:
        ranked = [trial for trial in trials if trial.passed and trial.metric_value is not None]
        best_trial = None
        recommended: dict | None = None
        if ranked:
            ranked.sort(
                key=lambda trial: trial.metric_value or 0.0, reverse=study_spec.goal == "maximize"
            )
            best_trial = ranked[0]
            recommended = best_trial.parameters
        return MooseStudyReport(
            study_id=study_spec.study_id,
            task_id=study_spec.task_template.task_id,
            trials=trials,
            best_trial_id=best_trial.trial_id if best_trial else None,
            recommended_parameters=recommended,
            summary_metrics={"total_trials": len(trials), "passed_trials": len(ranked)},
        )
