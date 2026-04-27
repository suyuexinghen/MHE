from __future__ import annotations

import json
import subprocess
from pathlib import Path

from metaharness.sdk.manifest import ComponentManifest
from metaharness_ext.octave.contracts import (
    OctaveExecutableSpec,
    OctaveExperimentSpec,
    OctaveInvariantSpec,
    OctaveOutputSpec,
    OctaveRunArtifact,
    OctaveScriptSpec,
    OctaveStudyAxis,
    OctaveStudySpec,
    OctaveToleranceSpec,
)
from metaharness_ext.octave.environment import OctaveEnvironmentProbeComponent
from metaharness_ext.octave.evidence import build_evidence_bundle
from metaharness_ext.octave.executor import OctaveExecutorComponent
from metaharness_ext.octave.policy import OctaveEvidencePolicy
from metaharness_ext.octave.scientific_context import OctaveScientificContextAdapter
from metaharness_ext.octave.script_compiler import OctaveScriptCompilerComponent
from metaharness_ext.octave.study import OctaveStudyComponent
from metaharness_ext.octave.validator import OctaveValidatorComponent


def _spec(tmp_path: Path) -> OctaveExperimentSpec:
    return OctaveExperimentSpec(
        task_id="octave-demo",
        script=OctaveScriptSpec(mode="inline", inline_source="result = alpha + 1;"),
        workspace={"working_directory": str(tmp_path / "run")},
        parameters={"alpha": 1.0},
        expected_outputs=[
            OctaveOutputSpec(
                name="result",
                variable_name="result",
                tolerance=OctaveToleranceSpec(expected_value=2.0),
            )
        ],
    )


def test_octave_component_manifests_validate() -> None:
    manifest_dir = Path("src/metaharness_ext/octave")

    for path in manifest_dir.glob("*.json"):
        manifest = ComponentManifest.model_validate(json.loads(path.read_text()))
        assert manifest.name.startswith("octave")
        assert manifest.harness_version


def test_octave_compiler_generates_safe_wrapper(tmp_path: Path) -> None:
    plan = OctaveScriptCompilerComponent().build_plan(_spec(tmp_path))

    assert plan.execution_params.argv[:4] == [
        "octave-cli",
        "--no-gui",
        "--quiet",
        "--no-init-file",
    ]
    assert "save('-text', 'mhe_status.txt'" in plan.wrapper_source
    assert "result = alpha + 1;" in plan.wrapper_source


def test_octave_environment_missing_binary_blocks_promotion(tmp_path: Path) -> None:
    spec = _spec(tmp_path).model_copy(
        update={"executable": OctaveExecutableSpec(binary_name="missing-octave-cli-for-test")}
    )

    report = OctaveEnvironmentProbeComponent().probe(spec)

    assert not report.available
    assert report.blocks_promotion
    assert report.missing_prerequisites


def test_octave_executor_uses_no_init_file(monkeypatch, tmp_path: Path) -> None:
    spec = _spec(tmp_path)
    plan = OctaveScriptCompilerComponent().build_plan(spec)
    captured: dict[str, object] = {}

    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/octave-cli")

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["cwd"] = kwargs["cwd"]
        output_path = Path(kwargs["cwd"]) / "outputs" / "result.txt"
        output_path.write_text("# Created by Octave\nresult = 2\n")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(subprocess, "run", fake_run)

    artifact = OctaveExecutorComponent().execute_plan(plan)

    assert "--no-init-file" in captured["command"]
    assert artifact.status == "completed"
    assert artifact.output_files


def test_octave_validator_policy_and_evidence_ready(tmp_path: Path) -> None:
    spec = _spec(tmp_path)
    plan = OctaveScriptCompilerComponent().build_plan(spec)
    artifact = OctaveRunArtifact(
        artifact_id="artifact-1",
        run_id=plan.run_id,
        task_id=plan.task_id,
        plan_ref=plan.plan_id,
        status="completed",
        return_code=0,
        working_directory=str(tmp_path),
        output_files=[str(tmp_path / "result.txt")],
        stdout_path=str(tmp_path / "stdout.log"),
        stderr_path=str(tmp_path / "stderr.log"),
        summary_metrics={"result": 2.0},
    )

    validation = OctaveValidatorComponent().validate_run(artifact, plan)
    bundle = build_evidence_bundle(artifact, validation, plan=plan)
    policy = OctaveEvidencePolicy().evaluate(bundle)

    assert validation.passed
    assert validation.governance_state == "ready"
    assert policy.governance_state == "ready"


def test_octave_scientific_context_adds_deferred_invariant(tmp_path: Path) -> None:
    spec = _spec(tmp_path).model_copy(deep=True)
    spec.expected_outputs[0].invariants = [
        OctaveInvariantSpec(expression="result > 0", description="positive result")
    ]
    plan = OctaveScriptCompilerComponent().build_plan(spec)
    artifact = OctaveRunArtifact(
        artifact_id="artifact-1",
        run_id=plan.run_id,
        task_id=plan.task_id,
        plan_ref=plan.plan_id,
        status="completed",
        return_code=0,
        working_directory=str(tmp_path),
        summary_metrics={"result": 2.0},
    )
    validation = OctaveValidatorComponent().validate_run(artifact, plan)

    result = OctaveScientificContextAdapter().post_validate(validation, artifact, spec)

    assert any(issue.code == "octave_context_invariant_deferred" for issue in result.issues)
    assert result.scored_evidence is not None


def test_octave_study_component_recommends_best_trial(tmp_path: Path) -> None:
    spec = _spec(tmp_path)
    study = OctaveStudySpec(
        study_id="study-1",
        task_template=spec,
        axes=[OctaveStudyAxis(parameter_path="parameters.alpha", values=[1.0, 2.0])],
        objective_metric="result.actual",
        goal="maximize",
    )

    class Compiler:
        def build_plan(self, task):
            return OctaveScriptCompilerComponent().build_plan(task)

    class Executor:
        def execute_plan(self, plan):
            alpha = 2.0 if "alpha = 2.0;" in plan.wrapper_source else 1.0
            return OctaveRunArtifact(
                artifact_id=f"artifact-{plan.run_id}",
                run_id=plan.run_id,
                task_id=plan.task_id,
                plan_ref=plan.plan_id,
                status="completed",
                return_code=0,
                working_directory=str(tmp_path),
                output_files=[str(tmp_path / f"{plan.run_id}.txt")],
                stdout_path=str(tmp_path / "stdout.log"),
                stderr_path=str(tmp_path / "stderr.log"),
                summary_metrics={"result": alpha + 1.0},
            )

    class Validator:
        def validate_run(self, run, plan):
            report = OctaveValidatorComponent().validate_run(run, plan)
            report.issues = [
                issue for issue in report.issues if issue.code != "octave_output_missing"
            ]
            return report

    report = OctaveStudyComponent().run_study(
        study,
        compiler=Compiler(),
        executor=Executor(),
        validator=Validator(),
    )

    assert len(report.trials) == 2
    assert report.best_trial_id is not None
    assert report.recommended_parameters
