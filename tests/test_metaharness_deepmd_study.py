from __future__ import annotations

import json
from pathlib import Path

import pytest

from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.deepmd.contracts import (
    DeepMDDatasetSpec,
    DeepMDDescriptorSpec,
    DeepMDExecutableSpec,
    DeepMDFittingNetSpec,
    DeepMDMutationAxis,
    DeepMDRunArtifact,
    DeepMDStudySpec,
    DeepMDTrainSpec,
    DeepMDValidationReport,
    DPGenMachineSpec,
    DPGenRunSpec,
)
from metaharness_ext.deepmd.study import DeepMDStudyComponent
from metaharness_ext.deepmd.train_config_compiler import DeepMDTrainConfigCompilerComponent


class _FakeExecutor:
    def __init__(self, metric_key: str, values: dict[int | float, float]) -> None:
        self.metric_key = metric_key
        self.values = values
        self.calls: list[int | float] = []

    def execute_plan(self, plan):
        axis_value = plan.input_json.get("training", {}).get("numb_steps")
        if axis_value is None:
            axis_value = plan.param_json.get("model_devi_f_trust_lo")
        self.calls.append(axis_value)
        metric = self.values[axis_value]
        return DeepMDRunArtifact(
            task_id=plan.task_id,
            run_id=plan.run_id,
            application_family=plan.application_family,
            execution_mode=plan.execution_mode,
            command=plan.command,
            return_code=0,
            stdout_path="/tmp/stdout.log",
            stderr_path="/tmp/stderr.log",
            working_directory="/tmp/run",
            status="completed",
            result_summary={"exit_code": 0, self.metric_key: metric},
        )


class _FakeValidator:
    def __init__(self, metric_key: str, values: dict[int | float, float]) -> None:
        self.metric_key = metric_key
        self.values = values

    def validate_run(self, artifact: DeepMDRunArtifact) -> DeepMDValidationReport:
        metric = artifact.result_summary[self.metric_key]
        return DeepMDValidationReport(
            task_id=artifact.task_id,
            run_id=artifact.run_id,
            passed=True,
            status="tested",
            summary_metrics={self.metric_key: float(metric)},
            evidence_files=[],
        )


