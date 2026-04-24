from metaharness_ext.jedi.contracts import (
    JediDiagnosticSummary,
    JediRunArtifact,
    JediValidationReport,
)
from metaharness_ext.jedi.evidence import build_evidence_bundle
from metaharness_ext.jedi.policy import JediEvidencePolicy


def test_jedi_policy_rejects_environment_invalid_validation() -> None:
    run = JediRunArtifact(
        task_id="task-1",
        run_id="run-1",
        application_family="variational",
        execution_mode="validate_only",
        command=["/usr/bin/qg4DVar.x", "--validate-only", "config.yaml"],
        return_code=None,
        stdout_path="/tmp/stdout.log",
        stderr_path="/tmp/stderr.log",
        working_directory="/tmp/run",
        status="unavailable",
    )
    validation = JediValidationReport(
        task_id="task-1",
        run_id="run-1",
        passed=False,
        status="environment_invalid",
        blocking_reasons=["binary not found"],
        policy_decision="reject",
    )

    report = JediEvidencePolicy().evaluate(build_evidence_bundle(run, validation))

    assert report.decision == "reject"
    assert report.passed is False
    assert report.gates[0].reason == "Validation status is environment_invalid."


def test_jedi_policy_defers_incomplete_real_run_evidence() -> None:
    run = JediRunArtifact(
        task_id="task-2",
        run_id="run-2",
        application_family="hofx",
        execution_mode="real_run",
        command=["/usr/bin/qgHofX4D.x", "config.yaml"],
        return_code=0,
        stdout_path="/tmp/stdout.log",
        stderr_path="/tmp/stderr.log",
        working_directory="/tmp/run",
        status="completed",
    )
    validation = JediValidationReport(
        task_id="task-2",
        run_id="run-2",
        passed=True,
        status="executed",
        policy_decision="allow",
    )

    report = JediEvidencePolicy().evaluate(build_evidence_bundle(run, validation))

    assert report.decision == "defer"
    assert report.passed is False
    gate_names = {gate.gate for gate in report.gates}
    assert "primary_output_evidence" in gate_names
    assert "diagnostic_or_reference_evidence" in gate_names


def test_jedi_policy_allows_complete_executed_evidence_bundle() -> None:
    run = JediRunArtifact(
        task_id="task-3",
        run_id="run-3",
        application_family="variational",
        execution_mode="real_run",
        command=["/usr/bin/qg4DVar.x", "config.yaml"],
        return_code=0,
        config_path="/tmp/config.yaml",
        stdout_path="/tmp/stdout.log",
        stderr_path="/tmp/stderr.log",
        output_files=["/tmp/analysis.out"],
        diagnostic_files=["/tmp/departures.json"],
        working_directory="/tmp/run",
        status="completed",
    )
    validation = JediValidationReport(
        task_id="task-3",
        run_id="run-3",
        passed=True,
        status="executed",
        policy_decision="allow",
        provenance_refs=["prov://run-3"],
        checkpoint_refs=["ckpt://run-3"],
    )
    summary = JediDiagnosticSummary(files_scanned=["/tmp/departures.json"])

    report = JediEvidencePolicy().evaluate(build_evidence_bundle(run, validation, summary))

    assert report.decision == "allow"
    assert report.passed is True
    warning_codes = {warning.code for warning in report.warnings}
    assert "handoff_refs_present" in warning_codes
    assert report.gates[-1].gate == "evidence_ready"
