from __future__ import annotations

from metaharness_ext.pycfd.contracts import (
    PyCFDProblemSpec,
    PyCFDRunArtifact,
    PyCFDRunPlan,
    PyCFDStudyAxis,
    PyCFDStudySpec,
    PyCFDValidationReport,
)
from metaharness_ext.pycfd.study import PyCFDStudyComponent


class DummyCompiler:
    pass


class DummyExecutor:
    pass


class DummyValidator:
    pass


class FakeCompiler:
    def __init__(self):
        self.specs: list[PyCFDProblemSpec] = []

    def compile(self, spec: PyCFDProblemSpec, run_id: str, workspace_dir: str) -> PyCFDRunPlan:
        self.specs.append(spec)
        return PyCFDRunPlan(
            plan_id=f"plan-{run_id}",
            task_id=spec.task_id,
            run_id=run_id,
            spec=spec,
            workspace_dir=workspace_dir,
            script_source="print('fake')",
        )


class FakeExecutor:
    def execute(self, plan: PyCFDRunPlan) -> PyCFDRunArtifact:
        residual = 1.0 / plan.spec.mesh.nx
        return PyCFDRunArtifact(
            artifact_id=f"artifact-{plan.run_id}",
            run_id=plan.run_id,
            task_id=plan.task_id,
            plan_ref=plan.plan_id,
            case_type=plan.spec.case_type,
            status="completed",
            residual_l1=residual,
            residual_l2=residual,
            summary_metrics={"residual_l2": residual, "iterations": plan.spec.mesh.nx},
        )


class FakeValidator:
    def validate(self, artifact: PyCFDRunArtifact, plan_ref: str = "") -> PyCFDValidationReport:
        return PyCFDValidationReport(
            task_id=artifact.task_id,
            plan_ref=plan_ref,
            artifact_ref=artifact.artifact_id,
            passed=True,
            residual_l1_passed=True,
            residual_l2_passed=True,
            summary_metrics={"residual_l2": artifact.residual_l2},
        )


class TestPyCFDStudy:
    def test_snapshot_generation_values(self):
        study = PyCFDStudyComponent(DummyCompiler(), DummyExecutor(), DummyValidator())
        spec = PyCFDStudySpec(
            study_id="s1",
            task_template=PyCFDProblemSpec(task_id="t1"),
            axes=[PyCFDStudyAxis(parameter_path="mesh.nx", values=[8, 16, 32])],
        )
        snapshots = study._generate_snapshots(spec)
        assert len(snapshots) == 3
        assert snapshots[0] == {"mesh.nx": 8}
        assert snapshots[2] == {"mesh.nx": 32}

    def test_snapshot_generation_range(self):
        study = PyCFDStudyComponent(DummyCompiler(), DummyExecutor(), DummyValidator())
        spec = PyCFDStudySpec(
            study_id="s1",
            task_template=PyCFDProblemSpec(task_id="t1"),
            axes=[PyCFDStudyAxis(parameter_path="solver.CFL", range=(0.5, 0.7), step=0.1)],
        )
        snapshots = study._generate_snapshots(spec)
        assert len(snapshots) == 3
        values = [s["solver.CFL"] for s in snapshots]
        assert values == [0.5, 0.6, 0.7]

    def test_snapshot_generation_empty_axes(self):
        study = PyCFDStudyComponent(DummyCompiler(), DummyExecutor(), DummyValidator())
        spec = PyCFDStudySpec(
            study_id="s1",
            task_template=PyCFDProblemSpec(task_id="t1"),
            axes=[],
        )
        snapshots = study._generate_snapshots(spec)
        assert snapshots == [{}]

    def test_apply_snapshot(self):
        study = PyCFDStudyComponent(DummyCompiler(), DummyExecutor(), DummyValidator())
        spec = PyCFDProblemSpec(task_id="t1", case_type="vortex")
        mutated = study._apply_snapshot(spec, {"mesh.nx": 99, "flow.M_inf": 0.85})
        assert mutated.mesh.nx == 99
        assert mutated.flow.M_inf == 0.85

    def test_run_study_produces_report(self):
        study = PyCFDStudyComponent(DummyCompiler(), DummyExecutor(), DummyValidator())
        spec = PyCFDStudySpec(
            study_id="s1",
            task_template=PyCFDProblemSpec(task_id="t1"),
            axes=[PyCFDStudyAxis(parameter_path="mesh.nx", values=[8, 16])],
        )
        report = study.run_study(spec)
        assert report.study_id == "s1"
        assert len(report.trials) == 2
        assert report.summary_metrics["total_trials"] == 2

    def test_max_trials_respected(self):
        study = PyCFDStudyComponent(DummyCompiler(), DummyExecutor(), DummyValidator())
        spec = PyCFDStudySpec(
            study_id="s1",
            task_template=PyCFDProblemSpec(task_id="t1"),
            axes=[PyCFDStudyAxis(parameter_path="mesh.nx", values=[8, 16, 32, 64])],
            max_trials=2,
        )
        report = study.run_study(spec)
        assert len(report.trials) == 2

    def test_run_study_uses_compiler_executor_validator_pipeline(self):
        compiler = FakeCompiler()
        study = PyCFDStudyComponent(compiler, FakeExecutor(), FakeValidator())
        spec = PyCFDStudySpec(
            study_id="s1",
            task_template=PyCFDProblemSpec(task_id="t1"),
            axes=[PyCFDStudyAxis(parameter_path="mesh.nx", values=[8, 16])],
            objective="residual_l2",
        )
        report = study.run_study(spec)
        assert [compiled.mesh.nx for compiled in compiler.specs] == [8, 16]
        assert [trial.passed for trial in report.trials] == [True, True]
        assert [trial.plan_ref for trial in report.trials] == ["plan-s1-trial-0", "plan-s1-trial-1"]
        assert report.best_trial_id == "s1-trial-1"
        assert report.recommended_parameters == {"mesh.nx": 16}
        assert report.summary_metrics["passed_trials"] == 2

    def test_run_study_records_pipeline_failure_as_failed_trial(self):
        class FailingExecutor:
            def execute(self, plan: PyCFDRunPlan) -> PyCFDRunArtifact:
                raise RuntimeError(f"boom {plan.run_id}")

        study = PyCFDStudyComponent(FakeCompiler(), FailingExecutor(), FakeValidator())
        spec = PyCFDStudySpec(
            study_id="s1",
            task_template=PyCFDProblemSpec(task_id="t1"),
            axes=[PyCFDStudyAxis(parameter_path="mesh.nx", values=[8])],
        )
        report = study.run_study(spec)
        assert report.trials[0].passed is False
        assert report.trials[0].messages == ["boom s1-trial-0"]