class _FakeCompletedProcess:
    def __init__(self, *, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _build_train_spec() -> DeepMDTrainSpec:
    return DeepMDTrainSpec(
        task_id="deepmd-study-task",
        executable=DeepMDExecutableSpec(execution_mode="train"),
        dataset=DeepMDDatasetSpec(
            dataset_id="deepmd-study-task",
            train_systems=["/tmp/train-system"],
            validation_systems=[],
            type_map=["H", "O"],
            labels_present=["energy", "force"],
        ),
        type_map=["H", "O"],
        descriptor=DeepMDDescriptorSpec(
            descriptor_type="se_e2_a",
            rcut=6.0,
            rcut_smth=5.5,
            sel=[32],
            neuron=[25, 50, 100],
        ),
        fitting_net=DeepMDFittingNetSpec(neuron=[240, 240, 240]),
        training={"numb_steps": 1000, "save_freq": 100, "disp_freq": 100},
        learning_rate={"type": "exp", "start_lr": 0.001, "decay_steps": 1000},
        loss={"type": "ener", "start_pref_e": 0.02, "start_pref_f": 1000.0},
    )


def _build_dpgen_spec() -> DPGenRunSpec:
    return DPGenRunSpec(
        task_id="dpgen-study-task",
        executable=DeepMDExecutableSpec(binary_name="dpgen", execution_mode="dpgen_run"),
        param={"model_devi_f_trust_lo": 0.1, "model_devi_f_trust_hi": 0.3},
        machine=DPGenMachineSpec(),
    )


@pytest.mark.asyncio
async def test_study_minimizes_train_metric(tmp_path: Path) -> None:
    component = DeepMDStudyComponent()
    await component.activate(ComponentRuntime(storage_path=tmp_path))
    compiler = DeepMDTrainConfigCompilerComponent()
    executor = _FakeExecutor("rmse_e_trn", {500: 0.8, 1000: 0.4, 1500: 0.2})
    validator = _FakeValidator("rmse_e_trn", {500: 0.8, 1000: 0.4, 1500: 0.2})

    spec = DeepMDStudySpec(
        study_id="study-1",
        task_id="deepmd-study-task",
        base_task=_build_train_spec(),
        axis=DeepMDMutationAxis(kind="numb_steps", values=[500, 1000, 1500]),
        metric_key="rmse_e_trn",
        goal="minimize",
    )

    report = component.run_study(spec, compiler=compiler, executor=executor, validator=validator)

    assert executor.calls == [500, 1000, 1500]
    assert [trial.axis_value for trial in report.trials] == [500, 1000, 1500]
    assert report.recommended_value == 1500
    assert report.summary_metrics["best_rmse_e_trn"] == pytest.approx(0.2)


@pytest.mark.asyncio
async def test_study_maximizes_dpgen_metric(tmp_path: Path) -> None:
    component = DeepMDStudyComponent()
    await component.activate(ComponentRuntime(storage_path=tmp_path))
    compiler = DeepMDTrainConfigCompilerComponent()
    executor = _FakeExecutor("candidate_count", {0.1: 2.0, 0.2: 5.0, 0.3: 4.0})
    validator = _FakeValidator("candidate_count", {0.1: 2.0, 0.2: 5.0, 0.3: 4.0})

    spec = DeepMDStudySpec(
        study_id="study-2",
        task_id="dpgen-study-task",
        base_task=_build_dpgen_spec(),
        axis=DeepMDMutationAxis(kind="model_devi_f_trust_lo", values=[0.1, 0.2, 0.3]),
        metric_key="candidate_count",
        goal="maximize",
    )

    report = component.run_study(spec, compiler=compiler, executor=executor, validator=validator)

    assert report.recommended_value == pytest.approx(0.2)
    assert report.summary_metrics["best_candidate_count"] == pytest.approx(5.0)


def test_study_axis_requires_values() -> None:
    with pytest.raises(ValueError, match="axis.values"):
        DeepMDMutationAxis(kind="numb_steps", values=[])


@pytest.mark.asyncio
async def test_study_rejects_unsupported_train_axis(tmp_path: Path) -> None:
    component = DeepMDStudyComponent()
    await component.activate(ComponentRuntime(storage_path=tmp_path))

    spec = DeepMDStudySpec(
        study_id="study-bad-train",
        task_id="deepmd-study-task",
        base_task=_build_train_spec(),
        axis=DeepMDMutationAxis(kind="model_devi_f_trust_lo", values=[0.1]),
        metric_key="rmse_e_trn",
    )

    with pytest.raises(NotImplementedError, match="not supported"):
        component.run_study(
            spec,
            compiler=DeepMDTrainConfigCompilerComponent(),
            executor=_FakeExecutor("rmse_e_trn", {0.1: 0.5}),
            validator=_FakeValidator("rmse_e_trn", {0.1: 0.5}),
        )


@pytest.mark.asyncio
async def test_study_rejects_unsupported_dpgen_axis(tmp_path: Path) -> None:
    component = DeepMDStudyComponent()
    await component.activate(ComponentRuntime(storage_path=tmp_path))

    spec = DeepMDStudySpec(
        study_id="study-bad-dpgen",
        task_id="dpgen-study-task",
        base_task=_build_dpgen_spec(),
        axis=DeepMDMutationAxis(kind="numb_steps", values=[1000]),
        metric_key="candidate_count",
    )

    with pytest.raises(NotImplementedError, match="not supported"):
        component.run_study(
            spec,
            compiler=DeepMDTrainConfigCompilerComponent(),
            executor=_FakeExecutor("candidate_count", {1000: 1.0}),
            validator=_FakeValidator("candidate_count", {1000: 1.0}),
        )


@pytest.mark.asyncio
async def test_study_rcut_runs_real_train_chain(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    component = DeepMDStudyComponent()
    await component.activate(ComponentRuntime(storage_path=tmp_path))
    compiler = DeepMDTrainConfigCompilerComponent()
    from metaharness_ext.deepmd.executor import DeepMDExecutorComponent
    from metaharness_ext.deepmd.validator import DeepMDValidatorComponent

    real_executor = DeepMDExecutorComponent()
    real_validator = DeepMDValidatorComponent()
    await real_executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr(
        "metaharness_ext.deepmd.executor.shutil.which", lambda binary: f"/usr/bin/{binary}"
    )

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        input_json = json.loads((cwd / "input.json").read_text())
        rcut = input_json["model"]["descriptor"]["rcut"]
        rmse = 0.02 if rcut == 7.0 else 0.05
        (cwd / "lcurve.out").write_text(f"# step rmse_e rmse_f\n100 {rmse} 2.50e-02\n")
        (cwd / "checkpoint").write_text("checkpoint-marker")
        return _FakeCompletedProcess(returncode=0, stdout="training ok", stderr="")

    monkeypatch.setattr("metaharness_ext.deepmd.executor.subprocess.run", fake_run)

    spec = DeepMDStudySpec(
        study_id="study-rcut",
        task_id="deepmd-study-task",
        base_task=_build_train_spec(),
        axis=DeepMDMutationAxis(kind="rcut", values=[6.0, 7.0]),
        metric_key="rmse_e_trn",
        goal="minimize",
    )

    report = component.run_study(
        spec,
        compiler=compiler,
        executor=real_executor,
        validator=real_validator,
    )

    assert [trial.axis_value for trial in report.trials] == [6.0, 7.0]
    assert report.recommended_value == pytest.approx(7.0)
    assert report.summary_metrics["best_rmse_e_trn"] == pytest.approx(0.02)
    assert all(trial.validation.status == "trained" for trial in report.trials)


@pytest.mark.asyncio
async def test_study_sel_runs_real_train_chain(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    component = DeepMDStudyComponent()
    await component.activate(ComponentRuntime(storage_path=tmp_path))
    compiler = DeepMDTrainConfigCompilerComponent()
    from metaharness_ext.deepmd.executor import DeepMDExecutorComponent
    from metaharness_ext.deepmd.validator import DeepMDValidatorComponent

    real_executor = DeepMDExecutorComponent()
    real_validator = DeepMDValidatorComponent()
    await real_executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr(
        "metaharness_ext.deepmd.executor.shutil.which", lambda binary: f"/usr/bin/{binary}"
    )

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        input_json = json.loads((cwd / "input.json").read_text())
        sel = input_json["model"]["descriptor"]["sel"][0]
        rmse = 0.03 if sel == 48 else 0.08
        (cwd / "lcurve.out").write_text(f"# step rmse_e rmse_f\n100 {rmse} 2.50e-02\n")
        (cwd / "checkpoint").write_text("checkpoint-marker")
        return _FakeCompletedProcess(returncode=0, stdout="training ok", stderr="")

    monkeypatch.setattr("metaharness_ext.deepmd.executor.subprocess.run", fake_run)

    spec = DeepMDStudySpec(
        study_id="study-sel",
        task_id="deepmd-study-task",
        base_task=_build_train_spec(),
        axis=DeepMDMutationAxis(kind="sel", values=[32, 48]),
        metric_key="rmse_e_trn",
        goal="minimize",
    )

    report = component.run_study(
        spec,
        compiler=compiler,
        executor=real_executor,
        validator=real_validator,
    )

    assert [trial.axis_value for trial in report.trials] == [32, 48]
    assert report.recommended_value == 48
    assert report.summary_metrics["best_rmse_e_trn"] == pytest.approx(0.03)
    assert all(trial.validation.status == "trained" for trial in report.trials)


@pytest.mark.asyncio
async def test_study_model_devi_trust_lo_runs_real_dpgen_chain(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    component = DeepMDStudyComponent()
    await component.activate(ComponentRuntime(storage_path=tmp_path))
    compiler = DeepMDTrainConfigCompilerComponent()
    from metaharness_ext.deepmd.executor import DeepMDExecutorComponent
    from metaharness_ext.deepmd.validator import DeepMDValidatorComponent

    real_executor = DeepMDExecutorComponent()
    real_validator = DeepMDValidatorComponent()
    await real_executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr(
        "metaharness_ext.deepmd.executor.shutil.which", lambda binary: f"/usr/bin/{binary}"
    )

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        param_json = json.loads((cwd / "param.json").read_text())
        trust_lo = param_json["model_devi_f_trust_lo"]
        candidate_count = 5 if trust_lo == 0.2 else 2
        accurate_count = 2 if trust_lo == 0.2 else 1
        failed_count = 0
        (cwd / "record.dpgen").write_text(
            f"candidate_count={candidate_count}\naccurate_count={accurate_count}\nfailed_count={failed_count}\n"
        )
        iter_dir = cwd / "iter.000000"
        (iter_dir / "00.train").mkdir(parents=True)
        (iter_dir / "01.model_devi").mkdir(parents=True)
        (iter_dir / "02.fp").mkdir(parents=True)
        return _FakeCompletedProcess(returncode=0, stdout="dpgen run ok", stderr="")

    monkeypatch.setattr("metaharness_ext.deepmd.executor.subprocess.run", fake_run)

    spec = DeepMDStudySpec(
        study_id="study-trust-lo",
        task_id="dpgen-study-task",
        base_task=_build_dpgen_spec(),
        axis=DeepMDMutationAxis(kind="model_devi_f_trust_lo", values=[0.1, 0.2]),
        metric_key="candidate_count",
        goal="maximize",
    )

    report = component.run_study(
        spec,
        compiler=compiler,
        executor=real_executor,
        validator=real_validator,
    )

    assert [trial.axis_value for trial in report.trials] == [0.1, 0.2]
    assert report.recommended_value == pytest.approx(0.2)
    assert report.summary_metrics["best_candidate_count"] == pytest.approx(5.0)
    assert all(trial.validation.status == "baseline_success" for trial in report.trials)


@pytest.mark.asyncio
async def test_study_model_devi_trust_hi_runs_real_dpgen_chain(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    component = DeepMDStudyComponent()
    await component.activate(ComponentRuntime(storage_path=tmp_path))
    compiler = DeepMDTrainConfigCompilerComponent()
    from metaharness_ext.deepmd.executor import DeepMDExecutorComponent
    from metaharness_ext.deepmd.validator import DeepMDValidatorComponent

    real_executor = DeepMDExecutorComponent()
    real_validator = DeepMDValidatorComponent()
    await real_executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr(
        "metaharness_ext.deepmd.executor.shutil.which", lambda binary: f"/usr/bin/{binary}"
    )

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        param_json = json.loads((cwd / "param.json").read_text())
        trust_hi = param_json["model_devi_f_trust_hi"]
        candidate_count = 6 if trust_hi == 0.4 else 3
        accurate_count = 2
        failed_count = 0
        (cwd / "record.dpgen").write_text(
            f"candidate_count={candidate_count}\naccurate_count={accurate_count}\nfailed_count={failed_count}\n"
        )
        iter_dir = cwd / "iter.000000"
        (iter_dir / "00.train").mkdir(parents=True)
        (iter_dir / "01.model_devi").mkdir(parents=True)
        (iter_dir / "02.fp").mkdir(parents=True)
        return _FakeCompletedProcess(returncode=0, stdout="dpgen run ok", stderr="")

    monkeypatch.setattr("metaharness_ext.deepmd.executor.subprocess.run", fake_run)

    spec = DeepMDStudySpec(
        study_id="study-trust-hi",
        task_id="dpgen-study-task",
        base_task=_build_dpgen_spec(),
        axis=DeepMDMutationAxis(kind="model_devi_f_trust_hi", values=[0.3, 0.4]),
        metric_key="candidate_count",
        goal="maximize",
    )

    report = component.run_study(
        spec,
        compiler=compiler,
        executor=real_executor,
        validator=real_validator,
    )

    assert [trial.axis_value for trial in report.trials] == [0.3, 0.4]
    assert report.recommended_value == pytest.approx(0.4)
    assert report.summary_metrics["best_candidate_count"] == pytest.approx(6.0)
    assert all(trial.validation.status == "baseline_success" for trial in report.trials)
