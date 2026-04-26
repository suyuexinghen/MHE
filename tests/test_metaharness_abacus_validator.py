from pathlib import Path

from metaharness.core.models import ValidationIssueCategory
from metaharness.provenance import ArtifactSnapshotStore
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.abacus.contracts import AbacusRunArtifact
from metaharness_ext.abacus.validator import AbacusValidatorComponent


def test_abacus_validator_accepts_nscf_evidence() -> None:
    artifact = AbacusRunArtifact(
        task_id="task-nscf",
        run_id="run-nscf",
        application_family="nscf",
        return_code=0,
        status="completed",
        working_directory="/tmp",
        prepared_inputs=["INPUT", "STRU", "KPT"],
        control_file_paths={
            "input_file": "INPUT",
            "structure_file": "STRU",
            "kpoints_file": "KPT",
        },
        output_root="/tmp/OUT.ABACUS",
        output_files=["/tmp/OUT.ABACUS", "/tmp/OUT.ABACUS/result.dat"],
        diagnostic_files=["/tmp/OUT.ABACUS/running_nscf.log"],
    )

    validator = AbacusValidatorComponent()
    report = validator.validate_run(artifact)

    assert report.passed is True
    assert report.status == "executed"
    assert report.blocks_promotion is False
    assert report.governance_state == "defer"
    assert artifact.control_file_paths.kpoints_file == "KPT"
    assert report.scored_evidence is not None
    assert report.scored_evidence.attributes["governance_state"] == "defer"
    assert f"abacus://run/{artifact.task_id}/{artifact.run_id}" in report.evidence_refs


def test_abacus_validator_rejects_nscf_without_log_evidence() -> None:
    artifact = AbacusRunArtifact(
        task_id="task-nscf",
        run_id="run-nscf",
        application_family="nscf",
        return_code=0,
        status="completed",
        working_directory="/tmp",
        prepared_inputs=["INPUT", "STRU", "KPT"],
        output_root="/tmp/OUT.ABACUS",
        output_files=["/tmp/OUT.ABACUS", "/tmp/OUT.ABACUS/result.dat"],
        diagnostic_files=[],
    )

    validator = AbacusValidatorComponent()
    report = validator.validate_run(artifact)

    assert report.passed is False
    assert report.status == "validation_failed"
    assert any("NSCF log evidence (running_nscf.log)" == item for item in report.missing_evidence)


def test_abacus_validator_rejects_nscf_with_only_scf_log_evidence() -> None:
    artifact = AbacusRunArtifact(
        task_id="task-nscf",
        run_id="run-nscf",
        application_family="nscf",
        return_code=0,
        status="completed",
        working_directory="/tmp",
        prepared_inputs=["INPUT", "STRU", "KPT"],
        output_root="/tmp/OUT.ABACUS",
        output_files=["/tmp/OUT.ABACUS", "/tmp/OUT.ABACUS/result.dat"],
        diagnostic_files=["/tmp/OUT.ABACUS/running_scf.log"],
    )

    validator = AbacusValidatorComponent()
    report = validator.validate_run(artifact)

    assert report.passed is False
    assert report.status == "validation_failed"
    assert report.blocks_promotion is True
    assert report.governance_state == "blocked"
    assert report.scored_evidence is not None
    assert report.scored_evidence.attributes["governance_state"] == "blocked"
    assert report.missing_evidence == ["NSCF log evidence (running_nscf.log)"]
    assert any(issue.blocks_promotion for issue in report.issues)
    assert any(
        issue.category == ValidationIssueCategory.PROMOTION_BLOCKER for issue in report.issues
    )


def test_abacus_validator_accepts_relax_structure_evidence(tmp_path: Path) -> None:
    output_root = tmp_path / "OUT.ABACUS"
    output_root.mkdir()
    structure = output_root / "STRU_ION_D"
    structure.write_text("structure")

    artifact = AbacusRunArtifact(
        task_id="task-relax",
        run_id="run-relax",
        application_family="relax",
        return_code=0,
        status="completed",
        working_directory=str(tmp_path),
        prepared_inputs=["INPUT", "STRU"],
        output_root=str(output_root),
        output_files=[str(output_root)],
        structure_files=[str(structure)],
    )

    validator = AbacusValidatorComponent()
    report = validator.validate_run(artifact)

    assert report.passed is True
    assert report.status == "executed"
    assert report.governance_state == "defer"
    assert report.scored_evidence is not None
    assert report.scored_evidence.attributes["governance_state"] == "defer"


