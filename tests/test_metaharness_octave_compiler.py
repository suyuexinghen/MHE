from pathlib import Path

import pytest

from metaharness_ext.octave.contracts import (
    OctaveEnvironmentReport,
    OctaveExperimentSpec,
    OctaveInputAssetSpec,
    OctaveOutputSpec,
    OctavePackageFact,
    OctavePackageSpec,
    OctaveScriptSpec,
    OctaveToleranceSpec,
    OctaveWorkspaceSpec,
)
from metaharness_ext.octave.script_compiler import OctaveScriptCompilerComponent
from metaharness_ext.octave.workspace import OctaveWorkspaceManager


def _spec(tmp_path: Path) -> OctaveExperimentSpec:
    return OctaveExperimentSpec(
        task_id="compile-task",
        script=OctaveScriptSpec(mode="inline", inline_source="result = alpha + 1;"),
        workspace=OctaveWorkspaceSpec(working_directory=str(tmp_path / "run")),
        packages=[OctavePackageSpec(name="statistics")],
        parameters={"alpha": 2.0, "label": "trial"},
        expected_outputs=[
            OctaveOutputSpec(
                name="result",
                variable_name="result",
                tolerance=OctaveToleranceSpec(expected_value=3.0, atol=1e-9),
            )
        ],
    )


def test_octave_compiler_builds_deterministic_wrapper(tmp_path: Path) -> None:
    compiler = OctaveScriptCompilerComponent()
    spec = _spec(tmp_path)
    environment = OctaveEnvironmentReport(
        task_id=spec.task_id,
        available=True,
        status="available",
        workspace_writable=True,
        packages=[OctavePackageFact(name="statistics", version="1.6.0", available=True)],
    )

    plan = compiler.build_plan(spec, environment)
    second_plan = compiler.build_plan(spec, environment)

    assert plan.plan_id == second_plan.plan_id
    assert plan.workspace_dir == str(tmp_path / "run")
    assert plan.execution_params.argv[:4] == ["octave-cli", "--no-gui", "--quiet", "--no-init-file"]
    assert "pkg load statistics;" in plan.wrapper_source
    assert "alpha = 2.0;" in plan.wrapper_source
    assert "label = 'trial';" in plan.wrapper_source
    assert "result = alpha + 1;" in plan.wrapper_source
    assert "save('-text', 'outputs/result.txt', 'result');" in plan.wrapper_source
    assert plan.evidence_refs == [f"octave://plan/{spec.task_id}/{plan.plan_id}"]


def test_octave_compiler_rejects_missing_required_package(tmp_path: Path) -> None:
    compiler = OctaveScriptCompilerComponent()
    spec = _spec(tmp_path)
    environment = OctaveEnvironmentReport(
        task_id=spec.task_id,
        available=True,
        status="available",
        workspace_writable=True,
        packages=[],
    )

    with pytest.raises(ValueError, match="statistics"):
        compiler.compile(spec, environment)


def test_octave_workspace_materializes_wrapper_and_inputs(tmp_path: Path) -> None:
    input_file = tmp_path / "input.dat"
    input_file.write_text("1 2 3")
    spec = _spec(tmp_path).model_copy(
        update={
            "inputs": [
                OctaveInputAssetSpec(
                    source_path=str(input_file),
                    target_name="input.dat",
                    kind="data",
                )
            ]
        }
    )
    plan = OctaveScriptCompilerComponent().compile(spec)
    manager = OctaveWorkspaceManager()

    wrapper_path, input_paths = manager.materialize_plan(plan, tmp_path / "run")

    assert Path(wrapper_path).read_text() == plan.wrapper_source
    assert Path(input_paths[0]).read_text() == "1 2 3"
    assert (tmp_path / "run" / "outputs").is_dir()
