from __future__ import annotations

import copy
import itertools

from metaharness_ext.boutpp.contracts import (
    BoutPPProblemSpec,
    BoutPPStudyReport,
    BoutPPStudySpec,
    BoutPPStudyTrial,
)


class BoutPPStudyComponent:
    def __init__(self, compiler, executor, postprocess, validator):
        self._compiler = compiler
        self._executor = executor
        self._postprocess = postprocess
        self._validator = validator

    def run_study(self, study_spec: BoutPPStudySpec) -> BoutPPStudyReport:
        snapshots = self._generate_snapshots(study_spec)
        trials: list[BoutPPStudyTrial] = []
        for index, snapshot in enumerate(snapshots):
            trial_id = f"{study_spec.study_id}-trial-{index}"
            try:
                spec = self._apply_snapshot(study_spec.task_template, snapshot)
                trial = self._run_trial(trial_id, spec, snapshot, study_spec.objective)
            except Exception as error:
                trial = BoutPPStudyTrial(trial_id=trial_id, parameters=snapshot, passed=False, messages=[str(error)])
            trials.append(trial)
            if study_spec.max_trials and len(trials) >= study_spec.max_trials:
                break
        return self._build_report(study_spec, trials)

    def _generate_snapshots(self, study_spec: BoutPPStudySpec) -> list[dict]:
        if not study_spec.axes:
            return [{}]
        values_per_axis: list[list] = []
        for axis in study_spec.axes:
            if axis.values is not None:
                values_per_axis.append(list(axis.values))
            elif axis.range is not None and axis.step is not None:
                start, end = axis.range
                values = []
                current = start
                while current <= end + 1e-12:
                    values.append(current)
                    current += axis.step
                values_per_axis.append(values)
            else:
                values_per_axis.append([None])
        axis_paths = [axis.parameter_path for axis in study_spec.axes]
        return [dict(zip(axis_paths, combo, strict=True)) for combo in itertools.product(*values_per_axis)]

    def _apply_snapshot(self, spec: BoutPPProblemSpec, snapshot: dict) -> BoutPPProblemSpec:
        mutated = copy.deepcopy(spec)
        for dotted_path, value in snapshot.items():
            container = mutated
            parts = dotted_path.split(".")
            for part in parts[:-1]:
                container = getattr(container, part) if hasattr(container, part) else container[part]
            last = parts[-1]
            if isinstance(container, dict):
                container[last] = value
            else:
                setattr(container, last, value)
        return mutated

    def _run_trial(self, trial_id: str, spec: BoutPPProblemSpec, snapshot: dict, objective: str) -> BoutPPStudyTrial:
        workspace_dir = spec.graph_metadata.get("study_workspace", f".runs/boutpp/studies/{trial_id}")
        plan = self._compiler.compile(spec, run_id=trial_id, workspace_dir=workspace_dir)
        artifact = self._executor.execute(plan)
        postprocess = self._postprocess.postprocess(artifact)
        validation = self._validator.validate(artifact, plan_ref=plan.plan_id, postprocess=postprocess, validation_spec=spec.validation)
        summary_metrics = {**artifact.summary_metrics, **postprocess.summary_metrics, **validation.summary_metrics}
        metric_value = summary_metrics.get(objective)
        if not isinstance(metric_value, (int, float)):
            metric_value = None
        return BoutPPStudyTrial(
            trial_id=trial_id,
            parameters=snapshot,
            plan_ref=plan.plan_id,
            artifact_ref=artifact.artifact_id,
            postprocess_ref=postprocess.report_id,
            validation_ref=validation.artifact_ref,
            metric_value=float(metric_value) if metric_value is not None else None,
            passed=validation.passed,
            messages=[*postprocess.warnings, *validation.messages],
        )

    def _build_report(self, study_spec: BoutPPStudySpec, trials: list[BoutPPStudyTrial]) -> BoutPPStudyReport:
        passing_trials = [trial for trial in trials if trial.passed and trial.metric_value is not None]
        best_trial = None
        recommended: dict | None = None
        if passing_trials:
            reverse = study_spec.goal == "maximize"
            passing_trials.sort(key=lambda trial: trial.metric_value or 0.0, reverse=reverse)
            best_trial = passing_trials[0]
            recommended = best_trial.parameters
        return BoutPPStudyReport(
            study_id=study_spec.study_id,
            task_id=study_spec.resolved_task_id,
            trials=trials,
            best_trial_id=best_trial.trial_id if best_trial else None,
            recommended_parameters=recommended,
            summary_metrics={"total_trials": len(trials), "passed_trials": len(passing_trials)},
        )
