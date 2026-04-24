from pathlib import Path

from metaharness_ext.abacus.contracts import (
    AbacusExecutableSpec,
    AbacusRunPlan,
)
from metaharness_ext.abacus.executor import AbacusExecutorComponent


def test_abacus_executor_resolves_binary_and_builds_command() -> None:
    executor = AbacusExecutorComponent()
    plan = AbacusRunPlan(
        task_id="task-1",
        run_id="run-1",
        application_family="scf",
        command=[],
        working_directory=str(Path("/tmp/abacus_test")),
        input_content="INPUT_PARAMETERS\nsuffix ABACUS\n",
        structure_content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n",
        suffix="ABACUS",
        executable=AbacusExecutableSpec(binary_name="echo", launcher="direct"),
    )

    artifact = executor.execute_plan(plan)

    assert artifact.task_id == "task-1"
    assert artifact.run_id == "run-1"
    assert artifact.application_family == "scf"
    assert artifact.return_code == 0
    assert artifact.status == "completed"
    assert artifact.prepared_inputs
    assert any("INPUT" in p for p in artifact.prepared_inputs)
    assert any("STRU" in p for p in artifact.prepared_inputs)
    assert f"abacus://run/{artifact.task_id}/{artifact.run_id}" in artifact.evidence_refs
    assert "abacus://input/INPUT" in artifact.evidence_refs
    assert "abacus://input/STRU" in artifact.evidence_refs


def test_abacus_executor_reports_missing_binary() -> None:
    executor = AbacusExecutorComponent()
    plan = AbacusRunPlan(
        task_id="task-1",
        run_id="run-1",
        application_family="scf",
        command=[],
        working_directory=str(Path("/tmp/abacus_test")),
        input_content="INPUT_PARAMETERS\nsuffix ABACUS\n",
        structure_content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n",
        suffix="ABACUS",
        executable=AbacusExecutableSpec(binary_name="nonexistent_abacus_binary", launcher="direct"),
    )

    artifact = executor.execute_plan(plan)

    assert artifact.status == "unavailable"
    assert artifact.return_code is None
    assert artifact.result_summary.get("fallback_reason") == "binary_not_found"
    assert f"abacus://run/{artifact.task_id}/{artifact.run_id}" in artifact.evidence_refs
    assert "abacus://input/INPUT" in artifact.evidence_refs


def test_abacus_executor_reports_missing_launcher(monkeypatch) -> None:
    def fake_which(name: str) -> str | None:
        if name == "echo":
            return "/usr/bin/echo"
        return None

    monkeypatch.setattr("metaharness_ext.abacus.executor.shutil.which", fake_which)

    executor = AbacusExecutorComponent()
    plan = AbacusRunPlan(
        task_id="task-1",
        run_id="run-1",
        application_family="scf",
        command=[],
        working_directory=str(Path("/tmp/abacus_test")),
        input_content="INPUT_PARAMETERS\nsuffix ABACUS\n",
        structure_content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n",
        suffix="ABACUS",
        executable=AbacusExecutableSpec(binary_name="echo", launcher="mpirun"),
    )

    artifact = executor.execute_plan(plan)

    assert artifact.status == "unavailable"
    assert artifact.return_code is None
    assert artifact.result_summary.get("fallback_reason") == "launcher_not_found"
    assert f"abacus://run/{artifact.task_id}/{artifact.run_id}" in artifact.evidence_refs


def test_abacus_executor_writes_kpt_when_present() -> None:
    executor = AbacusExecutorComponent()
    plan = AbacusRunPlan(
        task_id="task-1",
        run_id="run-1",
        application_family="scf",
        command=[],
        working_directory=str(Path("/tmp/abacus_test")),
        input_content="INPUT_PARAMETERS\nsuffix ABACUS\n",
        structure_content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n",
        kpoints_content="K_POINTS\n1\n0.0 0.0 0.0 1.0\n",
        suffix="ABACUS",
        executable=AbacusExecutableSpec(binary_name="echo", launcher="direct"),
    )

    artifact = executor.execute_plan(plan)

    assert artifact.status == "completed"
    assert any("KPT" in p for p in artifact.prepared_inputs)


def test_abacus_executor_artifact_includes_stdout_stderr_paths() -> None:
    executor = AbacusExecutorComponent()
    plan = AbacusRunPlan(
        task_id="task-1",
        run_id="run-1",
        application_family="scf",
        command=[],
        working_directory=str(Path("/tmp/abacus_test")),
        input_content="INPUT_PARAMETERS\nsuffix ABACUS\n",
        structure_content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n",
        suffix="ABACUS",
        executable=AbacusExecutableSpec(binary_name="echo", launcher="direct"),
    )

    artifact = executor.execute_plan(plan)

    assert artifact.stdout_path is not None
    assert artifact.stderr_path is not None
    assert Path(artifact.stdout_path).exists()
    assert Path(artifact.stderr_path).exists()


def test_abacus_executor_discovers_diagnostics_and_structures(tmp_path: Path, monkeypatch) -> None:
    executor = AbacusExecutorComponent()
    plan = AbacusRunPlan(
        task_id="task-md",
        run_id="run-md",
        application_family="md",
        command=[],
        working_directory=str(tmp_path / "abacus_test"),
        input_content="INPUT_PARAMETERS\nsuffix ABACUS\ncalculation md\n",
        structure_content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n",
        suffix="ABACUS",
        expected_logs=["running_md.log"],
        executable=AbacusExecutableSpec(binary_name="echo", launcher="direct"),
    )

    def fake_run(command, *, cwd, capture_output, text, check, timeout):
        out_dir = cwd / "OUT.ABACUS"
        out_dir.mkdir(parents=True, exist_ok=True)
        (cwd / "running_md.log").write_text("log")
        (out_dir / "MD_dump").write_text("dump")
        (out_dir / "STRU_MD_0").write_text("structure")
        return type("_CompletedProcess", (), {"returncode": 0, "stdout": "ok", "stderr": ""})()

    monkeypatch.setattr("metaharness_ext.abacus.executor.subprocess.run", fake_run)

    artifact = executor.execute_plan(plan)

    assert any(Path(path).name == "running_md.log" for path in artifact.diagnostic_files)
    assert any(Path(path).name == "MD_dump" for path in artifact.output_files)
    assert any(Path(path).name.startswith("STRU_MD") for path in artifact.structure_files)
