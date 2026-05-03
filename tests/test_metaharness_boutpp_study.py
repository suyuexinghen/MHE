from __future__ import annotations

from metaharness_ext.boutpp.contracts import (
    BoutPPProblemSpec,
    BoutPPRunArtifact,
    BoutPPStudyAxis,
    BoutPPStudySpec,
    BoutPPValidationReport,
)
from metaharness_ext.boutpp.study import BoutPPStudyComponent


class FakeCompiler:
    def __init__(self):
        self.specs = []

    def compile(self, spec, run_id: str, workspace_dir: str):
        self.specs.append(spec)
        return type(
            "Plan",
            (),
            {
                "plan_id": f"plan-{run_id}",
                "task_id": spec.task_id,
                "run_id": run_id,
                "spec": spec,
                "workspace_dir": workspace_dir,
                "data_dir": f"{workspace_dir}/data",
                "bout_inp_content": "",
                "command": ["/bin/true", "-d", f"{workspace_dir}/data"],
            },
        )()


class FakeExecutor:
    def execute(self, plan):
        metric = plan.spec.options["solver"]["atol"] if "solver" in plan.spec.options else 1.0
        return BoutPPRunArtifact(
            artifact_id=f"artifact-{plan.run_id}",
            run_id=plan.run_id,
            task_id=plan.task_id,
            plan_ref=plan.plan_id,
            status="completed",
            summary_metrics={"runtime_seconds": float(metric)},
        )


class FakePostprocess:
    def postprocess(self, artifact):
        return type(
            "Postprocess",
            (),
            {"report_id": f"post-{artifact.run_id}", "summary_metrics": artifact.summary_metrics, "warnings": [], "variable_names": ["T"]},
        )()


class FakeValidator:
    def validate(self, artifact, plan_ref: str = "", postprocess=None, validation_spec=None):
        return BoutPPValidationReport(
            task_id=artifact.task_id,
            plan_ref=plan_ref,
            artifact_ref=artifact.artifact_id,
            postprocess_ref=postprocess.report_id if postprocess else None,
            passed=True,
            summary_metrics={"runtime_seconds": artifact.summary_metrics["runtime_seconds"]},
        )


def test_study_runs_cartesian_trials():
    study = BoutPPStudyComponent(FakeCompiler(), FakeExecutor(), FakePostprocess(), FakeValidator())
    spec = BoutPPStudySpec(
        study_id="study-1",
        task_template=BoutPPProblemSpec(task_id="task-1", options={"solver": {"atol": 1.0}}),
        axes=[BoutPPStudyAxis(parameter_path="options.solver.atol", values=[1.0, 0.5])],
        objective="runtime_seconds",
    )
    report = study.run_study(spec)
    assert len(report.trials) == 2
    assert report.best_trial_id is not None
    assert report.recommended_parameters is not None


def test_snapshot_generation_empty_axes():
    study = BoutPPStudyComponent(FakeCompiler(), FakeExecutor(), FakePostprocess(), FakeValidator())
    spec = BoutPPStudySpec(study_id="study-1", task_template=BoutPPProblemSpec(task_id="task-1"))
    assert study._generate_snapshots(spec) == [{}]
