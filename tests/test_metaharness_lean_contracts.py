from __future__ import annotations

from metaharness_ext.lean.backends import MockLeanBackend
from metaharness_ext.lean.contracts import (
    LeanBlueprint,
    LeanBlueprintItem,
    LeanDiagnostic,
    LeanEnvironmentReport,
    LeanEvidenceBundle,
    LeanProjectSpec,
    LeanProvenance,
    LeanRunArtifact,
    LeanTaskSpec,
    LeanValidationReport,
)
from metaharness_ext.lean.types import (
    LeanBlueprintItemStatus,
    LeanDiagnosticSeverity,
    LeanFamily,
    LeanValidationStatus,
)


def test_task_spec_roundtrip_with_project() -> None:
    task = LeanTaskSpec(
        family=LeanFamily.FORMAL_PROOF,
        target_file="Proofs/Main.lean",
        target_lemma="main_theorem",
        project=LeanProjectSpec(
            project_root="/tmp/lean-project",
            toolchain_version="leanprover/lean4:v4.15.0",
            lakefile_path="/tmp/lean-project/lakefile.lean",
        ),
        budget=3,
    )

    restored = LeanTaskSpec.model_validate_json(task.model_dump_json())

    assert restored.project is not None
    assert restored.project.project_root == "/tmp/lean-project"
    assert restored.target_lemma == "main_theorem"


def test_task_spec_roundtrip_without_project() -> None:
    task = LeanTaskSpec(target_file="Proofs/Main.lean", project=None)

    restored = LeanTaskSpec.model_validate_json(task.model_dump_json())

    assert restored.project is None


def test_blueprint_item_roundtrip() -> None:
    item = LeanBlueprintItem(
        label="lem:helper",
        lean_declaration="MyProject.helper",
        file="Proofs/Main.lean",
        uses=["lem:base"],
        status=LeanBlueprintItemStatus.PARTIAL,
        attempts=2,
        budget=8,
        informal_statement="helper statement",
        informal_proof="helper proof",
    )

    restored = LeanBlueprintItem.model_validate_json(item.model_dump_json())

    assert restored.uses == ["lem:base"]
    assert restored.status is LeanBlueprintItemStatus.PARTIAL


def test_run_artifact_roundtrip_with_diagnostics() -> None:
    diagnostic = LeanDiagnostic(
        file="Proofs/Main.lean",
        line=12,
        column=4,
        severity=LeanDiagnosticSeverity.WARNING,
        message="declaration uses sorry",
        code="sorry",
    )
    artifact = LeanRunArtifact(
        artifact_id="artifact-1",
        plan_ref="plan-1",
        exit_code=0,
        stdout="ok",
        diagnostics=[diagnostic],
        sorry_locations=[diagnostic],
    )

    restored = LeanRunArtifact.model_validate_json(artifact.model_dump_json())

    assert restored.diagnostics[0].line == 12
    assert restored.sorry_locations[0].code == "sorry"


def test_environment_report_roundtrip() -> None:
    report = LeanEnvironmentReport(
        lean_available=True,
        lake_available=True,
        project_root_found=True,
        build_status="unknown",
        toolchain_version="leanprover/lean4:v4.15.0",
        optional_tools={"loogle": False, "leanexplore": True},
        blocks_promotion=False,
    )

    restored = LeanEnvironmentReport.model_validate_json(report.model_dump_json())

    assert restored.optional_tools["leanexplore"] is True
    assert restored.blocks_promotion is False


def test_validation_report_roundtrip_with_new_statuses() -> None:
    for status in [LeanValidationStatus.TIMEOUT, LeanValidationStatus.WORKSPACE_ERROR]:
        report = LeanValidationReport(
            status=status, retriable=status is LeanValidationStatus.TIMEOUT
        )
        restored = LeanValidationReport.model_validate_json(report.model_dump_json())
        assert restored.status is status


def test_evidence_bundle_roundtrip() -> None:
    environment = LeanEnvironmentReport(blocks_promotion=False)
    validation = LeanValidationReport(
        status=LeanValidationStatus.FULLY_PROVEN,
        blocks_promotion=False,
        completeness_ratio=1.0,
    )
    artifact = LeanRunArtifact(artifact_id="artifact-1", plan_ref="plan-1", exit_code=0)
    bundle = LeanEvidenceBundle(
        bundle_id="bundle-1",
        task_ref="task-1",
        environment_report=environment,
        blueprint=LeanBlueprint(items=[]),
        artifacts=[artifact],
        validation_report=validation,
        provenance=LeanProvenance(command=["lake", "env", "lean", "Proofs/Main.lean"]),
    )

    restored = LeanEvidenceBundle.model_validate_json(bundle.model_dump_json())

    assert restored.artifacts[0].artifact_id == "artifact-1"
    assert restored.provenance.command[0] == "lake"


def test_mock_backend_returns_structured_diagnostics() -> None:
    backend = MockLeanBackend(
        exit_code=1,
        stdout="stdout",
        stderr="stderr",
        diagnostics=[
            LeanDiagnostic(line=5, severity=LeanDiagnosticSeverity.ERROR, message="failed")
        ],
    )

    result = backend.run("Proofs/Main.lean")

    assert result.exit_code == 1
    assert result.stdout == "stdout"
    assert result.stderr == "stderr"
    assert result.diagnostics[0].file == "Proofs/Main.lean"
    assert result.diagnostics[0].line == 5


def test_validation_status_enum_values() -> None:
    values = {status.value for status in LeanValidationStatus}

    assert values == {
        "fully_proven",
        "partially_proven",
        "budget_exhausted",
        "compilation_failed",
        "statement_drift",
        "environment_failed",
        "timeout",
        "workspace_error",
    }
