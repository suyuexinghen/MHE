from __future__ import annotations

from metaharness_ext.lean.contracts import (
    LeanDiagnostic,
    LeanEnvironmentReport,
    LeanRunArtifact,
    LeanRunPlan,
)
from metaharness_ext.lean.types import LeanDiagnosticSeverity, LeanValidationStatus
from metaharness_ext.lean.validator import LeanValidatorComponent


def test_validator_fully_proven() -> None:
    artifact = LeanRunArtifact(artifact_id="a", plan_ref="p", exit_code=0)

    report = LeanValidatorComponent().validate_run(artifact)

    assert report.status is LeanValidationStatus.FULLY_PROVEN
    assert report.blocks_promotion is False
    assert report.completeness_ratio == 1.0


def test_validator_partially_proven_with_budget_remaining() -> None:
    artifact = LeanRunArtifact(
        artifact_id="a",
        plan_ref="p",
        exit_code=0,
        sorry_locations=[LeanDiagnostic(message="sorry", code="sorry")],
    )
    plan = LeanRunPlan(
        plan_id="p",
        task_ref="task",
        target_file="Proofs/Main.lean",
        execution_params={"attempts": 1, "budget": 3},
    )

    report = LeanValidatorComponent().validate_run(artifact, plan)

    assert report.status is LeanValidationStatus.PARTIALLY_PROVEN
    assert report.blocks_promotion is True
    assert report.retriable is True


def test_validator_budget_exhausted() -> None:
    artifact = LeanRunArtifact(
        artifact_id="a",
        plan_ref="p",
        exit_code=0,
        sorry_locations=[LeanDiagnostic(message="sorry", code="sorry")],
    )
    plan = LeanRunPlan(
        plan_id="p",
        task_ref="task",
        target_file="Proofs/Main.lean",
        execution_params={"attempts": 3, "budget": 3},
    )

    report = LeanValidatorComponent().validate_run(artifact, plan)

    assert report.status is LeanValidationStatus.BUDGET_EXHAUSTED
    assert report.retriable is False


def test_validator_compilation_failed() -> None:
    artifact = LeanRunArtifact(
        artifact_id="a",
        plan_ref="p",
        exit_code=1,
        diagnostics=[
            LeanDiagnostic(severity=LeanDiagnosticSeverity.ERROR, message="unknown identifier")
        ],
    )

    report = LeanValidatorComponent().validate_run(artifact)

    assert report.status is LeanValidationStatus.COMPILATION_FAILED
    assert report.retriable is True


def test_validator_timeout() -> None:
    artifact = LeanRunArtifact(
        artifact_id="a",
        plan_ref="p",
        exit_code=124,
        diagnostics=[LeanDiagnostic(message="timeout", code="timeout")],
    )

    report = LeanValidatorComponent().validate_run(artifact)

    assert report.status is LeanValidationStatus.TIMEOUT
    assert report.retriable is True


def test_validator_environment_failed() -> None:
    artifact = LeanRunArtifact(artifact_id="a", plan_ref="p", exit_code=0)
    environment = LeanEnvironmentReport(blocks_promotion=True)

    report = LeanValidatorComponent().validate_run(artifact, environment_report=environment)

    assert report.status is LeanValidationStatus.ENVIRONMENT_FAILED


def test_validator_workspace_error() -> None:
    artifact = LeanRunArtifact(
        artifact_id="a",
        plan_ref="p",
        exit_code=1,
        diagnostics=[LeanDiagnostic(message="workspace failed", code="workspace_error")],
    )

    report = LeanValidatorComponent().validate_run(artifact)

    assert report.status is LeanValidationStatus.WORKSPACE_ERROR
    assert report.retriable is False


def test_validator_statement_snapshot_and_modified_drift(tmp_path) -> None:
    source = tmp_path / "Main.lean"
    source.write_text("theorem main : True := by trivial\n")
    validator = LeanValidatorComponent()
    before = validator.snapshot_statement(source)
    source.write_text("theorem main : False := by contradiction\n")
    after = validator.snapshot_statement(source)

    report = validator.validate_drift(before, after)

    assert report.status is LeanValidationStatus.STATEMENT_DRIFT
    assert report.blocks_promotion is True
    assert report.drift_changes == [{"name": "main", "change": "modified"}]


def test_validator_added_drift_does_not_block(tmp_path) -> None:
    source = tmp_path / "Main.lean"
    source.write_text("theorem main : True := by trivial\n")
    validator = LeanValidatorComponent()
    before = validator.snapshot_statement(source)
    source.write_text("theorem main : True := by trivial\nlemma helper : True := by trivial\n")
    after = validator.snapshot_statement(source)

    report = validator.validate_drift(before, after)

    assert report.status is LeanValidationStatus.STATEMENT_DRIFT
    assert report.blocks_promotion is False
    assert report.drift_changes == [{"name": "helper", "change": "added"}]


def test_validator_removed_drift_blocks(tmp_path) -> None:
    source = tmp_path / "Main.lean"
    source.write_text("theorem main : True := by trivial\nlemma helper : True := by trivial\n")
    validator = LeanValidatorComponent()
    before = validator.snapshot_statement(source)
    source.write_text("theorem main : True := by trivial\n")
    after = validator.snapshot_statement(source)

    report = validator.validate_drift(before, after)

    assert report.blocks_promotion is True
    assert report.drift_changes == [{"name": "helper", "change": "removed"}]
