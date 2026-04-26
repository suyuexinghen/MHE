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
    assert report.evidence["run_id"] == "run-1"
    assert report.evidence["status"] == "environment_invalid"
    assert report.evidence["diagnostic_files_scanned"] == 0
    assert report.evidence["ioda_groups_found"] == []
    assert report.evidence["ioda_groups_missing"] == []
    assert report.evidence["observer_output_detected"] is False
    assert report.evidence["posterior_output_detected"] is False


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
    assert report.evidence["run_id"] == "run-2"
    assert report.evidence["status"] == "executed"
    assert report.evidence["diagnostic_files_scanned"] == 0
    assert report.evidence["ioda_groups_found"] == []
    assert report.evidence["ioda_groups_missing"] == []
    assert report.evidence["observer_output_detected"] is False
    assert report.evidence["posterior_output_detected"] is False


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
    summary = JediDiagnosticSummary(
        files_scanned=["/tmp/departures.json"],
        ioda_groups_found=["MetaData", "ObsValue", "HofX"],
        ioda_groups_missing=["ObsError"],
        minimizer_iterations=4,
        outer_iterations=2,
        inner_iterations=5,
        initial_cost_function=12.5,
        final_cost_function=3.125,
        initial_gradient_norm=8.0,
        final_gradient_norm=0.5,
        gradient_norm_reduction=0.0625,
        observer_output_detected=True,
    )

    report = JediEvidencePolicy().evaluate(build_evidence_bundle(run, validation, summary))

    assert report.decision == "allow"
    assert report.passed is True
    warning_codes = {warning.code for warning in report.warnings}
    assert "handoff_refs_present" in warning_codes
    diagnostics_gate = next(
        gate for gate in report.gates if gate.gate == "diagnostics_structured_signal"
    )
    assert diagnostics_gate.decision.value == "allow"
    assert diagnostics_gate.evidence["ioda_groups_found"] == ["MetaData", "ObsValue", "HofX"]
    assert diagnostics_gate.evidence["ioda_groups_missing"] == ["ObsError"]
    assert diagnostics_gate.evidence["minimizer_iterations"] == 4
    assert diagnostics_gate.evidence["outer_iterations"] == 2
    assert diagnostics_gate.evidence["inner_iterations"] == 5
    assert diagnostics_gate.evidence["initial_cost_function"] == 12.5
    assert diagnostics_gate.evidence["final_cost_function"] == 3.125
    assert diagnostics_gate.evidence["initial_gradient_norm"] == 8.0
    assert diagnostics_gate.evidence["final_gradient_norm"] == 0.5
    assert diagnostics_gate.evidence["gradient_norm_reduction"] == 0.0625
    assert diagnostics_gate.evidence["observer_output_detected"] is True
    assert report.evidence["diagnostic_files_scanned"] == 1
    assert report.evidence["ioda_groups_found"] == ["MetaData", "ObsValue", "HofX"]
    assert report.evidence["ioda_groups_missing"] == ["ObsError"]
    assert report.evidence["minimizer_iterations"] == 4
    assert report.evidence["outer_iterations"] == 2
    assert report.evidence["inner_iterations"] == 5
    assert report.evidence["initial_cost_function"] == 12.5
    assert report.evidence["final_cost_function"] == 3.125
    assert report.evidence["initial_gradient_norm"] == 8.0
    assert report.evidence["final_gradient_norm"] == 0.5
    assert report.evidence["gradient_norm_reduction"] == 0.0625
    assert report.evidence["observer_output_detected"] is True
    assert report.evidence["posterior_output_detected"] is False
    assert report.gates[-1].gate == "evidence_ready"


def test_jedi_policy_defers_when_real_run_diagnostics_summary_has_no_structured_signal() -> None:
    run = JediRunArtifact(
        task_id="task-4",
        run_id="run-4",
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
        task_id="task-4",
        run_id="run-4",
        passed=True,
        status="executed",
        policy_decision="allow",
    )
    summary = JediDiagnosticSummary()

    report = JediEvidencePolicy().evaluate(build_evidence_bundle(run, validation, summary))

    assert report.decision == "defer"
    assert report.passed is False
    diagnostics_gate = next(
        gate for gate in report.gates if gate.gate == "diagnostics_structured_signal"
    )
    assert diagnostics_gate.decision.value == "defer"
    assert "structured diagnostics evidence" in diagnostics_gate.reason
