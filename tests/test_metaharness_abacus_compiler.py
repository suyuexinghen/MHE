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
    assert plan.control_files.input_content == plan.input_content
    assert plan.control_files.structure_content == plan.structure_content
    assert plan.workspace_layout.working_directory == plan.working_directory
    assert plan.workspace_layout.output_root == plan.output_root
    assert plan.runtime_assets.all_paths() == []
    assert plan.lifecycle_state.compiled is True
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
    assert plan.expected_logs == ["running_nscf.log"]
    assert plan.required_runtime_paths == ["/tmp/charge-density.cube"]
    assert plan.runtime_assets.charge_density_path == "/tmp/charge-density.cube"
    assert plan.runtime_assets.restart_inputs == []
    assert plan.kpoints_content is not None
    assert plan.control_files.kpoints_name == "KPT"
    assert "calculation nscf" in plan.input_content
    assert "charge_density_path /tmp/charge-density.cube" in plan.input_content


def test_abacus_compiler_builds_relax_plan() -> None:
    spec = AbacusRelaxSpec(
        task_id="task-relax",
        executable=AbacusExecutableSpec(binary_name="abacus"),
        structure=AbacusStructureSpec(content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n"),
        restart_file_path="/tmp/restart.stru",
        relax_controls={"relax_nmax": 10},
    )

    compiler = AbacusInputCompilerComponent()
    plan = compiler.compile(spec)

    assert plan.application_family == "relax"
    assert plan.output_root == "OUT.ABACUS"
    assert plan.expected_logs == ["running_relax.log", "running_scf.log"]
    assert plan.required_runtime_paths == ["/tmp/restart.stru"]
    assert plan.runtime_assets.restart_inputs == ["/tmp/restart.stru"]
    assert "calculation relax" in plan.input_content
    assert "relax_nmax 10" in plan.input_content
    assert "restart_file_path /tmp/restart.stru" in plan.input_content


def test_abacus_compiler_promotes_relax_restart_from_legacy_controls() -> None:
    spec = AbacusRelaxSpec(
        task_id="task-relax-legacy",
        executable=AbacusExecutableSpec(binary_name="abacus"),
        structure=AbacusStructureSpec(content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n"),
        relax_controls={"relax_nmax": 10, "restart_file_path": "/tmp/restart.stru"},
    )

    assert spec.restart_file_path == "/tmp/restart.stru"
    assert "restart_file_path" not in spec.relax_controls

    plan = AbacusInputCompilerComponent().compile(spec)

    assert plan.required_runtime_paths == ["/tmp/restart.stru"]
    assert plan.runtime_assets.restart_inputs == ["/tmp/restart.stru"]
    assert plan.input_content.count("restart_file_path /tmp/restart.stru") == 1


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


def test_abacus_compiler_renders_params_deterministically() -> None:
    compiler = AbacusInputCompilerComponent()
    structure = AbacusStructureSpec(content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n")
    forward = AbacusMdSpec(
        task_id="task-md-forward",
        executable=AbacusExecutableSpec(binary_name="abacus"),
        structure=structure,
        params={"md_nstep": 5, "md_dt": 1.0},
    )
    reverse = AbacusMdSpec(
        task_id="task-md-reverse",
        executable=AbacusExecutableSpec(binary_name="abacus"),
        structure=structure,
        params={"md_dt": 1.0, "md_nstep": 5},
    )

    forward_input = compiler.compile(forward).input_content
    reverse_input = compiler.compile(reverse).input_content

    assert forward_input == reverse_input
    assert forward_input.index("md_dt 1.0") < forward_input.index("md_nstep 5")


def test_abacus_compiler_renders_relax_controls_deterministically() -> None:
    compiler = AbacusInputCompilerComponent()
    structure = AbacusStructureSpec(content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n")
    forward = AbacusRelaxSpec(
        task_id="task-relax-forward",
        executable=AbacusExecutableSpec(binary_name="abacus"),
        structure=structure,
        relax_controls={"relax_nmax": 10, "force_thr": 0.01},
    )
    reverse = AbacusRelaxSpec(
        task_id="task-relax-reverse",
        executable=AbacusExecutableSpec(binary_name="abacus"),
        structure=structure,
        relax_controls={"force_thr": 0.01, "relax_nmax": 10},
    )

    forward_input = compiler.compile(forward).input_content
    reverse_input = compiler.compile(reverse).input_content

    assert forward_input == reverse_input
    assert forward_input.index("force_thr 0.01") < forward_input.index("relax_nmax 10")


def test_abacus_nscf_requires_prerequisite_reference() -> None:
    with pytest.raises(ValueError, match="charge_density_path or restart_file_path"):
        AbacusNscfSpec(
            task_id="task-invalid",
            executable=AbacusExecutableSpec(binary_name="abacus"),
            structure=AbacusStructureSpec(content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n"),
            kpoints=AbacusKPointSpec(content="K_POINTS\n1\n0.0 0.0 0.0 1\n"),
        )


def test_abacus_compiler_builds_nscf_plan_with_restart_only_prerequisite() -> None:
    spec = AbacusNscfSpec(
        task_id="task-nscf-restart-only",
        executable=AbacusExecutableSpec(binary_name="abacus"),
        structure=AbacusStructureSpec(content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n"),
        kpoints=AbacusKPointSpec(content="K_POINTS\n1\n0.0 0.0 0.0 1\n"),
        restart_file_path="/tmp/restart.stru",
    )

    plan = AbacusInputCompilerComponent().compile(spec)

    assert plan.required_runtime_paths == ["/tmp/restart.stru"]
    assert plan.runtime_assets.restart_inputs == ["/tmp/restart.stru"]
    assert plan.runtime_assets.charge_density_path is None
    assert "restart_file_path /tmp/restart.stru" in plan.input_content
    assert "charge_density_path" not in plan.input_content


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
    assert plan.runtime_assets.pot_file == "/tmp/model.pb"
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


def test_abacus_compiler_groups_required_runtime_assets() -> None:
    spec = AbacusNscfSpec(
        task_id="task-nscf-assets",
        executable=AbacusExecutableSpec(binary_name="abacus"),
        structure=AbacusStructureSpec(content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n"),
        kpoints=AbacusKPointSpec(content="K_POINTS\n1\n0.0 0.0 0.0 1\n"),
        charge_density_path="/tmp/charge-density.cube",
        restart_file_path="/tmp/restart.stru",
        required_paths=["/tmp/shared.dat", "/tmp/shared.dat"],
        pseudo_files=["/tmp/Si.upf"],
        orbital_files=["/tmp/Si.orb"],
    )

    plan = AbacusInputCompilerComponent().compile(spec)

    assert plan.runtime_assets.explicit_required_paths == ["/tmp/shared.dat", "/tmp/shared.dat"]
    assert plan.runtime_assets.pseudo_files == ["/tmp/Si.upf"]
    assert plan.runtime_assets.orbital_files == ["/tmp/Si.orb"]
    assert plan.runtime_assets.restart_inputs == ["/tmp/restart.stru"]
    assert plan.runtime_assets.charge_density_path == "/tmp/charge-density.cube"
    assert plan.required_runtime_paths == [
        "/tmp/shared.dat",
        "/tmp/Si.upf",
        "/tmp/Si.orb",
        "/tmp/restart.stru",
        "/tmp/charge-density.cube",
    ]


def test_abacus_compiler_preserves_explicit_working_directory() -> None:
    spec = AbacusScfSpec(
        task_id="task-custom-workdir",
        executable=AbacusExecutableSpec(binary_name="abacus"),
        structure=AbacusStructureSpec(content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n"),
        working_directory="~/abacus-runs/custom-task",
    )

    plan = AbacusInputCompilerComponent().compile(spec)

    assert plan.working_directory == "~/abacus-runs/custom-task"
    assert plan.workspace_layout.working_directory == "~/abacus-runs/custom-task"


def test_abacus_compiler_uses_default_working_directory_when_missing() -> None:
    spec = AbacusScfSpec(
        task_id="task-default-workdir",
        executable=AbacusExecutableSpec(binary_name="abacus"),
        structure=AbacusStructureSpec(content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n"),
    )

    plan = AbacusInputCompilerComponent().compile(spec)

    assert plan.working_directory == "./.runs/abacus/task-default-workdir/run-task-default-workdir"
    assert (
        plan.workspace_layout.working_directory
        == "./.runs/abacus/task-default-workdir/run-task-default-workdir"
    )


def test_abacus_relax_rejects_conflicting_restart_paths() -> None:
    with pytest.raises(
        ValueError, match="restart_file_path does not match relax_controls.restart_file_path"
    ):
        AbacusRelaxSpec(
            task_id="task-relax-conflict",
            executable=AbacusExecutableSpec(binary_name="abacus"),
            structure=AbacusStructureSpec(content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n"),
            restart_file_path="/tmp/new.restart",
            relax_controls={"restart_file_path": "/tmp/old.restart"},
        )

    with pytest.raises(ValueError, match="basis_type=lcao is not supported for MD"):
        AbacusMdSpec(
            task_id="task-md-lcao",
            executable=AbacusExecutableSpec(binary_name="abacus"),
            structure=AbacusStructureSpec(content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n"),
            basis_type="lcao",
        )
