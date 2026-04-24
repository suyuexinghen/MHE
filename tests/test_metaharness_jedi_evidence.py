from metaharness_ext.jedi.contracts import (
    JediDiagnosticSummary,
    JediRunArtifact,
    JediValidationReport,
)
from metaharness_ext.jedi.evidence import build_evidence_bundle


def test_build_evidence_bundle_aggregates_run_validation_and_summary() -> None:
    run = JediRunArtifact(
        task_id="task-1",
        run_id="run-1",
        application_family="variational",
        execution_mode="real_run",
        command=["/usr/bin/qg4DVar.x", "config.yaml"],
        return_code=0,
        config_path="/tmp/config.yaml",
        stdout_path="/tmp/stdout.log",
        stderr_path="/tmp/stderr.log",
        prepared_inputs=["/tmp/background.nc"],
        output_files=["/tmp/analysis.out"],
        diagnostic_files=["/tmp/departures.json"],
        reference_files=["/tmp/reference.json"],
        working_directory="/tmp/run",
        status="completed",
    )
    validation = JediValidationReport(
        task_id="task-1",
        run_id="run-1",
        passed=True,
        status="executed",
        evidence_files=["/tmp/departures.json", "/tmp/reference.json"],
        policy_decision="allow",
    )
    summary = JediDiagnosticSummary(files_scanned=["/tmp/departures.json", "/tmp/extra.nc"])

    bundle = build_evidence_bundle(run, validation, summary)

    assert bundle.task_id == "task-1"
    assert bundle.validation is validation
    assert bundle.summary is summary
    assert "/tmp/config.yaml" in bundle.evidence_files
    assert "/tmp/background.nc" in bundle.evidence_files
    assert "/tmp/analysis.out" in bundle.evidence_files
    assert "/tmp/extra.nc" in bundle.evidence_files
    assert bundle.evidence_files.count("/tmp/departures.json") == 1
    assert bundle.warnings == []
    assert bundle.metadata["policy_decision"] == "allow"


def test_build_evidence_bundle_warns_for_incomplete_real_run_evidence() -> None:
    run = JediRunArtifact(
        task_id="task-2",
        run_id="run-2",
        application_family="hofx",
        execution_mode="real_run",
        command=["/usr/bin/qgHofX4D.x", "config.yaml"],
        return_code=0,
        stdout_path=None,
        stderr_path=None,
        working_directory="/tmp/run",
        status="completed",
    )

    bundle = build_evidence_bundle(run)

    codes = {warning.code for warning in bundle.warnings}
    assert "stdout_missing" in codes
    assert "stderr_missing" in codes
    assert "primary_output_missing" in codes
    assert "runtime_evidence_incomplete" in codes
