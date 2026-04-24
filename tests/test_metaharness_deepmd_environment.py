from pathlib import Path

import pytest

from metaharness_ext.deepmd.contracts import (
    DeepMDDatasetSpec,
    DeepMDDescriptorSpec,
    DeepMDExecutableSpec,
    DeepMDFittingNetSpec,
    DeepMDTrainSpec,
    DPGenAutotestSpec,
    DPGenMachineSpec,
    DPGenRunSpec,
)
from metaharness_ext.deepmd.environment import DeepMDEnvironmentProbeComponent


def _build_train_spec(dataset_dir: Path) -> DeepMDTrainSpec:
    return DeepMDTrainSpec(
        task_id="deepmd-train",
        executable=DeepMDExecutableSpec(binary_name="dp", execution_mode="train"),
        dataset=DeepMDDatasetSpec(
            dataset_id="dataset-1",
            train_systems=[str(dataset_dir)],
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
        training={"numb_steps": 1000},
        learning_rate={"type": "exp", "start_lr": 0.001, "decay_steps": 1000},
        loss={"type": "ener", "start_pref_e": 0.02, "start_pref_f": 1000.0},
    )


def test_deepmd_environment_reports_missing_train_binary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dataset_dir = tmp_path / "train-system"
    dataset_dir.mkdir()
    spec = _build_train_spec(dataset_dir)
    probe = DeepMDEnvironmentProbeComponent()
    monkeypatch.setattr("metaharness_ext.deepmd.environment.shutil.which", lambda name: None)

    report = probe.probe(spec)

    assert report.application_family == "deepmd_train"
    assert report.execution_mode == "train"
    assert report.dp_available is False
    assert report.dp_probe_supported is False
    assert report.required_paths_present is True
    assert report.workspace_ready is True
    assert any("DeepMD binary not found" in message for message in report.messages)


def test_deepmd_environment_checks_missing_dataset_paths(tmp_path: Path) -> None:
    missing_dir = tmp_path / "missing-system"
    spec = _build_train_spec(missing_dir)
    probe = DeepMDEnvironmentProbeComponent()

    report = probe.probe(spec)

    assert report.required_paths_present is False
    assert str(missing_dir) in report.missing_required_paths
    assert any(str(missing_dir) in message for message in report.messages)


def test_deepmd_environment_checks_dpgen_workspace_and_machine_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace_dir = tmp_path / "workspace-inputs"
    workspace_dir.mkdir()
    spec = DPGenRunSpec(
        task_id="dpgen-run",
        executable=DeepMDExecutableSpec(binary_name="dpgen", execution_mode="dpgen_run"),
        param={"type_map": ["H", "O"], "numb_models": 4},
        machine=DPGenMachineSpec(local_root=str(tmp_path / "missing-root"), python_path="python3"),
        workspace_files=[str(workspace_dir)],
    )
    probe = DeepMDEnvironmentProbeComponent()
    monkeypatch.setattr(
        "metaharness_ext.deepmd.environment.shutil.which",
        lambda name: "/usr/bin/python3" if name == "python3" else None,
    )

    report = probe.probe(spec)

    assert report.application_family == "dpgen_run"
    assert report.dp_available is False
    assert report.dpgen_available is False
    assert report.python_available is True
    assert report.required_paths_present is True
    assert report.machine_root_ready is False
    assert report.workspace_ready is False
    assert "machine.local_root" in report.environment_prerequisites
    assert "machine.local_root" in report.missing_prerequisites
    assert any("Machine local root is not a directory" in message for message in report.messages)
    assert any("DP-GEN binary not found" in message for message in report.messages)


def test_deepmd_environment_checks_remote_and_scheduler_prerequisites(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace_dir = tmp_path / "workspace-inputs"
    workspace_dir.mkdir()
    spec = DPGenRunSpec(
        task_id="dpgen-run",
        executable=DeepMDExecutableSpec(binary_name="dpgen", execution_mode="dpgen_run"),
        param={"type_map": ["H", "O"], "numb_models": 4},
        machine=DPGenMachineSpec(
            batch_type="slurm", context_type="ssh", local_root=str(tmp_path), python_path="python3"
        ),
        workspace_files=[str(workspace_dir)],
    )
    probe = DeepMDEnvironmentProbeComponent()
    monkeypatch.setattr(
        "metaharness_ext.deepmd.environment.shutil.which",
        lambda name: f"/usr/bin/{name}" if name in {"dpgen", "python3"} else None,
    )

    report = probe.probe(spec)

    assert report.machine_spec_valid is False
    assert report.remote_root_configured is False
    assert report.scheduler_command_configured is False
    assert "machine.remote_root" in report.missing_prerequisites
    assert "machine.command" in report.missing_prerequisites
    assert report.fallback_reason == "missing_remote_root"


def test_deepmd_environment_checks_missing_dpgen_workspace_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    missing_workspace = tmp_path / "missing-workspace"
    spec = DPGenAutotestSpec(
        task_id="dpgen-autotest",
        executable=DeepMDExecutableSpec(binary_name="dpgen", execution_mode="dpgen_autotest"),
        param={"type_map": ["H", "O"], "properties": {"elastic": {}}},
        machine=DPGenMachineSpec(local_root=str(tmp_path), python_path="python3"),
        workspace_files=[str(missing_workspace)],
    )
    probe = DeepMDEnvironmentProbeComponent()
    monkeypatch.setattr(
        "metaharness_ext.deepmd.environment.shutil.which",
        lambda name: "/usr/bin/python3" if name == "python3" else None,
    )

    report = probe.probe(spec)

    assert report.application_family == "dpgen_autotest"
    assert report.required_paths_present is False
    assert report.workspace_ready is False
    assert str(missing_workspace) in report.missing_required_paths
    assert any(str(missing_workspace) in message for message in report.messages)


def test_dpgen_machine_spec_rejects_remote_root_for_local_context() -> None:
    with pytest.raises(ValueError, match="remote_root"):
        DPGenMachineSpec(context_type="local", remote_root="/remote")


def test_dpgen_machine_spec_allows_remote_root_to_be_checked_by_environment() -> None:
    machine = DPGenMachineSpec(context_type="ssh", batch_type="shell")

    assert machine.remote_root is None


def test_dpgen_machine_spec_allows_scheduler_command_to_be_checked_by_environment() -> None:
    machine = DPGenMachineSpec(context_type="ssh", batch_type="slurm", remote_root="/remote")

    assert machine.command is None


def test_dpgen_machine_spec_rejects_command_for_shell_batch_type() -> None:
    with pytest.raises(ValueError, match="command is only allowed"):
        DPGenMachineSpec(batch_type="shell", context_type="local", command="bash")


def test_deepmd_environment_reports_probe_output_when_binary_available(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dataset_dir = tmp_path / "train-system"
    dataset_dir.mkdir()
    spec = _build_train_spec(dataset_dir)
    probe = DeepMDEnvironmentProbeComponent()

    monkeypatch.setattr(
        "metaharness_ext.deepmd.environment.shutil.which",
        lambda name: f"/usr/bin/{name}" if name in {"dp", "python", "python3"} else None,
    )

    def fake_run(command, *, text, capture_output, check, timeout):
        return type("_FakeCompletedProcess", (), {"returncode": 0, "stdout": "deepmd help", "stderr": ""})()

    monkeypatch.setattr("metaharness_ext.deepmd.environment.subprocess.run", fake_run)

    report = probe.probe(spec)

    assert report.dp_probe_supported is True
    assert report.dp_probe_succeeded is True
    assert report.dp_probe_output == "deepmd help"
    assert any(ref.startswith("deepmd://binary/") for ref in report.evidence_refs)


def test_deepmd_environment_sets_machine_fallback_reason(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace_dir = tmp_path / "workspace-inputs"
    workspace_dir.mkdir()
    spec = DPGenAutotestSpec(
        task_id="dpgen-autotest",
        executable=DeepMDExecutableSpec(binary_name="dpgen", execution_mode="dpgen_autotest"),
        param={"type": "eos"},
        machine=DPGenMachineSpec(
            batch_type="slurm",
            context_type="ssh",
            local_root=str(tmp_path),
            remote_root="/remote/work",
            python_path="missing-python",
            command="sbatch",
        ),
        workspace_files=[str(workspace_dir)],
    )
    probe = DeepMDEnvironmentProbeComponent()
    monkeypatch.setattr(
        "metaharness_ext.deepmd.environment.shutil.which",
        lambda name: "/usr/bin/dpgen" if name == "dpgen" else None,
    )

    report = probe.probe(spec)

    assert report.python_available is False
    assert report.machine_spec_valid is False
    assert report.fallback_reason == "missing_python_runtime"
    assert "machine.python_path" in report.missing_prerequisites


def test_dpgen_machine_spec_normalizes_blank_optional_fields() -> None:
    machine = DPGenMachineSpec(batch_type="slurm", context_type="ssh", local_root=".", remote_root="/remote", command="sbatch")

    assert machine.command == "sbatch"
