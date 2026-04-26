from __future__ import annotations

import random
import uuid
from itertools import product
from typing import Any

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.qcompute.capabilities import CAP_QCOMPUTE_STUDY_RUN
from metaharness_ext.qcompute.config_compiler import QComputeConfigCompilerComponent
from metaharness_ext.qcompute.contracts import (
    QComputeEnvironmentReport,
    QComputeExperimentSpec,
    QComputeObjective,
    QComputeRunPlan,
    QComputeStudyAxis,
    QComputeStudyReport,
    QComputeStudySpec,
    QComputeStudyStrategy,
    QComputeStudyTrial,
    QComputeValidationReport,
)
from metaharness_ext.qcompute.evidence import build_evidence_bundle
from metaharness_ext.qcompute.executor import QComputeExecutorComponent
from metaharness_ext.qcompute.governance import QComputeGovernanceAdapter
from metaharness_ext.qcompute.policy import QComputeEvidencePolicy
from metaharness_ext.qcompute.slots import QCOMPUTE_STUDY_SLOT
from metaharness_ext.qcompute.validator import QComputeValidatorComponent


class QComputeStudyComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(QCOMPUTE_STUDY_SLOT)
        api.declare_input("study", "QComputeStudySpec")
        api.declare_output("report", "QComputeStudyReport", mode="sync")
        api.provide_capability(CAP_QCOMPUTE_STUDY_RUN)

    def run_study(
        self,
        spec: QComputeStudySpec,
        *,
        compiler: QComputeConfigCompilerComponent | None = None,
        executor: QComputeExecutorComponent | None = None,
        validator: QComputeValidatorComponent | None = None,
    ) -> QComputeStudyReport:
        if compiler is None:
            compiler = QComputeConfigCompilerComponent()
        if executor is None:
            executor = QComputeExecutorComponent()
            executor._runtime = self._runtime  # noqa: SLF001
        if validator is None:
            validator = QComputeValidatorComponent()

        grid = _generate_grid(spec)
        grid = grid[: spec.max_trials]

        policy_eval = QComputeEvidencePolicy()
        governance = QComputeGovernanceAdapter()
        trials: list[QComputeStudyTrial] = []

        for params in grid:
            experiment = _mutate_spec(spec.experiment_template, params)
            plan = compiler.build_plan(experiment)
            artifact = executor.execute_plan(plan)

            environment_report = _build_environment_report(experiment, plan)
            validation = validator.validate_run(artifact, plan, environment_report)
            evidence_bundle = build_evidence_bundle(artifact, validation, environment_report)
            policy_report = policy_eval.evaluate(evidence_bundle)
            governance.build_core_validation_report(validation, policy_report)

            objective_value = _extract_objective(validation, spec.objective)
            trials.append(
                QComputeStudyTrial(
                    trial_id=f"{spec.study_id}-{uuid.uuid4().hex[:8]}",
                    parameter_snapshot=dict(params),
                    evidence_bundle=evidence_bundle,
                    trajectory_score=objective_value,
                )
            )

        best_trial_id = _select_best_trial(trials, spec.objective)
        pareto_front = _compute_pareto_front(trials)

        return QComputeStudyReport(
            study_id=spec.study_id,
            trials=trials,
            best_trial_id=best_trial_id,
            pareto_front=pareto_front,
            convergence_analysis=_build_convergence_analysis(trials, spec.objective),
        )


def _generate_grid(spec: QComputeStudySpec) -> list[dict[str, Any]]:
    strategy: QComputeStudyStrategy = spec.strategy
    if strategy == "grid":
        return _generate_grid_cartesian(spec.axes)
    if strategy == "random":
        return _generate_random(spec.axes, spec.max_trials)
    raise ValueError(f"Unsupported study strategy: {strategy}")


def _generate_grid_cartesian(
    axes: list[QComputeStudyAxis],
) -> list[dict[str, Any]]:
    axis_values: list[list[Any]] = []
    for axis in axes:
        if axis.values is not None:
            axis_values.append(axis.values)
        elif axis.range is not None:
            lo, hi = axis.range
            step = axis.step or 1.0
            vals: list[Any] = []
            current = lo
            while current <= hi + 1e-12:
                vals.append(current)
                current += step
            axis_values.append(vals)
        else:
            axis_values.append([])

    if not axis_values or any(len(v) == 0 for v in axis_values):
        return []

    snapshots: list[dict[str, Any]] = []
    for combo in product(*axis_values):
        snapshot: dict[str, Any] = {}
        for axis, value in zip(axes, combo):
            snapshot[axis.parameter_path] = value
        snapshots.append(snapshot)
    return snapshots


