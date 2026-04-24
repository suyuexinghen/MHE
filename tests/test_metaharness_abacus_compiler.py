import pytest

from metaharness_ext.abacus.contracts import (
    AbacusEnvironmentReport,
    AbacusExecutableSpec,
    AbacusKPointSpec,
    AbacusMdSpec,
    AbacusNscfSpec,
    AbacusRelaxSpec,
    AbacusScfSpec,
    AbacusStructureSpec,
)
from metaharness_ext.abacus.input_compiler import AbacusInputCompilerComponent


def test_abacus_compiler_builds_scf_plan() -> None:
    spec = AbacusScfSpec(
        task_id="task-scf",
        executable=AbacusExecutableSpec(binary_name="abacus"),
        structure=AbacusStructureSpec(content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n"),
    )

    compiler = AbacusInputCompilerComponent()
    plan = compiler.compile(spec)

    assert plan.application_family == "scf"
    assert plan.output_root == "OUT.ABACUS"
    assert plan.expected_outputs == ["OUT.ABACUS/"]
    assert plan.expected_logs == ["running_scf.log"]
    assert plan.required_runtime_paths == []
    assert "calculation scf" in plan.input_content


def test_abacus_compiler_builds_nscf_plan() -> None:
    spec = AbacusNscfSpec(
        task_id="task-nscf",
        executable=AbacusExecutableSpec(binary_name="abacus"),
        structure=AbacusStructureSpec(content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n"),
        kpoints=AbacusKPointSpec(content="K_POINTS\n1\n0.0 0.0 0.0 1\n"),
        charge_density_path="/tmp/charge-density.cube",
    )

    compiler = AbacusInputCompilerComponent()
    plan = compiler.compile(spec)

    assert plan.application_family == "nscf"
    assert plan.output_root == "OUT.ABACUS"
    assert plan.expected_logs == ["running_nscf.log", "running_scf.log"]
    assert plan.required_runtime_paths == ["/tmp/charge-density.cube"]
    assert plan.kpoints_content is not None
    assert "calculation nscf" in plan.input_content
    assert "charge_density_path /tmp/charge-density.cube" in plan.input_content


def test_abacus_compiler_builds_relax_plan() -> None:
    spec = AbacusRelaxSpec(
        task_id="task-relax",
        executable=AbacusExecutableSpec(binary_name="abacus"),
        structure=AbacusStructureSpec(content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n"),
        relax_controls={"relax_nmax": 10, "restart_file_path": "/tmp/restart.stru"},
    )

    compiler = AbacusInputCompilerComponent()
    plan = compiler.compile(spec)

    assert plan.application_family == "relax"
    assert plan.output_root == "OUT.ABACUS"
    assert plan.expected_logs == ["running_relax.log", "running_scf.log"]
    assert plan.required_runtime_paths == ["/tmp/restart.stru"]
    assert "calculation relax" in plan.input_content
    assert "relax_nmax 10" in plan.input_content
    assert "restart_file_path /tmp/restart.stru" in plan.input_content


def test_abacus_compiler_builds_md_plan() -> None:
    spec = AbacusMdSpec(
        task_id="task-md",
        executable=AbacusExecutableSpec(binary_name="abacus"),
        structure=AbacusStructureSpec(content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n"),
        params={"md_nstep": 5, "md_dt": 1.0},
    )

    compiler = AbacusInputCompilerComponent()
    plan = compiler.compile(spec)

    assert plan.application_family == "md"
    assert plan.output_root == "OUT.ABACUS"
    assert plan.expected_outputs == ["OUT.ABACUS/"]
    assert plan.expected_logs == ["running_md.log"]
    assert plan.required_runtime_paths == []
    assert "calculation md" in plan.input_content
    assert "md_nstep 5" in plan.input_content
    assert "md_dt 1.0" in plan.input_content


def test_abacus_nscf_requires_prerequisite_reference() -> None:
    with pytest.raises(ValueError, match="charge_density_path or restart_file_path"):
        AbacusNscfSpec(
            task_id="task-invalid",
            executable=AbacusExecutableSpec(binary_name="abacus"),
            structure=AbacusStructureSpec(content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n"),
            kpoints=AbacusKPointSpec(content="K_POINTS\n1\n0.0 0.0 0.0 1\n"),
        )


def test_abacus_compiler_builds_md_dp_plan() -> None:
    spec = AbacusMdSpec(
        task_id="task-md-dp",
        executable=AbacusExecutableSpec(binary_name="abacus"),
        structure=AbacusStructureSpec(content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n"),
        esolver_type="dp",
        pot_file="/tmp/model.pb",
    )

    compiler = AbacusInputCompilerComponent()
    plan = compiler.compile(spec)

    assert plan.application_family == "md"
    assert plan.esolver_type == "dp"
    assert plan.pot_file == "/tmp/model.pb"
    assert plan.required_runtime_paths == ["/tmp/model.pb"]
    assert plan.environment_prerequisites == ["deeppmd_support"]
    assert "pot_file /tmp/model.pb" in plan.input_content


def test_abacus_compiler_prefers_environment_report_when_provided() -> None:
    spec = AbacusMdSpec(
        task_id="task-md-dp-env",
        executable=AbacusExecutableSpec(binary_name="abacus"),
        structure=AbacusStructureSpec(content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n"),
        esolver_type="dp",
        pot_file="/tmp/model.pb",
    )
    environment = AbacusEnvironmentReport(
        environment_prerequisites=["deeppmd_support", "gpu_support"],
        evidence_refs=["abacus://environment/task-md-dp-env", "abacus://binary/abacus"],
    )

    compiler = AbacusInputCompilerComponent()
    plan = compiler.compile(spec, environment)

    assert plan.environment_prerequisites == ["deeppmd_support", "gpu_support"]
    assert plan.environment_evidence_refs == [
        "abacus://environment/task-md-dp-env",
        "abacus://binary/abacus",
    ]


def test_abacus_md_dp_requires_pot_file() -> None:
    with pytest.raises(ValueError, match="esolver_type=dp requires pot_file"):
        AbacusMdSpec(
            task_id="task-md-dp",
            executable=AbacusExecutableSpec(binary_name="abacus"),
            structure=AbacusStructureSpec(content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n"),
            esolver_type="dp",
        )


def test_abacus_md_rejects_lcao_baseline() -> None:
    with pytest.raises(ValueError, match="basis_type=lcao is not supported for MD"):
        AbacusMdSpec(
            task_id="task-md-lcao",
            executable=AbacusExecutableSpec(binary_name="abacus"),
            structure=AbacusStructureSpec(content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n"),
            basis_type="lcao",
        )