def test_abacus_validator_rejects_relax_without_structure_evidence() -> None:
    artifact = AbacusRunArtifact(
        task_id="task-relax",
        run_id="run-relax",
        application_family="relax",
        return_code=0,
        status="completed",
        working_directory="/tmp",
        prepared_inputs=["INPUT", "STRU"],
        output_root="/tmp/OUT.ABACUS",
        output_files=["/tmp/OUT.ABACUS"],
        structure_files=[],
    )

    validator = AbacusValidatorComponent()
    report = validator.validate_run(artifact)

    assert report.passed is False
    assert report.status == "validation_failed"
    assert any("final structure evidence" in item for item in report.missing_evidence)


def test_abacus_validator_accepts_md_artifact_evidence(tmp_path: Path) -> None:
    output_root = tmp_path / "OUT.ABACUS"
    output_root.mkdir()
    md_dump = output_root / "MD_dump"
    md_dump.write_text("md")

    artifact = AbacusRunArtifact(
        task_id="task-md",
        run_id="run-md",
        application_family="md",
        return_code=0,
        status="completed",
        working_directory=str(tmp_path),
        prepared_inputs=["INPUT", "STRU"],
        output_root=str(output_root),
        output_files=[str(output_root), str(md_dump)],
        diagnostic_files=[],
    )

    validator = AbacusValidatorComponent()
    report = validator.validate_run(artifact)

    assert report.passed is True
    assert report.status == "executed"
    assert report.governance_state == "defer"
    assert report.scored_evidence is not None
    assert report.scored_evidence.attributes["governance_state"] == "defer"


def test_abacus_validator_accepts_md_restart_artifact_evidence(tmp_path: Path) -> None:
    output_root = tmp_path / "OUT.ABACUS"
    output_root.mkdir()
    restart = output_root / "Restart_md.0"
    restart.write_text("restart")

    artifact = AbacusRunArtifact(
        task_id="task-md",
        run_id="run-md",
        application_family="md",
        return_code=0,
        status="completed",
        working_directory=str(tmp_path),
        prepared_inputs=["INPUT", "STRU"],
        output_root=str(output_root),
        output_files=[str(output_root), str(restart)],
        diagnostic_files=[],
    )

    validator = AbacusValidatorComponent()
    report = validator.validate_run(artifact)

    assert report.passed is True
    assert report.status == "executed"


def test_abacus_validator_accepts_md_structure_artifact_evidence(tmp_path: Path) -> None:
    output_root = tmp_path / "OUT.ABACUS"
    output_root.mkdir()
    structure = output_root / "STRU_MD_0"
    structure.write_text("structure")

    artifact = AbacusRunArtifact(
        task_id="task-md",
        run_id="run-md",
        application_family="md",
        return_code=0,
        status="completed",
        working_directory=str(tmp_path),
        prepared_inputs=["INPUT", "STRU"],
        output_root=str(output_root),
        output_files=[str(output_root), str(structure)],
        diagnostic_files=[],
    )

    validator = AbacusValidatorComponent()
    report = validator.validate_run(artifact)

    assert report.passed is True
    assert report.status == "executed"


def test_abacus_validator_accepts_md_dp_evidence() -> None:
    artifact = AbacusRunArtifact(
        task_id="task-md-dp",
        run_id="run-md-dp",
        application_family="md",
        return_code=0,
        status="completed",
        working_directory="/tmp",
        prepared_inputs=["INPUT", "STRU"],
        output_root="/tmp/OUT.ABACUS",
        output_files=["/tmp/OUT.ABACUS", "/tmp/OUT.ABACUS/MD_dump"],
        diagnostic_files=[],
        result_summary={
            "esolver_type": "dp",
            "pot_file": "/tmp/model.pb",
            "environment_prerequisites": ["deeppmd_support"],
        },
    )

    validator = AbacusValidatorComponent()
    report = validator.validate_run(artifact)

    assert report.passed is True
    assert report.status == "executed"
    assert report.blocks_promotion is False
    assert report.governance_state == "defer"
    assert report.scored_evidence is not None
    assert report.scored_evidence.attributes["governance_state"] == "defer"
    assert report.summary_metrics["esolver_type"] == "dp"
    assert any(ref.startswith("abacus://run/task-md-dp/run-md-dp") for ref in report.evidence_refs)


def test_abacus_validator_blocks_md_dp_missing_prerequisite() -> None:
    artifact = AbacusRunArtifact(
        task_id="task-md-dp",
        run_id="run-md-dp",
        application_family="md",
        return_code=0,
        status="completed",
        working_directory="/tmp",
        prepared_inputs=["INPUT", "STRU"],
        output_root="/tmp/OUT.ABACUS",
        output_files=["/tmp/OUT.ABACUS", "/tmp/OUT.ABACUS/MD_dump"],
        diagnostic_files=[],
        result_summary={
            "esolver_type": "dp",
            "missing_prerequisites": ["deeppmd_support"],
        },
    )

    validator = AbacusValidatorComponent()
    report = validator.validate_run(artifact)

    assert report.passed is False
    assert report.status == "environment_invalid"
    assert report.blocks_promotion is True
    assert report.governance_state == "blocked"
    assert report.scored_evidence is not None
    assert report.scored_evidence.attributes["governance_state"] == "blocked"
    assert any("deeppmd_support" in item for item in report.missing_evidence)
    assert any(issue.blocks_promotion for issue in report.issues)
    assert any(
        issue.category == ValidationIssueCategory.PROMOTION_BLOCKER for issue in report.issues
    )


