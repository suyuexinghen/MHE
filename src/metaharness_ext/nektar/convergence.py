from __future__ import annotations

import math
from pathlib import Path

from metaharness.core.models import ScoredEvidence
from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.nektar.analyzers import (
    parse_filter_outputs,
    parse_solver_log,
    summarize_reference_error,
)
from metaharness_ext.nektar.capabilities import CAP_NEKTAR_CONVERGENCE_STUDY
from metaharness_ext.nektar.contracts import (
    ConvergenceStudyReport,
    ConvergenceStudySpec,
    ConvergenceTrialReport,
    ErrorSummary,
    FilterOutputAnalysis,
    FilterOutputSummary,
    NektarProblemSpec,
    NektarRunArtifact,
    NektarValidationReport,
    SolverLogAnalysis,
)
from metaharness_ext.nektar.postprocess import PostprocessComponent
from metaharness_ext.nektar.session_compiler import build_session_plan
from metaharness_ext.nektar.slots import CONVERGENCE_STUDY_SLOT
from metaharness_ext.nektar.solver_executor import SolverExecutorComponent
from metaharness_ext.nektar.validator import NektarValidatorComponent


class ConvergenceStudyComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(CONVERGENCE_STUDY_SLOT)
        api.declare_input("study", "ConvergenceStudySpec")
        api.declare_output("report", "ConvergenceStudyReport", mode="sync")
        api.provide_capability(CAP_NEKTAR_CONVERGENCE_STUDY)

    def run_study(
        self,
        spec: ConvergenceStudySpec,
        *,
        executor: SolverExecutorComponent,
        postprocessor: PostprocessComponent,
        validator: NektarValidatorComponent,
    ) -> ConvergenceStudyReport:
        if spec.axis.kind != "num_modes":
            raise NotImplementedError(f"Unsupported convergence axis: {spec.axis.kind}")
        if len(spec.axis.values) < spec.min_points:
            raise ValueError("Convergence study requires at least min_points axis values")
        self._validate_rule_inputs(spec)

        trials: list[ConvergenceTrialReport] = []
        for value in spec.axis.values:
            trial = self._run_single_trial(
                spec,
                value,
                executor=executor,
                postprocessor=postprocessor,
                validator=validator,
            )
            trials.append(trial)
            if spec.stop_on_first_pass and self._should_stop_after_trial(trials, spec):
                break

        recommended, converged, recommended_reason = self._evaluate_recommendation(trials, spec)
        metric_series = self._collect_metric_series(trials)
        error_sequence = [
            trial.metric_value for trial in metric_series if trial.metric_value is not None
        ]
        drop_ratios = self._compute_drop_ratios(metric_series)
        observed_order = self._compute_observed_order(metric_series)
        messages = self._build_report_messages(
            trials, recommended, spec, recommended_reason, converged
        )
        summary_metrics = self._build_summary_metrics(
            trials,
            recommended,
            spec,
            observed_order=observed_order,
            drop_ratios=drop_ratios,
        )
        return ConvergenceStudyReport(
            study_id=spec.study_id,
            task_id=spec.task_id,
            axis_kind=spec.axis.kind,
            metric_key=spec.metric_key,
            trials=trials,
            recommended_value=recommended.axis_value if recommended is not None else None,
            recommended_trial_id=recommended.trial_id if recommended is not None else None,
            converged=converged,
            observed_order=observed_order,
            recommended_reason=recommended_reason,
            error_sequence=error_sequence,
            drop_ratios=drop_ratios,
            messages=messages,
            summary_metrics=summary_metrics,
        )

    def _run_single_trial(
        self,
        spec: ConvergenceStudySpec,
        axis_value: int,
        *,
        executor: SolverExecutorComponent,
        postprocessor: PostprocessComponent,
        validator: NektarValidatorComponent,
    ) -> ConvergenceTrialReport:
        trial_task_id = self._build_trial_task_id(spec, axis_value)
        try:
            problem = self._mutate_problem_num_modes(spec, axis_value)
            plan = build_session_plan(problem)
            run = executor.execute_plan(plan)
            run = postprocessor.run_postprocess(run)
            validation = validator.validate_run(run)
            return self._build_trial_report(spec, axis_value, plan.plan_id, run, validation)
        except Exception as error:
            return self._build_failed_trial_report(spec, axis_value, trial_task_id, error)

    def _validate_rule_inputs(self, spec: ConvergenceStudySpec) -> None:
        if spec.convergence_rule == "absolute" and spec.target_tolerance is None:
            raise ValueError("absolute convergence_rule requires target_tolerance")
        if spec.relative_drop_ratio <= 0 or spec.relative_drop_ratio >= 1:
            raise ValueError("relative_drop_ratio must be between 0 and 1")
        if spec.plateau_tolerance < 0:
            raise ValueError("plateau_tolerance must be non-negative")

    def _mutate_problem_num_modes(
        self, spec: ConvergenceStudySpec, value: int
    ) -> NektarProblemSpec:
        problem = spec.base_problem.model_copy(deep=True)
        problem.task_id = self._build_trial_task_id(spec, value)
        problem.parameters["NumModes"] = value
        if spec.postprocess_plan_override is not None:
            problem.postprocess_plan = [dict(step) for step in spec.postprocess_plan_override]
        return problem

    def _build_trial_task_id(self, spec: ConvergenceStudySpec, value: int) -> str:
        return f"{spec.task_id}__study__{spec.axis.kind}__{value}"

    def _build_trial_report(
        self,
        spec: ConvergenceStudySpec,
        axis_value: int,
        plan_id: str,
        run: NektarRunArtifact,
        validation: NektarValidationReport,
    ) -> ConvergenceTrialReport:
        solver_log_analysis, filter_output_analysis, error_summary = self._build_trial_analyses(
            spec, run, validation
        )
        metric_value = self._resolve_trial_metric(validation, run, spec.metric_key)
        messages = list(validation.messages)
        messages.extend(error_summary.messages)
        return ConvergenceTrialReport(
            trial_id=run.run_id,
            task_id=run.task_id,
            axis_kind=spec.axis.kind,
            axis_value=axis_value,
            mutated_parameters={"NumModes": axis_value},
            plan_id=plan_id,
            run=run,
            validation=validation,
            solver_log_analysis=solver_log_analysis,
            filter_output_analysis=filter_output_analysis,
            error_summary=error_summary,
            metric_value=metric_value,
            status=run.status,
            passed=validation.passed,
            messages=messages,
        )

    def _build_failed_trial_report(
        self,
        spec: ConvergenceStudySpec,
        axis_value: int,
        trial_task_id: str,
        error: Exception,
    ) -> ConvergenceTrialReport:
        run = NektarRunArtifact(
            run_id=f"run::{trial_task_id}",
            task_id=trial_task_id,
            solver_family=spec.base_problem.solver_family,
            solver_binary="",
            filter_output=FilterOutputSummary(),
            result_summary={"fallback_reason": type(error).__name__},
            status="failed",
            graph_metadata=dict(spec.base_problem.graph_metadata),
            candidate_identity=spec.base_problem.candidate_identity.model_copy(deep=True),
            promotion_metadata=spec.base_problem.promotion_metadata.model_copy(deep=True),
            checkpoint_refs=list(spec.base_problem.checkpoint_refs),
            provenance_refs=list(spec.base_problem.provenance_refs),
            scored_evidence=ScoredEvidence(
                score=0.0,
                evidence_refs=list(
                    dict.fromkeys(
                        [
                            *spec.base_problem.checkpoint_refs,
                            *spec.base_problem.trace_refs,
                            *spec.base_problem.provenance_refs,
                        ]
                    )
                ),
                reasons=[type(error).__name__],
                attributes={"status": "failed", "task_id": trial_task_id},
            ),
            execution_policy=spec.base_problem.execution_policy.model_copy(deep=True),
        )
        validation = NektarValidationReport(
            task_id=trial_task_id,
            passed=False,
            solver_exited_cleanly=False,
            field_files_exist=False,
            error_vs_reference=None,
            messages=[str(error)],
            metrics={},
            checkpoint_refs=list(run.checkpoint_refs),
            provenance_refs=list(run.provenance_refs),
            trace_refs=list(run.trace_refs),
            scored_evidence=ScoredEvidence(
                score=0.0,
                evidence_refs=list(
                    dict.fromkeys([*run.checkpoint_refs, *run.trace_refs, *run.provenance_refs])
                ),
                reasons=[str(error)],
                attributes={"status": "failed", "fallback_reason": type(error).__name__},
            ),
        )
        error_summary = ErrorSummary(
            status="no_reference_error",
            messages=["Reference error summary unavailable for failed trial."],
        )
        return ConvergenceTrialReport(
            trial_id=run.run_id,
            task_id=trial_task_id,
            axis_kind=spec.axis.kind,
            axis_value=axis_value,
            mutated_parameters={"NumModes": axis_value},
            plan_id=f"plan::{trial_task_id}",
            run=run,
            validation=validation,
            solver_log_analysis=SolverLogAnalysis(path="", exists=False),
            filter_output_analysis=FilterOutputAnalysis(),
            error_summary=error_summary,
            metric_value=None,
            status="failed",
            passed=False,
            messages=[str(error)],
        )

    def _build_trial_analyses(
        self,
        spec: ConvergenceStudySpec,
        run: NektarRunArtifact,
        validation: NektarValidationReport,
    ) -> tuple[SolverLogAnalysis, FilterOutputAnalysis, ErrorSummary]:
        solver_log_path = self._resolve_solver_log_path(run)
        solver_log_analysis = (
            parse_solver_log(solver_log_path)
            if solver_log_path is not None
            else SolverLogAnalysis(path="", exists=False)
        )
        output_paths = [*run.derived_files, *run.field_files, *run.filter_output.checkpoint_files]
        filter_output_analysis = parse_filter_outputs(output_paths)
        metrics = dict(validation.metrics)
        if spec.target_tolerance is not None:
            metrics["error_tolerance"] = spec.target_tolerance
        error_summary = summarize_reference_error(metrics)
        return solver_log_analysis, filter_output_analysis, error_summary

    def _resolve_solver_log_path(self, run: NektarRunArtifact) -> str | None:
        for log_file in run.log_files:
            path = Path(log_file)
            if path.name == "solver.log":
                return str(path)
        return None

    def _resolve_trial_metric(
        self,
        validation: NektarValidationReport,
        run: NektarRunArtifact,
        metric_key: str,
    ) -> float | None:
        for source in (
            validation.metrics,
            run.filter_output.error_norms,
            run.filter_output.metrics,
        ):
            value = source.get(metric_key)
            if value is None:
                continue
            try:
                return float(value)
            except (TypeError, ValueError):
                continue
        return None

    def _collect_metric_series(
        self,
        trials: list[ConvergenceTrialReport],
    ) -> list[ConvergenceTrialReport]:
        return [
            trial
            for trial in trials
            if trial.status == "completed"
            and trial.metric_value is not None
            and trial.metric_value > 0
        ]

    def _compute_drop_ratios(self, series: list[ConvergenceTrialReport]) -> list[float]:
        ratios: list[float] = []
        for previous, current in zip(series, series[1:], strict=False):
            if (
                previous.metric_value is None
                or current.metric_value is None
                or previous.metric_value <= 0
            ):
                continue
            ratios.append(current.metric_value / previous.metric_value)
        return ratios

    def _compute_local_orders(self, series: list[ConvergenceTrialReport]) -> list[float]:
        orders: list[float] = []
        for previous, current in zip(series, series[1:], strict=False):
            if previous.metric_value is None or current.metric_value is None:
                continue
            if previous.metric_value <= 0 or current.metric_value <= 0:
                continue
            if current.axis_value <= previous.axis_value:
                continue
            numerator = previous.metric_value / current.metric_value
            denominator = current.axis_value / previous.axis_value
            if numerator <= 0 or denominator <= 0 or denominator == 1:
                continue
            orders.append(math.log(numerator) / math.log(denominator))
        return orders

    def _compute_observed_order(self, series: list[ConvergenceTrialReport]) -> float | None:
        orders = self._compute_local_orders(series)
        if len(orders) >= 2:
            return sum(orders[-2:]) / 2
        if orders:
            return orders[-1]
        return None

    def _evaluate_recommendation(
        self,
        trials: list[ConvergenceTrialReport],
        spec: ConvergenceStudySpec,
    ) -> tuple[ConvergenceTrialReport | None, bool, str | None]:
        metric_series = self._collect_metric_series(trials)
        if spec.convergence_rule == "absolute":
            return self._evaluate_absolute_rule(trials, metric_series, spec)
        if spec.convergence_rule == "relative_drop":
            return self._evaluate_relative_drop_rule(trials, metric_series, spec)
        return self._evaluate_plateau_rule(trials, metric_series, spec)

    def _evaluate_absolute_rule(
        self,
        trials: list[ConvergenceTrialReport],
        metric_series: list[ConvergenceTrialReport],
        spec: ConvergenceStudySpec,
    ) -> tuple[ConvergenceTrialReport | None, bool, str | None]:
        for trial in metric_series:
            if (
                trial.passed
                and trial.metric_value is not None
                and trial.metric_value <= float(spec.target_tolerance)
            ):
                return (
                    trial,
                    True,
                    (f"First trial meeting absolute tolerance {float(spec.target_tolerance):.6g}."),
                )
        fallback = self._fallback_trial(trials)
        if fallback is None:
            return None, False, None
        return (
            fallback,
            False,
            "No trial met the absolute tolerance; using the best available metric.",
        )

    def _evaluate_relative_drop_rule(
        self,
        trials: list[ConvergenceTrialReport],
        metric_series: list[ConvergenceTrialReport],
        spec: ConvergenceStudySpec,
    ) -> tuple[ConvergenceTrialReport | None, bool, str | None]:
        for previous, current in zip(metric_series, metric_series[1:], strict=False):
            if (
                previous.metric_value is None
                or current.metric_value is None
                or previous.metric_value <= 0
            ):
                continue
            ratio = current.metric_value / previous.metric_value
            if ratio <= spec.relative_drop_ratio and current.passed:
                return (
                    current,
                    True,
                    (
                        f"Error ratio {ratio:.6g} met relative_drop threshold {spec.relative_drop_ratio:.6g}."
                    ),
                )
        fallback = self._fallback_trial(trials)
        if fallback is None:
            return None, False, None
        return (
            fallback,
            False,
            "No adjacent trial pair met the relative_drop threshold; using the best available metric.",
        )

    def _evaluate_plateau_rule(
        self,
        trials: list[ConvergenceTrialReport],
        metric_series: list[ConvergenceTrialReport],
        spec: ConvergenceStudySpec,
    ) -> tuple[ConvergenceTrialReport | None, bool, str | None]:
        if not self._is_monotone_nonincreasing(metric_series):
            fallback = self._fallback_trial(trials)
            if fallback is None:
                return None, False, None
            return (
                fallback,
                False,
                "Metric sequence is not monotone non-increasing; plateau was not evaluated.",
            )
        ratios = self._compute_drop_ratios(metric_series)
        for index in range(1, len(ratios)):
            delta = abs(ratios[index] - ratios[index - 1])
            if delta < spec.plateau_tolerance:
                recommended = metric_series[index + 1]
                if recommended.passed:
                    return (
                        recommended,
                        True,
                        (
                            f"Drop-ratio change {delta:.6g} was within plateau tolerance"
                            f" {spec.plateau_tolerance:.6g}."
                        ),
                    )
        fallback = self._fallback_trial(trials)
        if fallback is None:
            return None, False, None
        return (
            fallback,
            False,
            "No plateau condition was detected; using the best available metric.",
        )

    def _fallback_trial(
        self, trials: list[ConvergenceTrialReport]
    ) -> ConvergenceTrialReport | None:
        completed_with_metric = [
            trial
            for trial in trials
            if trial.status == "completed" and trial.metric_value is not None
        ]
        if completed_with_metric:
            return min(completed_with_metric, key=lambda trial: trial.metric_value or float("inf"))
        if trials:
            return trials[-1]
        return None

    def _is_monotone_nonincreasing(self, series: list[ConvergenceTrialReport]) -> bool:
        metric_values = [trial.metric_value for trial in series if trial.metric_value is not None]
        return all(
            current <= previous
            for previous, current in zip(metric_values, metric_values[1:], strict=False)
        )

    def _should_stop_after_trial(
        self,
        trials: list[ConvergenceTrialReport],
        spec: ConvergenceStudySpec,
    ) -> bool:
        _, converged, _ = self._evaluate_recommendation(trials, spec)
        return converged

    def _build_report_messages(
        self,
        trials: list[ConvergenceTrialReport],
        recommended: ConvergenceTrialReport | None,
        spec: ConvergenceStudySpec,
        recommended_reason: str | None,
        converged: bool,
    ) -> list[str]:
        messages = [f"Executed {len(trials)} convergence trial(s)."]
        messages.append(f"Applied convergence rule '{spec.convergence_rule}'.")
        if recommended is None:
            messages.append("No recommended convergence level could be determined.")
            return messages
        messages.append(f"Recommended NumModes={recommended.axis_value}.")
        if recommended_reason is not None:
            messages.append(recommended_reason)
        if not converged:
            messages.append(
                "Recommendation is a best-available fallback rather than a converged result."
            )
        return messages

    def _build_summary_metrics(
        self,
        trials: list[ConvergenceTrialReport],
        recommended: ConvergenceTrialReport | None,
        spec: ConvergenceStudySpec,
        *,
        observed_order: float | None,
        drop_ratios: list[float],
    ) -> dict[str, float | str]:
        metrics: dict[str, float | str] = {
            "trial_count": float(len(trials)),
            "passed_count": float(sum(1 for trial in trials if trial.passed)),
            "failed_count": float(sum(1 for trial in trials if not trial.passed)),
        }
        metric_values = [trial.metric_value for trial in trials if trial.metric_value is not None]
        if metric_values:
            metrics["best_metric_value"] = min(metric_values)
        if recommended is not None:
            metrics["recommended_value"] = float(recommended.axis_value)
        if observed_order is not None:
            metrics["observed_order"] = observed_order
        if drop_ratios:
            metrics["last_drop_ratio"] = drop_ratios[-1]
        if spec.target_tolerance is not None:
            metrics["target_tolerance"] = spec.target_tolerance
        if spec.convergence_rule == "relative_drop":
            metrics["relative_drop_ratio"] = spec.relative_drop_ratio
        if spec.convergence_rule == "plateau":
            metrics["plateau_tolerance"] = spec.plateau_tolerance
        return metrics
