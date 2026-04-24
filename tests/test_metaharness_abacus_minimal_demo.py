from pathlib import Path

from metaharness_ext.abacus.contracts import (
    AbacusExecutableSpec,
    AbacusKPointSpec,
    AbacusMdSpec,
    AbacusNscfSpec,
    AbacusRelaxSpec,
    AbacusRunArtifact,
    AbacusScfSpec,
    AbacusStructureSpec,
)
from metaharness_ext.abacus.environment import AbacusEnvironmentProbeComponent
from metaharness_ext.abacus.executor import AbacusExecutorComponent
from metaharness_ext.abacus.input_compiler import AbacusInputCompilerComponent
from metaharness_ext.abacus.validator import AbacusValidatorComponent


def test_abacus_minimal_scf_chain_with_missing_binary() -> None:
    spec = AbacusScfSpec(
        task_id="demo-task-1",
        executable=AbacusExecutableSpec(binary_name="nonexistent_abacus"),
        structure=AbacusStructureSpec(content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n"),
    )

    probe = AbacusEnvironmentProbeComponent()
    env_report = probe.probe(spec)
    assert env_report.abacus_available is False
    assert any("not found" in m for m in env_report.messages)

    compiler = AbacusInputCompilerComponent()
    plan = compiler.compile(spec)
    assert plan.input_content
    assert "scf" in plan.input_content
    assert plan.structure_content

    executor = AbacusExecutorComponent()
    artifact = executor.execute_plan(plan)
    assert artifact.status == "unavailable"
    assert artifact.result_summary.get("fallback_reason") == "binary_not_found"

    validator = AbacusValidatorComponent()
    report = validator.validate_run(artifact)
    assert report.passed is False
    assert report.status == "environment_invalid"
    assert report.blocks_promotion is True
    assert report.governance_state == "blocked"
    assert report.scored_evidence is not None


def test_abacus_minimal_scf_chain_with_real_echo_binary() -> None:
    spec = AbacusScfSpec(
        task_id="demo-task-2",
        executable=AbacusExecutableSpec(binary_name="echo"),
        structure=AbacusStructureSpec(content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n"),
        kpoints=None,
        basis_type="pw",
        esolver_type="ksdft",
    )

    probe = AbacusEnvironmentProbeComponent()
    env_report = probe.probe(spec)
    assert env_report.abacus_available is True

    compiler = AbacusInputCompilerComponent()
    plan = compiler.compile(spec)
    assert plan.application_family == "scf"

    executor = AbacusExecutorComponent()
    artifact = executor.execute_plan(plan)
    assert artifact.status == "completed"
    assert artifact.return_code == 0

    validator = AbacusValidatorComponent()
    report = validator.validate_run(artifact)
    assert report.passed is False
    assert report.status == "validation_failed"
    assert any("OUT." in m for m in report.missing_evidence)


def test_abacus_validator_rejects_zero_return_code_without_evidence() -> None:
    artifact = AbacusRunArtifact(
        task_id="task-1",
        run_id="run-1",
        application_family="scf",
        return_code=0,
        status="completed",
        working_directory="/tmp",
        prepared_inputs=[],
        output_files=[],
        diagnostic_files=[],
    )

    validator = AbacusValidatorComponent()
    report = validator.validate_run(artifact)

    assert report.passed is False
    assert report.status == "validation_failed"
    assert any("OUT." in m for m in report.messages)


def test_abacus_validator_accepts_sufficient_evidence() -> None:
    artifact = AbacusRunArtifact(
        task_id="task-1",
        run_id="run-1",
        application_family="scf",
        return_code=0,
        status="completed",
        working_directory="/tmp",
        prepared_inputs=["INPUT", "STRU"],
        output_files=["OUT.ABACUS/"],
        diagnostic_files=["OUT.ABACUS/running_scf.log"],
    )

    validator = AbacusValidatorComponent()
    report = validator.validate_run(artifact)

    assert report.passed is True
    assert report.status == "executed"


def test_abacus_validator_rejects_nonzero_return_code() -> None:
    artifact = AbacusRunArtifact(
        task_id="task-1",
        run_id="run-1",
        application_family="scf",
        return_code=1,
        status="failed",
        working_directory="/tmp",
        prepared_inputs=[],
        output_files=[],
        diagnostic_files=[],
    )

    validator = AbacusValidatorComponent()
    report = validator.validate_run(artifact)

    assert report.passed is False
    assert report.status == "runtime_failed"


def test_abacus_minimal_nscf_chain_with_real_echo_binary(tmp_path: Path) -> None:
    charge_density = tmp_path / "charge-density.cube"
    charge_density.write_text("density")
    spec = AbacusNscfSpec(
        task_id="demo-nscf-1",
        executable=AbacusExecutableSpec(binary_name="echo"),
        structure=AbacusStructureSpec(content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n"),
        kpoints=AbacusKPointSpec(content="K_POINTS\n1\n0.0 0.0 0.0 1\n"),
        charge_density_path=str(charge_density),
        working_directory=str(tmp_path / "nscf-run"),
    )

    probe = AbacusEnvironmentProbeComponent()
    env_report = probe.probe(spec)
    assert env_report.abacus_available is True

    compiler = AbacusInputCompilerComponent()
    plan = compiler.compile(spec)
    assert plan.application_family == "nscf"

    executor = AbacusExecutorComponent()
    artifact = executor.execute_plan(plan)
    assert artifact.status == "completed"
    assert artifact.return_code == 0

    validator = AbacusValidatorComponent()
    report = validator.validate_run(artifact)
    assert report.passed is False
    assert report.status == "validation_failed"
    assert any("NSCF log evidence" in item for item in report.missing_evidence)


def test_abacus_minimal_relax_chain_with_stubbed_structure_evidence(
    tmp_path: Path, monkeypatch
) -> None:
    spec = AbacusRelaxSpec(
        task_id="demo-relax-1",
        executable=AbacusExecutableSpec(binary_name="echo"),
        structure=AbacusStructureSpec(content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n"),
        relax_controls={"relax_nmax": 3},
        working_directory=str(tmp_path / "relax-run"),
    )

    probe = AbacusEnvironmentProbeComponent()
    env_report = probe.probe(spec)
    assert env_report.abacus_available is True

    compiler = AbacusInputCompilerComponent()
    plan = compiler.compile(spec)
    assert plan.application_family == "relax"

    executor = AbacusExecutorComponent()

    def fake_run(command, *, cwd, capture_output, text, check, timeout):
        out_dir = cwd / "OUT.ABACUS"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "STRU_ION_D").write_text("relaxed structure")
        return type("_CompletedProcess", (), {"returncode": 0, "stdout": "ok", "stderr": ""})()

    monkeypatch.setattr("metaharness_ext.abacus.executor.subprocess.run", fake_run)

    artifact = executor.execute_plan(plan)
    assert artifact.status == "completed"
    assert artifact.return_code == 0
    assert any(Path(path).name.startswith("STRU") for path in artifact.structure_files)

    validator = AbacusValidatorComponent()
    report = validator.validate_run(artifact)
    assert report.passed is True
    assert report.status == "executed"
    assert report.blocks_promotion is False
    assert report.governance_state == "defer"
    assert report.scored_evidence is not None


def test_abacus_minimal_md_chain_with_stubbed_artifact_evidence(
    tmp_path: Path, monkeypatch
) -> None:
    spec = AbacusMdSpec(
        task_id="demo-md-1",
        executable=AbacusExecutableSpec(binary_name="echo"),
        structure=AbacusStructureSpec(content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n"),
        params={"md_nstep": 3},
        working_directory=str(tmp_path / "md-run"),
    )

    probe = AbacusEnvironmentProbeComponent()
    env_report = probe.probe(spec)
    assert env_report.abacus_available is True

    compiler = AbacusInputCompilerComponent()
    plan = compiler.compile(spec)
    assert plan.application_family == "md"

    executor = AbacusExecutorComponent()

    def fake_run(command, *, cwd, capture_output, text, check, timeout):
        out_dir = cwd / "OUT.ABACUS"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "MD_dump").write_text("trajectory")
        return type("_CompletedProcess", (), {"returncode": 0, "stdout": "ok", "stderr": ""})()

    monkeypatch.setattr("metaharness_ext.abacus.executor.subprocess.run", fake_run)

    artifact = executor.execute_plan(plan)
    assert artifact.status == "completed"
    assert artifact.return_code == 0
    assert any(Path(path).name.startswith("MD_dump") for path in artifact.output_files)

    validator = AbacusValidatorComponent()
    report = validator.validate_run(artifact)
    assert report.passed is True
    assert report.status == "executed"


def test_abacus_minimal_md_dp_chain_with_stubbed_artifact_evidence(
    tmp_path: Path, monkeypatch
) -> None:
    pot_file = tmp_path / "model.pb"
    pot_file.write_text("model")
    spec = AbacusMdSpec(
        task_id="demo-md-dp-1",
        executable=AbacusExecutableSpec(binary_name="echo"),
        structure=AbacusStructureSpec(content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n"),
        esolver_type="dp",
        pot_file=str(pot_file),
        params={"md_nstep": 3},
        working_directory=str(tmp_path / "md-dp-run"),
    )

    probe = AbacusEnvironmentProbeComponent()
    monkeypatch.setattr(probe, "_probe_version", lambda binary_path: "abacus 1.0")
    monkeypatch.setattr(probe, "_probe_info", lambda binary_path: "DeepMD enabled build")
    monkeypatch.setattr(probe, "_probe_check_input", lambda binary_path: "ok")
    env_report = probe.probe(spec)
    assert env_report.deeppmd_support_detected is True
    assert env_report.missing_prerequisites == []

    compiler = AbacusInputCompilerComponent()
    plan = compiler.compile(spec)
    assert plan.application_family == "md"
    assert plan.esolver_type == "dp"

    executor = AbacusExecutorComponent()

    def fake_run_dp(command, *, cwd, capture_output, text, check, timeout):
        out_dir = cwd / "OUT.ABACUS"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "MD_dump").write_text("trajectory")
        return type("_CompletedProcess", (), {"returncode": 0, "stdout": "ok", "stderr": ""})()

    monkeypatch.setattr("metaharness_ext.abacus.executor.subprocess.run", fake_run_dp)

    artifact = executor.execute_plan(plan)
    artifact.result_summary["missing_prerequisites"] = env_report.missing_prerequisites
    assert artifact.status == "completed"

    validator = AbacusValidatorComponent()
    report = validator.validate_run(artifact)
    assert report.passed is True
    assert report.status == "executed"


def test_abacus_minimal_md_dp_chain_blocks_when_deepmd_support_unknown(
    tmp_path: Path, monkeypatch
) -> None:
    pot_file = tmp_path / "model.pb"
    pot_file.write_text("model")
    spec = AbacusMdSpec(
        task_id="demo-md-dp-2",
        executable=AbacusExecutableSpec(binary_name="echo"),
        structure=AbacusStructureSpec(content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n"),
        esolver_type="dp",
        pot_file=str(pot_file),
        working_directory=str(tmp_path / "md-dp-blocked-run"),
    )

    probe = AbacusEnvironmentProbeComponent()
    monkeypatch.setattr(probe, "_probe_version", lambda binary_path: "abacus 1.0")
    monkeypatch.setattr(probe, "_probe_info", lambda binary_path: None)
    monkeypatch.setattr(probe, "_probe_check_input", lambda binary_path: "ok")
    env_report = probe.probe(spec)
    assert env_report.deeppmd_support_detected is None
    assert env_report.missing_prerequisites == ["deeppmd_support"]

    artifact = AbacusRunArtifact(
        task_id=spec.task_id,
        run_id=f"run-{spec.task_id}",
        application_family="md",
        status="unavailable",
        working_directory=str(tmp_path / "md-dp-blocked-run"),
        evidence_refs=list(env_report.evidence_refs),
        result_summary={
            "fallback_reason": "missing_prerequisites",
            "missing_prerequisites": env_report.missing_prerequisites,
            "esolver_type": "dp",
        },
    )

    validator = AbacusValidatorComponent()
    report = validator.validate_run(artifact)
    assert report.passed is False
    assert report.status == "environment_invalid"
    assert report.blocks_promotion is True
    assert report.governance_state == "blocked"
    assert any(ref.startswith("abacus://environment/") for ref in report.evidence_refs)


def test_abacus_minimal_graph_shape_matches_phase4_story() -> None:
    graph_path = (
        Path(__file__).resolve().parent.parent / "examples" / "graphs" / "abacus-minimal.xml"
    )
    graph = graph_path.read_text()

    assert "abacus_gateway.primary.task" in graph
    assert "abacus_environment.primary.task" in graph
    assert "abacus_input_compiler.primary.plan" in graph
    assert "abacus_executor.primary.run" in graph
    assert "abacus_validator.primary.run" in graph