def test_abacus_validator_rejects_md_without_artifact_evidence() -> None:
    artifact = AbacusRunArtifact(
        task_id="task-md",
        run_id="run-md",
        application_family="md",
        return_code=0,
        status="completed",
        working_directory="/tmp",
        prepared_inputs=["INPUT", "STRU"],
        output_root="/tmp/OUT.ABACUS",
        output_files=["/tmp/OUT.ABACUS"],
        diagnostic_files=[],
    )

    validator = AbacusValidatorComponent()
    report = validator.validate_run(artifact)

    assert report.passed is False
    assert report.status == "validation_failed"
    assert report.blocks_promotion is True
    assert report.governance_state == "blocked"
    assert report.scored_evidence is not None
    assert report.scored_evidence.attributes["governance_state"] == "blocked"
    assert any("MD evidence" in item for item in report.missing_evidence)
    assert any("completed but evidence insufficient" in message for message in report.messages)
    assert any(issue.blocks_promotion for issue in report.issues)
    assert any(
        issue.category == ValidationIssueCategory.PROMOTION_BLOCKER for issue in report.issues
    )


def test_abacus_validator_rejects_md_with_only_non_characteristic_artifacts() -> None:
    artifact = AbacusRunArtifact(
        task_id="task-md-logs-only",
        run_id="run-md-logs-only",
        application_family="md",
        return_code=0,
        status="completed",
        working_directory="/tmp",
        prepared_inputs=["INPUT", "STRU"],
        output_root="/tmp/OUT.ABACUS",
        output_files=["/tmp/OUT.ABACUS", "/tmp/OUT.ABACUS/energy.dat"],
        diagnostic_files=["/tmp/OUT.ABACUS/running_md.log"],
        structure_files=[],
    )

    report = AbacusValidatorComponent().validate_run(artifact)

    assert report.passed is False
    assert report.status == "validation_failed"
    assert report.blocks_promotion is True
    assert report.missing_evidence == ["MD evidence (MD_dump, Restart_md, STRU_MD*)"]
    assert "/tmp/OUT.ABACUS/energy.dat" in report.evidence_files
    assert "/tmp/OUT.ABACUS/running_md.log" in report.evidence_files


def test_abacus_validator_keeps_prerequisite_rejection_evidence_linked() -> None:
    artifact = AbacusRunArtifact(
        task_id="task-md-dp",
        run_id="run-md-dp",
        application_family="md",
        return_code=0,
        status="completed",
        working_directory="/tmp",
        prepared_inputs=["INPUT", "STRU"],
        output_root="/tmp/OUT.ABACUS",
        output_files=["/tmp/OUT.ABACUS", "/tmp/OUT.ABACUS/MD_dump"],
        diagnostic_files=["/tmp/OUT.ABACUS/running_md.log"],
        result_summary={
            "esolver_type": "dp",
            "missing_prerequisites": ["deeppmd_support"],
        },
    )

    report = AbacusValidatorComponent().validate_run(artifact)

    assert report.passed is False
    assert report.status == "environment_invalid"
    assert "/tmp/OUT.ABACUS/MD_dump" in report.evidence_files
    assert "/tmp/OUT.ABACUS/running_md.log" in report.evidence_files
    assert report.missing_evidence == ["deeppmd_support"]


def test_abacus_validator_records_validation_snapshot(tmp_path: Path) -> None:
    output_root = tmp_path / "OUT.ABACUS"
    output_root.mkdir()
    (output_root / "running_nscf.log").write_text("ok")
    artifact = AbacusRunArtifact(
        task_id="task-persist",
        run_id="run-persist",
        application_family="nscf",
        return_code=0,
        status="completed",
        working_directory=str(tmp_path),
        prepared_inputs=["INPUT", "STRU", "KPT"],
        output_root=str(output_root),
        output_files=[str(output_root)],
        diagnostic_files=[str(output_root / "running_nscf.log")],
    )
    validator = AbacusValidatorComponent()
    import asyncio

    artifact_store = ArtifactSnapshotStore()
    asyncio.run(validator.activate(ComponentRuntime(artifact_store=artifact_store)))
    report = validator.validate_run(artifact)

    history = artifact_store.history(report.task_id)
    assert len(history) == 1
    assert history[0].artifact_kind == "validation_outcome"
    assert history[0].payload["task_id"] == report.task_id
