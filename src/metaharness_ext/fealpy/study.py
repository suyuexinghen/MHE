from __future__ import annotations

from itertools import product
from typing import Any

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.fealpy.capabilities import CAP_FEALPY_STUDY_RUN
from metaharness_ext.fealpy.compiler import FealpyCompilerComponent
from metaharness_ext.fealpy.contracts import (
    FealpyProblemSpec,
    FealpyStudyReport,
    FealpyStudySpec,
    FealpyStudyTrial,
)
from metaharness_ext.fealpy.evidence import build_evidence_bundle
from metaharness_ext.fealpy.executor import FealpyExecutorComponent
from metaharness_ext.fealpy.policy import FealpyEvidencePolicy
from metaharness_ext.fealpy.slots import FEALPY_STUDY_SLOT
from metaharness_ext.fealpy.validator import FealpyValidatorComponent


class FealpyStudyComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(FEALPY_STUDY_SLOT)
        api.declare_input("study", "FealpyStudySpec")
        api.declare_output("report", "FealpyStudyReport", mode="sync")
        api.provide_capability(CAP_FEALPY_STUDY_RUN)

    def run_study(
        self,
        spec: FealpyStudySpec,
        *,
        compiler: FealpyCompilerComponent | None = None,
        executor: FealpyExecutorComponent | None = None,
        validator: FealpyValidatorComponent | None = None,
    ) -> FealpyStudyReport:
        compiler = compiler or FealpyCompilerComponent()
        executor = executor or FealpyExecutorComponent()
        validator = validator or FealpyValidatorComponent()

        snapshots = _generate_parameter_snapshots(spec)
        if spec.max_trials is not None:
            snapshots = snapshots[: spec.max_trials]

        policy = FealpyEvidencePolicy()
        trials: list[FealpyStudyTrial] = []

        for snapshot in snapshots:
            trial_task = _mutate_task(spec.task_template, snapshot)
            plan = compiler.compile(trial_task)
            run = executor.execute_plan(plan)
            validation_report = validator.validate(run, plan)
            evidence_bundle = build_evidence_bundle(run, validation_report, plan=plan)
            policy_report = policy.evaluate(evidence_bundle)

            metric_value = _extract_metric(validation_report.summary_metrics, spec.objective)
            if metric_value is None and run.summary_metrics:
                metric_value = _extract_metric(run.summary_metrics, spec.objective)

            trials.append(
                FealpyStudyTrial(
                    trial_id=run.run_id,
                    parameters=snapshot,
                    plan_ref=plan.plan_id,
                    artifact_ref=run.artifact_id,
                    validation_ref=(
                        f"fealpy://validation/{validation_report.task_id}/"
                        f"{validation_report.artifact_ref}"
                    ),
                    metric_value=metric_value,
                    passed=validation_report.passed and policy_report.decision != "reject",
                    messages=[*validation_report.messages],
                )
            )

        best = _recommend_trial(trials, goal=spec.goal)
        return FealpyStudyReport(
            study_id=spec.study_id,
            task_id=spec.resolved_task_id,
            trials=trials,
            best_trial_id=best.trial_id if best is not None else None,
            recommended_parameters=best.parameters if best is not None else None,
            convergence_analysis=_build_convergence_analysis(trials, spec.objective, spec.goal),
            summary_metrics=_build_summary_metrics(trials, spec.objective, best),
            messages=[] if best is not None else ["No trial produced the requested metric."],
        )


def _generate_parameter_snapshots(spec: FealpyStudySpec) -> list[dict[str, Any]]:
    axis_values: list[list[Any]] = []
    for axis in spec.axes:
        if axis.values is not None:
            axis_values.append(list(axis.values))
        elif axis.range is not None:
            lo, hi = axis.range
            step = axis.step or 1.0
            values: list[float] = []
            current = lo
            while current <= hi + 1e-12:
                values.append(round(current, 10))
                current += step
            axis_values.append(values)
    if not axis_values or any(not v for v in axis_values):
        return []
    snapshots: list[dict[str, Any]] = []
    for combo in product(*axis_values):
        snapshots.append(
            {axis.parameter_path: value for axis, value in zip(spec.axes, combo, strict=True)}
        )
    return snapshots


def _mutate_task(base_task: FealpyProblemSpec, snapshot: dict[str, Any]) -> FealpyProblemSpec:
    task = base_task.model_copy(deep=True)
    suffix = "__".join(f"{key.replace('.', '_')}={value}" for key, value in snapshot.items())
    task.task_id = f"{base_task.task_id}__study__{suffix}"
    for path, value in snapshot.items():
        _set_dotted(task, path, value)
    return task


def _set_dotted(obj: Any, path: str, value: Any) -> None:
    parts = path.split(".")
    target = obj
    for part in parts[:-1]:
        if isinstance(target, dict):
            target = target.setdefault(part, {})
        else:
            target = getattr(target, part)
    final = parts[-1]
    if isinstance(target, dict):
        target[final] = value
    else:
        setattr(target, final, value)


def _extract_metric(metrics: dict[str, Any], metric_key: str) -> float | None:
    value = metrics.get(metric_key)
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _recommend_trial(trials: list[FealpyStudyTrial], *, goal: str) -> FealpyStudyTrial | None:
    candidates = [trial for trial in trials if trial.passed and trial.metric_value is not None]
    if not candidates:
        return None
    return sorted(candidates, key=lambda trial: trial.metric_value, reverse=goal == "maximize")[0]


def _build_convergence_analysis(
    trials: list[FealpyStudyTrial], objective_metric: str, goal: str
) -> dict[str, Any]:
    scores = [
        trial.metric_value for trial in trials if trial.passed and trial.metric_value is not None
    ]
    if not scores:
        return {
            "objective_metric": objective_metric,
            "trial_count": len(trials),
            "ready_count": 0,
        }
    return {
        "objective_metric": objective_metric,
        "goal": goal,
        "trial_count": len(trials),
        "ready_count": len(scores),
        "best_score": min(scores) if goal == "minimize" else max(scores),
        "worst_score": max(scores) if goal == "minimize" else min(scores),
        "score_range": max(scores) - min(scores),
    }


def _build_summary_metrics(
    trials: list[FealpyStudyTrial],
    metric_key: str,
    best: FealpyStudyTrial | None,
) -> dict[str, float | str]:
    summary: dict[str, float | str] = {
        "trial_count": float(len(trials)),
        "ready_count": float(sum(1 for trial in trials if trial.passed)),
    }
    if best is not None and best.metric_value is not None:
        summary[f"best_{metric_key}"] = best.metric_value
    return summary
