from __future__ import annotations

from itertools import product
from typing import Any

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.octave.capabilities import CAP_OCTAVE_STUDY_RUN
from metaharness_ext.octave.contracts import (
    OctaveExperimentSpec,
    OctaveStudyAxis,
    OctaveStudyReport,
    OctaveStudySpec,
    OctaveStudyTrial,
)
from metaharness_ext.octave.evidence import build_evidence_bundle
from metaharness_ext.octave.policy import OctaveEvidencePolicy
from metaharness_ext.octave.scientific_context import OctaveScientificContextAdapter
from metaharness_ext.octave.slots import OCTAVE_STUDY_SLOT


class OctaveStudyComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(OCTAVE_STUDY_SLOT)
        api.declare_input("study", "OctaveStudySpec")
        api.declare_output("report", "OctaveStudyReport", mode="sync")
        api.provide_capability(CAP_OCTAVE_STUDY_RUN)

    def run_study(
        self,
        spec: OctaveStudySpec,
        *,
        compiler: Any,
        executor: Any,
        validator: Any,
        context_adapter: OctaveScientificContextAdapter | None = None,
    ) -> OctaveStudyReport:
        snapshots = _generate_parameter_snapshots(spec)[: spec.max_trials]
        policy = OctaveEvidencePolicy()
        trials: list[OctaveStudyTrial] = []
        for snapshot in snapshots:
            trial_task = _mutate_task(spec.base_task, spec.resolved_task_id, snapshot)
            messages: list[str] = []
            if context_adapter is not None:
                context_result = context_adapter.pre_compile(trial_task)
                trial_task = context_result.spec or trial_task
                messages.extend(issue.message for issue in context_result.issues)
            plan = compiler.build_plan(trial_task)
            run = executor.execute_plan(plan)
            validation = validator.validate_run(run, plan)
            if context_adapter is not None:
                context_result = context_adapter.post_validate(validation, run, trial_task)
                validation.issues.extend(context_result.issues)
                if context_result.scored_evidence is not None:
                    validation.scored_evidence = context_result.scored_evidence
                messages.extend(issue.message for issue in context_result.issues)
            evidence_bundle = build_evidence_bundle(run, validation, plan=plan)
            policy_report = policy.evaluate(evidence_bundle)
            metric_value = _extract_metric(
                validation.numeric_metrics, spec.resolved_objective_metric
            )
            if metric_value is None:
                metric_value = _extract_metric(
                    validation.summary_metrics, spec.resolved_objective_metric
                )
            trials.append(
                OctaveStudyTrial(
                    trial_id=run.run_id,
                    parameters=snapshot,
                    parameter_snapshot=snapshot,
                    plan_ref=plan.plan_id,
                    artifact_ref=run.artifact_id,
                    validation_ref=f"octave://validation/{validation.task_id}/{validation.artifact_ref}",
                    evidence_bundle=evidence_bundle,
                    policy_report=policy_report,
                    metric_value=metric_value,
                    passed=validation.passed and policy_report.governance_state == "ready",
                    messages=[*validation.messages, *messages],
                )
            )

        best = _recommend_trial(trials, goal=spec.goal)
        return OctaveStudyReport(
            study_id=spec.study_id,
            task_id=spec.resolved_task_id,
            trials=trials,
            best_trial_id=best.trial_id if best is not None else None,
            recommended_parameters=best.parameter_snapshot if best is not None else None,
            convergence_analysis=_build_convergence_analysis(
                trials, spec.resolved_objective_metric, spec.goal
            ),
            summary_metrics=_build_summary_metrics(trials, spec.resolved_objective_metric, best),
            messages=[] if best is not None else ["No ready trial produced the requested metric."],
        )


def _generate_parameter_snapshots(spec: OctaveStudySpec) -> list[dict[str, Any]]:
    if spec.strategy in {"grid", "sequential", "bayesian"}:
        return _generate_grid(spec.axes)
    raise ValueError(f"Unsupported Octave study strategy: {spec.strategy}")


def _generate_grid(axes: list[OctaveStudyAxis]) -> list[dict[str, Any]]:
    axis_values: list[list[Any]] = []
    for axis in axes:
        if axis.values is not None:
            axis_values.append(list(axis.values))
        elif axis.range is not None:
            lo, hi = axis.range
            step = axis.step or 1.0
            values: list[float] = []
            current = lo
            while current <= hi + 1e-12:
                values.append(current)
                current += step
            axis_values.append(values)
    if not axis_values or any(not values for values in axis_values):
        return []
    snapshots: list[dict[str, Any]] = []
    for combo in product(*axis_values):
        snapshots.append({axis.path: value for axis, value in zip(axes, combo, strict=True)})
    return snapshots


def _mutate_task(
    base_task: OctaveExperimentSpec, task_id: str, snapshot: dict[str, Any]
) -> OctaveExperimentSpec:
    task = base_task.model_copy(deep=True)
    suffix = "__".join(f"{key.replace('.', '_')}={value}" for key, value in snapshot.items())
    task.task_id = f"{task_id}__study__{suffix}" if suffix else f"{task_id}__study"
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


def _recommend_trial(trials: list[OctaveStudyTrial], *, goal: str) -> OctaveStudyTrial | None:
    candidates = [trial for trial in trials if trial.passed and trial.metric_value is not None]
    if not candidates:
        return None
    return sorted(candidates, key=lambda trial: trial.metric_value, reverse=goal == "maximize")[0]


def _build_convergence_analysis(
    trials: list[OctaveStudyTrial], objective_metric: str, goal: str
) -> dict[str, Any]:
    scores = [
        trial.metric_value for trial in trials if trial.passed and trial.metric_value is not None
    ]
    if not scores:
        return {"objective_metric": objective_metric, "trial_count": len(trials), "ready_count": 0}
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
    trials: list[OctaveStudyTrial], metric_key: str, best: OctaveStudyTrial | None
) -> dict[str, float | str]:
    summary: dict[str, float | str] = {
        "trial_count": float(len(trials)),
        "ready_count": float(sum(1 for trial in trials if trial.passed)),
    }
    if best is not None and best.metric_value is not None:
        summary[f"best_{metric_key}"] = best.metric_value
    return summary
