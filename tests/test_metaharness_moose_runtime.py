from __future__ import annotations

import subprocess
from pathlib import Path

from metaharness.core.execution_modes import ExecutionMode
from metaharness_ext.moose.contracts import (
    MooseEnvironmentReport,
    MooseEvidenceBundle,
    MooseInputSpec,
    MooseOutputSpec,
    MooseProblemSpec,
    MooseRunArtifact,
    MooseWorkspaceSpec,
)
from metaharness_ext.moose.environment import MooseEnvironmentProbeComponent
from metaharness_ext.moose.evidence import build_evidence_bundle, build_instantiation_record
from metaharness_ext.moose.executor import MooseExecutorComponent
from metaharness_ext.moose.input_compiler import MooseInputCompilerComponent
from metaharness_ext.moose.policy import MooseEvidencePolicy
from metaharness_ext.moose.validator import MooseValidatorComponent


def _spec() -> MooseProblemSpec:
    return MooseProblemSpec(
        task_id="runtime-task",
        input=MooseInputSpec(
            mode="inline",
            inline_source="[Mesh]\n  dim = {{dim}}\n[]\n",
            mesh_only=True,
            mesh_output_path="mesh.e",
        ),
        expected_outputs=[MooseOutputSpec(name="mesh", kind="exodus", file_name="mesh.e")],
        parameters={"dim": 1},
    )


def test_moose_environment_probe_uses_mocked_binary(monkeypatch, tmp_path: Path) -> None:
    spec = _spec()
    monkeypatch.setattr(
        "metaharness_ext.moose.environment.shutil.which", lambda _: "/usr/bin/moose-opt"
    )
    monkeypatch.setattr(
        "metaharness_ext.moose.environment.tempfile.gettempdir", lambda: str(tmp_path)
    )

    def fake_run(command, **kwargs):
        if command == ["/usr/bin/moose-opt", "--version"]:
            return subprocess.CompletedProcess(command, 0, stdout="MOOSE 2024.0\n", stderr="")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr("metaharness_ext.moose.environment.subprocess.run", fake_run)

    report = MooseEnvironmentProbeComponent().probe(spec)

    assert report.available is True
    assert report.binary_path == "/usr/bin/moose-opt"
    assert report.version == "MOOSE 2024.0"
    assert report.source_tree_detected is False
    assert report.missing_prerequisites == []


def test_moose_input_compiler_renders_parameters_and_command(tmp_path: Path) -> None:
    spec = _spec()
    compiler = MooseInputCompilerComponent()

    plan = compiler.compile(spec, run_id="moose-run", workspace_dir=str(tmp_path / "run"))

    assert plan.command == ["moose-opt", "-i", "input.i", "--mesh-only", "mesh.e"]
    assert "dim = 1" in plan.input_source
    assert plan.workspace_dir == str(tmp_path / "run")


def test_moose_input_generation_maps_to_core_dry_run(tmp_path: Path) -> None:
    spec = _spec()
    plan = MooseInputCompilerComponent().compile(
        spec, run_id="moose-run", workspace_dir=str(tmp_path / "run")
    )

    record = build_instantiation_record(plan=plan)

    assert record is not None
    assert record.execution_mode is ExecutionMode.DRY_RUN
    assert record.native_execution_mode == "input_deck_generation"
    assert record.run_artifact_ref is None
    assert record.external_evidence_refs == []


def test_moose_executor_and_validator_use_mocked_subprocess(monkeypatch, tmp_path: Path) -> None:
    spec = _spec()
    plan = MooseInputCompilerComponent().compile(
        spec, run_id="moose-run", workspace_dir=str(tmp_path / "run")
    )
    executor = MooseExecutorComponent()
    monkeypatch.setattr(executor, "_resolve_binary", lambda _: "/usr/bin/moose-opt")

    def fake_run_command(command, *, plan, cwd):
        (cwd / "mesh.e").write_text("mesh output")
        return subprocess.CompletedProcess(
            command, 0, stdout="done\n", stderr="warning: mesh note\n"
        )

    monkeypatch.setattr(executor, "_run_command", fake_run_command)

    artifact = executor.execute_plan(plan)
    validation = MooseValidatorComponent().validate_run(artifact, plan)

    assert artifact.status == "completed"
    assert artifact.return_code == 0
    assert artifact.command[0] == "/usr/bin/moose-opt"
    assert Path(artifact.input_files[0]).read_text() == plan.input_source
    assert Path(artifact.output_files[0]).name == "mesh.e"
    assert artifact.warnings[0].severity == "suspicious"
    assert validation.passed is True
    assert validation.status.value == "executed"

    record = build_instantiation_record(plan=plan, artifact=artifact, validation=validation)
    assert record is not None
    assert record.execution_mode is ExecutionMode.INSTANTIATED
    assert record.native_execution_mode == "executable_run"
    assert record.run_artifact_ref == artifact.artifact_id
    assert record.validation_ref == validation.artifact_ref
    assert record.evidence_refs == artifact.evidence_refs
    assert record.external_evidence_refs == []