def _generate_random(
    axes: list[QComputeStudyAxis],
    max_trials: int,
) -> list[dict[str, Any]]:
    snapshots: list[dict[str, Any]] = []
    for _ in range(max_trials):
        snapshot: dict[str, Any] = {}
        for axis in axes:
            if axis.values is not None:
                snapshot[axis.parameter_path] = random.choice(axis.values)
            elif axis.range is not None:
                lo, hi = axis.range
                snapshot[axis.parameter_path] = random.uniform(lo, hi)
        snapshots.append(snapshot)
    return snapshots


def _mutate_spec(
    template: QComputeExperimentSpec,
    params: dict[str, Any],
) -> QComputeExperimentSpec:
    spec = template.model_copy(deep=True)
    for path, value in params.items():
        _set_dotted(spec, path, value)
    return spec


def _set_dotted(obj: Any, path: str, value: Any) -> None:
    parts = path.split(".")
    target = obj
    for part in parts[:-1]:
        target = getattr(target, part)
    setattr(target, parts[-1], value)


def _extract_objective(
    validation: QComputeValidationReport,
    objective: QComputeObjective,
) -> float | None:
    metrics = validation.metrics
    mapping: dict[str, float | None] = {
        "fidelity": metrics.fidelity,
        "energy": metrics.energy,
        "circuit_depth": (
            float(metrics.circuit_depth_executed)
            if metrics.circuit_depth_executed is not None
            else None
        ),
        "swap_count": (
            float(metrics.swap_count_executed) if metrics.swap_count_executed is not None else None
        ),
    }
    return mapping.get(objective)


def _select_best_trial(
    trials: list[QComputeStudyTrial],
    objective: QComputeObjective,
) -> str | None:
    maximize_objectives: set[str] = {"fidelity"}
    scored = [
        (t, t.trajectory_score)
        for t in trials
        if t.evidence_bundle.validation_report.passed and t.trajectory_score is not None
    ]
    if not scored:
        return None

    reverse = objective in maximize_objectives
    scored.sort(key=lambda pair: pair[1], reverse=reverse)
    return scored[0][0].trial_id


def _compute_pareto_front(trials: list[QComputeStudyTrial]) -> list[str]:
    passed = [
        t
        for t in trials
        if t.evidence_bundle.validation_report.passed
        and t.evidence_bundle.validation_report.metrics.fidelity is not None
        and t.evidence_bundle.validation_report.metrics.circuit_depth_executed is not None
    ]
    if len(passed) < 2:
        return [t.trial_id for t in passed]

    entries = [
        (
            t,
            t.evidence_bundle.validation_report.metrics.fidelity,
            float(t.evidence_bundle.validation_report.metrics.circuit_depth_executed),
        )
        for t in passed
    ]

    pareto_ids: list[str] = []
    for i, (ti, fi, di) in enumerate(entries):
        dominated = False
        for j, (tj, fj, dj) in enumerate(entries):
            if i == j:
                continue
            if fj >= fi and dj <= di and (fj > fi or dj < di):
                dominated = True
                break
        if not dominated:
            pareto_ids.append(ti.trial_id)
    return pareto_ids


def _build_environment_report(
    experiment: QComputeExperimentSpec,
    plan: QComputeRunPlan,
) -> QComputeEnvironmentReport:
    return QComputeEnvironmentReport(
        task_id=experiment.task_id,
        backend=experiment.backend,
        available=True,
        status="online",
        qubit_count_available=experiment.backend.qubit_count,
        queue_depth=0,
        estimated_wait_seconds=0,
        calibration_fresh=True,
        prerequisite_errors=[],
        blocks_promotion=False,
    )


def _build_convergence_analysis(
    trials: list[QComputeStudyTrial],
    objective: QComputeObjective,
) -> dict[str, Any]:
    scores = [
        t.trajectory_score
        for t in trials
        if t.trajectory_score is not None and t.evidence_bundle.validation_report.passed
    ]
    if not scores:
        return {
            "objective": objective,
            "trial_count": len(trials),
            "passing_count": 0,
        }
    return {
        "objective": objective,
        "trial_count": len(trials),
        "passing_count": len(scores),
        "best_score": max(scores) if objective == "fidelity" else min(scores),
        "worst_score": min(scores) if objective == "fidelity" else max(scores),
        "score_range": max(scores) - min(scores),
    }
