from __future__ import annotations

from metaharness_ext.pycfd.contracts import (
    PyCFDProblemSpec,
    PyCFDStudyAxis,
    PyCFDStudySpec,
)
from metaharness_ext.pycfd.study import PyCFDStudyComponent


class DummyCompiler:
    pass


class DummyExecutor:
    pass


class DummyValidator:
    pass


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