def test_moose_executor_discovers_custom_output_directory(monkeypatch, tmp_path: Path) -> None:
    spec = _spec().model_copy(update={"workspace": MooseWorkspaceSpec(output_directory="results")})
    plan = MooseInputCompilerComponent().compile(
        spec, run_id="moose-run", workspace_dir=str(tmp_path / "run")
    )
    executor = MooseExecutorComponent()
    monkeypatch.setattr(executor, "_resolve_binary", lambda _: "/usr/bin/moose-opt")

    def fake_run_command(command, *, plan, cwd):
        output_dir = cwd / "results"
        output_dir.mkdir()
        (output_dir / "mesh.e").write_text("mesh output")
        return subprocess.CompletedProcess(command, 0, stdout="done\n", stderr="")

    monkeypatch.setattr(executor, "_run_command", fake_run_command)

    artifact = executor.execute_plan(plan)

    assert Path(artifact.output_files[0]).parent.name == "results"
    assert artifact.summary_metrics["output_count"] == 1


def test_moose_executor_short_circuits_unavailable_environment(tmp_path: Path) -> None:
    plan = MooseInputCompilerComponent().compile(
        _spec(), run_id="moose-run", workspace_dir=str(tmp_path / "run")
    )
    environment = MooseEnvironmentReport(
        task_id=plan.task_id,
        available=False,
        status="prerequisite_missing",
        workspace_writable=True,
        missing_prerequisites=["MOOSE binary not found"],
    )

    artifact = MooseExecutorComponent().execute_plan(plan, environment)

    assert artifact.status == "unavailable"
    assert artifact.terminal_error_type == "environment_unavailable"
    assert artifact.return_code is None
    assert artifact.warnings[0].severity == "blocking"

    record = build_instantiation_record(plan=plan, artifact=artifact)
    assert record is not None
    assert record.execution_mode is ExecutionMode.UNKNOWN
    assert record.native_execution_mode == "execution_unavailable"
    assert record.external_evidence_refs == []


def test_moose_policy_and_evidence_bundle(tmp_path: Path) -> None:
    spec = _spec()
    plan = MooseInputCompilerComponent().compile(
        spec, run_id="moose-run", workspace_dir=str(tmp_path / "run")
    )
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "mesh.e").write_text("mesh output")
    artifact = MooseRunArtifact(
        artifact_id="artifact-1",
        run_id=plan.run_id,
        task_id=plan.task_id,
        plan_ref=plan.plan_id,
        status="completed",
        return_code=0,
        working_directory=str(tmp_path / "run"),
        input_files=[str(tmp_path / "run" / plan.input_filename)],
        output_files=[str(tmp_path / "run" / "mesh.e")],
        log_files=[],
        stdout_path=None,
        stderr_path=None,
        summary_metrics={"output_count": 1},
        evidence_refs=["moose://run/runtime-task/moose-run"],
    )
    validation = MooseValidatorComponent().validate_run(artifact, plan)
    environment = MooseEnvironmentReport(task_id=plan.task_id, available=True, status="available")
    bundle = build_evidence_bundle(
        task_id=spec.task_id,
        environment=environment,
        plan=plan,
        artifact=artifact,
        validation=validation,
    )
    policy = MooseEvidencePolicy().evaluate(bundle)

    assert isinstance(bundle, MooseEvidenceBundle)
    assert bundle.run_id == artifact.run_id
    assert bundle.plan_ref == plan.plan_id
    assert bundle.validation_ref == artifact.artifact_id
    assert len(bundle.instantiation_records) == 1
    assert bundle.instantiation_records[0].execution_mode is ExecutionMode.INSTANTIATED
    assert policy.decision == "allow"
