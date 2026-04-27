from pathlib import Path

from metaharness_ext.octave.contracts import (
    OctaveEnvironmentReport,
    OctaveExperimentSpec,
    OctaveOutputSpec,
    OctaveRunArtifact,
    OctaveRunPlan,
    OctaveScriptSpec,
    OctaveStudyAxis,
    OctaveStudySpec,
    OctaveToleranceSpec,
)
from metaharness_ext.octave.evidence import build_evidence_bundle
from metaharness_ext.octave.policy import OctaveEvidencePolicy
from metaharness_ext.octave.script_compiler import OctaveScriptCompilerComponent
from metaharness_ext.octave.study import OctaveStudyComponent
from metaharness_ext.octave.validator import OctaveValidatorComponent


def _spec() -> OctaveExperimentSpec:
    return OctaveExperimentSpec(
        task_id="validate-task",
        script=OctaveScriptSpec(mode="inline", inline_source="result = alpha + 1;"),
        parameters={"alpha": 1.0},
        expected_outputs=[
            OctaveOutputSpec(
                name="result",
                variable_name="result",
                tolerance=OctaveToleranceSpec(expected_value=2.0, atol=1e-8, rtol=0.0),
            )
        ],
    )


def _plan() -> OctaveRunPlan:
    return OctaveScriptCompilerComponent().compile(_spec())


def _artifact(tmp_path: Path, plan: OctaveRunPlan, *, result: float = 2.0) -> OctaveRunArtifact:
    tmp_path.mkdir(parents=True, exist_ok=True)
    output_file = tmp_path / "result.txt"
    stdout_file = tmp_path / "stdout.log"
    stderr_file = tmp_path / "stderr.log"
    output_file.write_text(str(result))
    stdout_file.write_text("ok")
    stderr_file.write_text("")
    return OctaveRunArtifact(
        artifact_id="artifact-1",
        run_id=plan.run_id,
        task_id=plan.task_id,
        plan_ref=plan.plan_id,
        status="completed",
        return_code=0,
        working_directory=str(tmp_path),
        output_files=[str(output_file)],
        log_files=[str(stdout_file), str(stderr_file)],
        stdout_path=str(stdout_file),
        stderr_path=str(stderr_file),
        summary_metrics={"result": result},
        evidence_refs=[f"octave://run/{plan.task_id}/{plan.run_id}"],
    )


def test_octave_validator_accepts_completed_run_with_toleranced_metric(tmp_path: Path) -> None:
    plan = _plan()
    artifact = _artifact(tmp_path, plan)

    report = OctaveValidatorComponent().validate_run(artifact, plan)

    assert report.passed is True
    assert report.status == "executed"
    assert report.governance_state == "ready"
    assert report.numeric_metrics["result.actual"] == 2.0
    assert report.numeric_metrics["result.within_tolerance"] is True
    assert report.blocks_promotion is False
    assert report.scored_evidence is not None


def test_octave_validator_blocks_numeric_tolerance_failure(tmp_path: Path) -> None:
    plan = _plan()
    artifact = _artifact(tmp_path, plan, result=3.0)

    report = OctaveValidatorComponent().validate_run(artifact, plan)

    assert report.passed is False
    assert report.status == "numeric_validation_failed"
    assert report.governance_state == "blocked"
    assert report.numeric_metrics["result.within_tolerance"] is False
    assert report.issues[0].code == "octave_numeric_tolerance_failed"


def test_octave_evidence_policy_allows_complete_validated_bundle(tmp_path: Path) -> None:
    plan = _plan()
    artifact = _artifact(tmp_path, plan)
    validation = OctaveValidatorComponent().validate_run(artifact, plan)
    environment = OctaveEnvironmentReport(
        task_id=plan.task_id,
        available=True,
        status="available",
        workspace_writable=True,
    )

    bundle = build_evidence_bundle(artifact, validation, environment=environment, plan=plan)
    report = OctaveEvidencePolicy().evaluate(bundle)

    assert (
        bundle.validation_ref
        == f"octave://validation/{validation.task_id}/{validation.artifact_ref}"
    )
    assert report.passed is True
    assert report.decision == "allow"
    assert report.governance_state == "ready"
    assert report.gates[0].gate == "octave_evidence_ready"


def test_octave_evidence_policy_rejects_unavailable_environment(tmp_path: Path) -> None:
    plan = _plan()
    artifact = _artifact(tmp_path, plan)
    validation = OctaveValidatorComponent().validate_run(artifact, plan)
    environment = OctaveEnvironmentReport(
        task_id=plan.task_id,
        available=False,
        status="prerequisite_missing",
        workspace_writable=True,
        prerequisite_errors=["Octave binary not found"],
        blocks_promotion=True,
    )

    bundle = build_evidence_bundle(artifact, validation, environment=environment, plan=plan)
    report = OctaveEvidencePolicy().evaluate(bundle)

    assert report.passed is False
    assert report.decision == "reject"
    assert report.governance_state == "blocked"
    assert report.gates[0].gate == "octave_environment_readiness"


class _Compiler:
    def build_plan(self, spec: OctaveExperimentSpec) -> OctaveRunPlan:
        return OctaveScriptCompilerComponent().compile(spec)


class _Executor:
    def __init__(self, tmp_path: Path) -> None:
        self._tmp_path = tmp_path

    def execute_plan(self, plan: OctaveRunPlan) -> OctaveRunArtifact:
        alpha = float(plan.graph_metadata.get("alpha", 0.0))
        result = alpha + 1.0
        return _artifact(self._tmp_path / plan.run_id, plan, result=result)


class _Validator:
    def validate_run(self, artifact: OctaveRunArtifact, plan: OctaveRunPlan):
        return OctaveValidatorComponent().validate_run(artifact, plan)


def test_octave_study_runs_grid_and_recommends_best_ready_trial(tmp_path: Path) -> None:
    base = _spec().model_copy(update={"graph_metadata": {"alpha": 1.0}})
    study = OctaveStudySpec(
        study_id="study-1",
        task_template=base,
        axes=[OctaveStudyAxis(parameter_path="graph_metadata.alpha", values=[1.0, 2.0])],
        objective="result.actual",
        goal="maximize",
    )

    report = OctaveStudyComponent().run_study(
        study,
        compiler=_Compiler(),
        executor=_Executor(tmp_path),
        validator=_Validator(),
    )

    assert len(report.trials) == 2
    assert report.best_trial_id == report.trials[0].trial_id
    assert report.recommended_parameters == {"graph_metadata.alpha": 1.0}
    assert report.summary_metrics["ready_count"] == 1.0
    assert report.convergence_analysis["objective_metric"] == "result.actual"
