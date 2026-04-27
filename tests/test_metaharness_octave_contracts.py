import pytest

from metaharness_ext.octave.contracts import (
    OctaveExecutableSpec,
    OctaveExperimentSpec,
    OctaveOutputSpec,
    OctavePackageSpec,
    OctaveScriptSpec,
    OctaveStudyAxis,
    OctaveStudySpec,
    OctaveToleranceSpec,
)


def _spec() -> OctaveExperimentSpec:
    return OctaveExperimentSpec(
        task_id="octave-task",
        script=OctaveScriptSpec(mode="inline", inline_source="result = alpha + 1;"),
        parameters={"alpha": 1.0},
        expected_outputs=[
            OctaveOutputSpec(
                name="result",
                variable_name="result",
                tolerance=OctaveToleranceSpec(expected_value=2.0, atol=1e-9),
                unit="dimensionless",
            )
        ],
    )


def test_octave_experiment_spec_requires_declared_outputs() -> None:
    with pytest.raises(ValueError, match="expected_outputs"):
        OctaveExperimentSpec(
            task_id="missing-output",
            script=OctaveScriptSpec(mode="inline", inline_source="result = 1;"),
        )


def test_octave_contracts_capture_task_boundaries() -> None:
    spec = _spec()

    assert spec.family == "script_run"
    assert spec.executable.binary_name == "octave-cli"
    assert spec.script.inline_source == "result = alpha + 1;"
    assert spec.expected_outputs[0].metric_key == "result"
    assert spec.expected_outputs[0].tolerance is not None
    assert spec.expected_outputs[0].tolerance.expected_value == 2.0


def test_octave_contracts_reject_unsafe_identifiers() -> None:
    with pytest.raises(ValueError, match="task_id"):
        OctaveExperimentSpec(
            task_id="../escape",
            script=OctaveScriptSpec(mode="inline", inline_source="result = 1;"),
            expected_outputs=[OctaveOutputSpec(name="result")],
        )
    with pytest.raises(ValueError, match="package name"):
        OctavePackageSpec(name="../io")
    with pytest.raises(ValueError, match="timeout_seconds"):
        OctaveExecutableSpec(timeout_seconds=0)


def test_octave_study_spec_resolves_alias_fields() -> None:
    study = OctaveStudySpec(
        study_id="study-1",
        task_template=_spec(),
        axes=[OctaveStudyAxis(parameter_path="parameters.alpha", values=[1.0, 2.0])],
        objective="result.actual",
        goal="maximize",
    )

    assert study.base_task.task_id == "octave-task"
    assert study.resolved_task_id == "octave-task"
    assert study.resolved_objective_metric == "result.actual"
    assert study.axes[0].path == "parameters.alpha"
