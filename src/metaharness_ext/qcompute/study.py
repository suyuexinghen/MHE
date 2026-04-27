from __future__ import annotations

import random
import uuid
from concurrent.futures import ThreadPoolExecutor
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


def trial_to_domain_payload(trial: QComputeStudyTrial) -> dict[str, Any]:
    """Convert a study trial to a domain_payload compatible dict for MutationProposal."""
    bundle = trial.evidence_bundle
    validation = bundle.validation_report
    return {
        "trial_id": trial.trial_id,
        "parameters": trial.parameter_snapshot,
        "trajectory_score": trial.trajectory_score,
        "validation_status": validation.status.value,
        "fidelity": validation.metrics.fidelity,
        "energy_error": validation.metrics.energy_error,
        "circuit_depth": validation.metrics.circuit_depth_executed,
        "backend": bundle.run_artifact.backend_actual,
    }


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

        # Quota-aware ordering: simulator trials first
        grid = _schedule_trials(grid, spec)

        grid = grid[: spec.max_trials]

        policy_eval = QComputeEvidencePolicy()
        governance = QComputeGovernanceAdapter()
        worker_count = max(1, min(spec.parallel_workers, len(grid))) if grid else 1

        if worker_count == 1:
            trials = [
                _run_trial(
                    params,
                    spec=spec,
                    compiler=compiler,
                    executor=executor,
                    validator=validator,
                    policy_eval=policy_eval,
                    governance=governance,
                )
                for params in grid
            ]
        else:
            with ThreadPoolExecutor(max_workers=worker_count) as pool:
                trials = list(
                    pool.map(
                        lambda params: _run_trial(
                            params,
                            spec=spec,
                            compiler=compiler,
                            executor=executor,
                            validator=validator,
                            policy_eval=policy_eval,
                            governance=governance,
                        ),
                        grid,
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


def _run_trial(
    params: dict[str, Any],
    *,
    spec: QComputeStudySpec,
    compiler: QComputeConfigCompilerComponent,
    executor: QComputeExecutorComponent,
    validator: QComputeValidatorComponent,
    policy_eval: QComputeEvidencePolicy,
    governance: QComputeGovernanceAdapter,
) -> QComputeStudyTrial:
    experiment = _mutate_spec(spec.experiment_template, params)
    plan = compiler.build_plan(experiment)
    artifact = executor.execute_plan(plan)

    environment_report = _build_environment_report(experiment, plan)
    validation = validator.validate_run(artifact, plan, environment_report)
    evidence_bundle = build_evidence_bundle(artifact, validation, environment_report)
    policy_report = policy_eval.evaluate(evidence_bundle)
    governance.build_core_validation_report(validation, policy_report)

    objective_value = _extract_objective(validation, spec.objective)
    return QComputeStudyTrial(
        trial_id=f"{spec.study_id}-{uuid.uuid4().hex[:8]}",
        parameter_snapshot=dict(params),
        evidence_bundle=evidence_bundle,
        trajectory_score=objective_value,
    )


def _generate_grid(spec: QComputeStudySpec) -> list[dict[str, Any]]:
    strategy: QComputeStudyStrategy = spec.strategy
    if strategy == "grid":
        return _generate_grid_cartesian(spec.axes)
    if strategy == "random":
        return _generate_random(spec.axes, spec.max_trials)
    if strategy == "bayesian":
        return _generate_bayesian(spec)
    if strategy == "agentic":
        return _generate_agentic(spec)
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


def _random_params(axes: list[QComputeStudyAxis], rng: random.Random) -> dict[str, Any]:
    """Generate random parameters from axis specifications."""
    params: dict[str, Any] = {}
    for axis in axes:
        if axis.values is not None:
            params[axis.parameter_path] = rng.choice(axis.values)
        elif axis.range is not None:
            lo, hi = axis.range
            params[axis.parameter_path] = rng.uniform(lo, hi)
    return params


def _generate_bayesian(spec: QComputeStudySpec) -> list[dict[str, Any]]:
    candidates = _generate_grid_cartesian(spec.axes)
    if not candidates:
        return []

    selected: list[dict[str, Any]] = []
    selected_keys: set[tuple[tuple[str, str], ...]] = set()
    while len(selected) < spec.max_trials:
        candidate = candidates[_bayesian_candidate_index(candidates, selected)]
        candidate_key = _params_key(candidate)
        if candidate_key in selected_keys:
            break
        selected.append(candidate)
        selected_keys.add(candidate_key)
        if len(selected_keys) == len(candidates):
            break
    return selected


def _bayesian_candidate_index(
    candidates: list[dict[str, Any]],
    selected: list[dict[str, Any]],
) -> int:
    if not selected:
        return len(candidates) // 2

    selected_keys = {_params_key(params) for params in selected}
    best_index = 0
    best_distance = -1.0
    for index, candidate in enumerate(candidates):
        if _params_key(candidate) in selected_keys:
            continue
        distance = min(_surrogate_distance(candidate, params) for params in selected)
        if distance > best_distance:
            best_index = index
            best_distance = distance
    return best_index


def _surrogate_distance(left: dict[str, Any], right: dict[str, Any]) -> float:
    distance = 0.0
    for key, left_value in left.items():
        right_value = right.get(key)
        if isinstance(left_value, (int, float)) and isinstance(right_value, (int, float)):
            distance += float(left_value - right_value) ** 2
        elif left_value != right_value:
            distance += 1.0
    return distance


def _params_key(params: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((key, repr(value)) for key, value in params.items()))


class FunctionalBrainProvider:
    """Simplified BrainProvider for agentic study strategy.

    Proposes parameter mutations by adding Gaussian noise to the
    best previous trial's parameters.
    """

    def __init__(self, *, noise_scale: float = 0.1, seed: int | None = None) -> None:
        self._noise_scale = noise_scale
        self._rng = random.Random(seed)

    def propose(
        self,
        axes: list[QComputeStudyAxis],
        best_params: dict[str, Any] | None,
        n_proposals: int = 3,
    ) -> list[dict[str, Any]]:
        """Generate parameter proposals by perturbing best known params."""
        if best_params is None:
            # Random initialization
            return [_random_params(axes, self._rng) for _ in range(n_proposals)]
        proposals: list[dict[str, Any]] = []
        for _ in range(n_proposals):
            proposal = dict(best_params)
            for key, value in proposal.items():
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    perturbed = value + self._rng.gauss(
                        0,
                        self._noise_scale * abs(value) if value != 0 else self._noise_scale,
                    )
                    proposal[key] = int(round(perturbed)) if isinstance(value, int) else perturbed
            proposals.append(proposal)
        return proposals


def _generate_agentic(spec: QComputeStudySpec) -> list[dict[str, Any]]:
    """Generate parameters using agentic exploration with FunctionalBrainProvider."""
    brain = FunctionalBrainProvider()
    proposals: list[dict[str, Any]] = []
    best_params: dict[str, Any] | None = None

    # Start with random exploration
    initial = brain.propose(spec.axes, best_params, n_proposals=min(3, spec.max_trials))
    proposals.extend(initial[: spec.max_trials])
    best_params = initial[0] if initial else None

    # Iterative refinement
    while len(proposals) < spec.max_trials:
        remaining = spec.max_trials - len(proposals)
        new_proposals = brain.propose(spec.axes, best_params, n_proposals=min(3, remaining))
        if not new_proposals:
            break
        proposals.extend(new_proposals)
        best_params = new_proposals[0]

    return proposals[: spec.max_trials]


def _schedule_trials(grid: list[dict[str, Any]], spec: QComputeStudySpec) -> list[dict[str, Any]]:
    """Reorder trials: simulator backends first, then real hardware.

    Within each group, preserve original order.
    """
    template = spec.experiment_template
    template_platform = template.backend.platform

    # If all trials use the same backend, no reordering needed
    sim_platforms = {"qiskit_aer", "pennylane_aer"}
    if template_platform in sim_platforms:
        # Check if any axis varies the backend platform
        has_backend_axis = any(
            "backend.platform" in (a.parameter_path or "") or "platform" in (a.parameter_path or "")
            for a in spec.axes
        )
        if not has_backend_axis:
            return grid

    # Split into simulator and real hardware groups
    sim_trials: list[dict[str, Any]] = []
    real_trials: list[dict[str, Any]] = []
    for params in grid:
        platform = params.get("backend.platform", template_platform)
        if platform in sim_platforms:
            sim_trials.append(params)
        else:
            real_trials.append(params)

    return sim_trials + real_trials


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
