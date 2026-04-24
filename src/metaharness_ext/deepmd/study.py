from __future__ import annotations

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.deepmd.capabilities import CAP_DEEPMD_STUDY
from metaharness_ext.deepmd.contracts import (
    DeepMDStudyReport,
    DeepMDStudySpec,
    DeepMDStudyTrial,
    DeepMDTrainSpec,
    DeepMDValidationReport,
    DPGenRunSpec,
    DPGenSimplifySpec,
)
from metaharness_ext.deepmd.evidence import build_evidence_bundle
from metaharness_ext.deepmd.executor import DeepMDExecutorComponent
from metaharness_ext.deepmd.governance import DeepMDGovernanceAdapter
from metaharness_ext.deepmd.policy import DeepMDEvidencePolicy
from metaharness_ext.deepmd.slots import DEEPMD_STUDY_SLOT
from metaharness_ext.deepmd.train_config_compiler import DeepMDTrainConfigCompilerComponent
from metaharness_ext.deepmd.validator import DeepMDValidatorComponent


class DeepMDStudyComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(DEEPMD_STUDY_SLOT)
        api.declare_input("study", "DeepMDStudySpec")
        api.declare_output("report", "DeepMDStudyReport", mode="sync")
        api.provide_capability(CAP_DEEPMD_STUDY)

    def run_study(
        self,
        spec: DeepMDStudySpec,
        *,
        compiler: DeepMDTrainConfigCompilerComponent,
        executor: DeepMDExecutorComponent,
        validator: DeepMDValidatorComponent,
    ) -> DeepMDStudyReport:
        trials: list[DeepMDStudyTrial] = []
        policy = DeepMDEvidencePolicy()
        governance = DeepMDGovernanceAdapter()
        for value in spec.axis.values:
            trial_task = self._mutate_task(spec, value)
            plan = compiler.build_plan(trial_task)
            run = executor.execute_plan(plan)
            validation = validator.validate_run(run)
            evidence_bundle = build_evidence_bundle(run, validation)
            policy_report = policy.evaluate(evidence_bundle)
            core_validation_report = governance.build_core_validation_report(validation, policy_report)
            candidate_record = governance.build_candidate_record(evidence_bundle, policy_report)
            metric_value = self._extract_metric(validation, spec.metric_key)
            trials.append(
                DeepMDStudyTrial(
                    trial_id=run.run_id,
                    task_id=run.task_id,
                    axis_kind=spec.axis.kind,
                    axis_value=value,
                    mutated_parameters={spec.axis.kind: value},
                    run=run,
                    validation=validation,
                    evidence_bundle=evidence_bundle,
                    policy_report=policy_report,
                    core_validation_report=core_validation_report,
                    candidate_record=candidate_record,
                    metric_value=metric_value,
                    passed=validation.passed,
                    messages=list(validation.messages),
                )
            )

        recommended = self._recommend_trial(trials, goal=spec.goal)
        summary_metrics: dict[str, float | str] = {"trial_count": float(len(trials))}
        if recommended is not None and recommended.metric_value is not None:
            summary_metrics[f"best_{spec.metric_key}"] = recommended.metric_value

        return DeepMDStudyReport(
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
            messages=[]
            if recommended is not None
            else ["No passing trial produced the requested metric."],
        )

    def _mutate_task(
        self, spec: DeepMDStudySpec, value: int | float
    ) -> DeepMDTrainSpec | DPGenRunSpec | DPGenSimplifySpec:
        task = spec.base_task.model_copy(deep=True)
        task.task_id = f"{spec.task_id}__study__{spec.axis.kind}__{value}"

        if isinstance(task, DeepMDTrainSpec):
            if spec.axis.kind == "numb_steps":
                task.training["numb_steps"] = int(value)
            elif spec.axis.kind == "rcut":
                task.descriptor.rcut = float(value)
            elif spec.axis.kind == "rcut_smth":
                task.descriptor.rcut_smth = float(value)
            elif spec.axis.kind == "sel":
                task.descriptor.sel = [int(value)]
            else:
                raise NotImplementedError(
                    f"Axis {spec.axis.kind} is not supported for DeepMDTrainSpec"
                )
            return task

        if isinstance(task, DPGenSimplifySpec):
            if spec.axis.kind == "relabeling.pick_number":
                task.relabeling["pick_number"] = int(value)
            else:
                raise NotImplementedError(
                    f"Axis {spec.axis.kind} is not supported for DPGenSimplifySpec"
                )
            return task

        if spec.axis.kind == "model_devi_f_trust_lo":
            task.param["model_devi_f_trust_lo"] = float(value)
        elif spec.axis.kind == "model_devi_f_trust_hi":
            task.param["model_devi_f_trust_hi"] = float(value)
        else:
            raise NotImplementedError(f"Axis {spec.axis.kind} is not supported for DPGenRunSpec")
        return task

    def _extract_metric(self, validation: DeepMDValidationReport, metric_key: str) -> float | None:
        value = validation.summary_metrics.get(metric_key)
        if isinstance(value, int | float):
            return float(value)
        return None

    def _recommend_trial(
        self, trials: list[DeepMDStudyTrial], *, goal: str
    ) -> DeepMDStudyTrial | None:
        candidates = [trial for trial in trials if trial.passed and trial.metric_value is not None]
        if not candidates:
            return None
        reverse = goal == "maximize"
        return sorted(candidates, key=lambda trial: trial.metric_value, reverse=reverse)[0]
