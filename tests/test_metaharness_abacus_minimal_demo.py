from metaharness_ext.abacus.contracts import (
    AbacusExecutableSpec,
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
