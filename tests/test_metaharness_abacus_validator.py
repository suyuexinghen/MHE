from pathlib import Path

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
        output_root="/tmp/OUT.ABACUS",
        output_files=["/tmp/OUT.ABACUS", "/tmp/OUT.ABACUS/result.dat"],
        diagnostic_files=["/tmp/OUT.ABACUS/running_nscf.log"],
    )

    validator = AbacusValidatorComponent()
    report = validator.validate_run(artifact)

    assert report.passed is True
    assert report.status == "executed"


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
    assert any("NSCF log evidence" in item for item in report.missing_evidence)


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
    assert any("MD evidence" in item for item in report.missing_evidence)
