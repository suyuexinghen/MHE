from __future__ import annotations

import copy

from metaharness_ext.pycfd.contracts import (
    PyCFDProblemSpec,
    PyCFDStudyReport,
    PyCFDStudySpec,
    PyCFDStudyTrial,
)


class PyCFDStudyComponent:
    """Runs parameter sweeps over PyCFD problem specs.

    Generates a Cartesian product of parameter axes, mutates the task template
    for each snapshot, and delegates to the compile-execute-validate pipeline.
    """

    def __init__(self, compiler, executor, validator):
        self._compiler = compiler
        self._executor = executor
        self._validator = validator

    def run_study(self, study_spec: PyCFDStudySpec) -> PyCFDStudyReport:
        snapshots = self._generate_snapshots(study_spec)
        trials: list[PyCFDStudyTrial] = []

        for i, snapshot in enumerate(snapshots):
            trial_id = f"{study_spec.study_id}-trial-{i}"
            try:
                spec = self._apply_snapshot(study_spec.task_template, snapshot)
                trial = self._run_trial(trial_id, spec, snapshot, study_spec.objective)
            except Exception as e:
                trial = PyCFDStudyTrial(
                    trial_id=trial_id,
                    parameters=snapshot,
                    passed=False,
                    messages=[str(e)],
                )
            trials.append(trial)
            if study_spec.max_trials and len(trials) >= study_spec.max_trials:
                break

        return self._build_report(study_spec, trials)

    def _generate_snapshots(self, study_spec: PyCFDStudySpec) -> list[dict]:
        axes = study_spec.axes
        if not axes:
            return [{}]

        values_per_axis: list[list] = []
        for axis in axes:
            if axis.values:
                values_per_axis.append(axis.values)
            elif axis.range and axis.step:
                start, end = axis.range
                vals = []
                v = start
                while v <= end + 1e-12:
                    vals.append(v)
                    v += axis.step
                values_per_axis.append(vals)
            else:
                values_per_axis.append([None])

        # Cartesian product
        import itertools

        combinations = list(itertools.product(*values_per_axis))
        axis_paths = [a.parameter_path for a in axes]
        return [dict(zip(axis_paths, combo)) for combo in combinations]

    def _apply_snapshot(self, spec: PyCFDProblemSpec, snapshot: dict) -> PyCFDProblemSpec:
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
        spec: PyCFDProblemSpec,
        snapshot: dict,
        objective: str,
    ) -> PyCFDStudyTrial:
        workspace_dir = spec.graph_metadata.get("study_workspace", f".runs/pycfd/studies/{trial_id}")
        plan = self._compiler.compile(spec, run_id=trial_id, workspace_dir=workspace_dir)
        artifact = self._executor.execute(plan)
        validation = self._validator.validate(artifact, plan_ref=plan.plan_id)
        summary_metrics = {**artifact.summary_metrics, **validation.summary_metrics}
        metric_value = summary_metrics.get(objective)
        if metric_value is not None and not isinstance(metric_value, int | float):
            metric_value = None
        return PyCFDStudyTrial(
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
        self, study_spec: PyCFDStudySpec, trials: list[PyCFDStudyTrial]
    ) -> PyCFDStudyReport:
        passed_trials = [t for t in trials if t.passed and t.metric_value is not None]
        best_trial = None
        recommended: dict | None = None

        if passed_trials:
            reverse = study_spec.goal == "maximize"
            passed_trials.sort(key=lambda t: t.metric_value or 0.0, reverse=reverse)
            best_trial = passed_trials[0]
            recommended = best_trial.parameters

        # Simple convergence analysis
        convergence: dict = {}
        if len(passed_trials) >= 2:
            drops = []
            for i in range(1, len(passed_trials)):
                prev = passed_trials[i - 1].metric_value
                curr = passed_trials[i].metric_value
                if prev and curr and prev != 0:
                    drops.append(abs(curr - prev) / abs(prev))
            if drops:
                convergence["mean_relative_drop"] = sum(drops) / len(drops)

        return PyCFDStudyReport(
            study_id=study_spec.study_id,
            task_id=study_spec.resolved_task_id,
            trials=trials,
            best_trial_id=best_trial.trial_id if best_trial else None,
            recommended_parameters=recommended,
            convergence_analysis=convergence,
            summary_metrics={"total_trials": len(trials), "passed_trials": len(passed_trials)},
        )
