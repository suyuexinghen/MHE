from __future__ import annotations

from metaharness_ext.moose.contracts import (
    MooseInputSpec,
    MooseProblemSpec,
    MooseRunArtifact,
    MooseRunPlan,
    MooseStudyAxis,
    MooseStudySpec,
    MooseValidationReport,
)
from metaharness_ext.moose.study import MooseStudyComponent
from metaharness_ext.moose.types import MooseValidationStatus


def _template() -> MooseProblemSpec:
    return MooseProblemSpec(
        task_id="study-task",
        input=MooseInputSpec(mode="inline", inline_source="[Mesh]\n[]\n", mesh_only=False),
    )


class _Compiler:
    def compile(self, spec: MooseProblemSpec, *, run_id: str, workspace_dir: str) -> MooseRunPlan:
        return MooseRunPlan(
            plan_id=f"plan-{run_id}",
            task_id=spec.task_id,
            run_id=run_id,
            spec=spec,
            workspace_dir=workspace_dir,
            input_filename=spec.input.input_filename,
            input_source=spec.input.inline_source or "",
            command=["moose-opt", "-i", spec.input.input_filename],
        )


class _Executor:
    def execute_plan(self, plan: MooseRunPlan) -> MooseRunArtifact:
        output_count = 1 if plan.spec.input.mesh_only else 0
        return MooseRunArtifact(
            artifact_id=f"artifact-{plan.run_id}",
            run_id=plan.run_id,
            task_id=plan.task_id,
            plan_ref=plan.plan_id,
            status="completed",
            return_code=0,
            working_directory=plan.workspace_dir,
            summary_metrics={"output_count": output_count},
        )


class _Validator:
    def validate_run(self, artifact: MooseRunArtifact, plan: MooseRunPlan) -> MooseValidationReport:
        return MooseValidationReport(
            task_id=artifact.task_id,
            plan_ref=plan.plan_id,
            artifact_ref=artifact.artifact_id,
            passed=True,
            status=MooseValidationStatus.EXECUTED,
            summary_metrics=dict(artifact.summary_metrics),
        )


def test_moose_study_sweeps_nested_spec_parameters() -> None:
    study = MooseStudySpec(
        study_id="mesh-mode-sweep",
        task_template=_template(),
        axes=[MooseStudyAxis(parameter_path="input.mesh_only", values=[False, True])],
        objective="output_count",
        goal="maximize",
    )

    report = MooseStudyComponent(_Compiler(), _Executor(), _Validator()).run_study(study)

    assert report.summary_metrics == {"total_trials": 2, "passed_trials": 2}
    assert report.best_trial_id == "mesh-mode-sweep-trial-1"
    assert report.recommended_parameters == {"input.mesh_only": True}
