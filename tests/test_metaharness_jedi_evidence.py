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
    summary = JediDiagnosticSummary(
        files_scanned=["/tmp/departures.json", "/tmp/extra.nc"],
        ioda_groups_missing=["ObsError", "PreQC"],
        minimizer_iterations=4,
        outer_iterations=2,
        inner_iterations=5,
        initial_cost_function=12.5,
        final_cost_function=3.125,
        initial_gradient_norm=8.0,
        final_gradient_norm=0.5,
        gradient_norm_reduction=0.0625,
    )

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
    assert bundle.candidate_id == "run-1"
    assert bundle.graph_version_id is None
    assert bundle.session_id == "task-1"
    assert bundle.session_events == []
    assert bundle.audit_refs == []
    assert bundle.metadata["policy_decision"] == "allow"
    assert bundle.metadata["diagnostics_present"] is True
    assert bundle.metadata["diagnostic_files_scanned"] == 2
    assert bundle.metadata["ioda_groups_found"] == []
    assert bundle.metadata["ioda_groups_missing"] == ["ObsError", "PreQC"]
    assert bundle.metadata["minimizer_iterations"] == 4
    assert bundle.metadata["outer_iterations"] == 2
    assert bundle.metadata["inner_iterations"] == 5
    assert bundle.metadata["initial_cost_function"] == 12.5
    assert bundle.metadata["final_cost_function"] == 3.125
    assert bundle.metadata["initial_gradient_norm"] == 8.0
    assert bundle.metadata["final_gradient_norm"] == 0.5
    assert bundle.metadata["gradient_norm_reduction"] == 0.0625
    assert bundle.metadata["observer_output_detected"] is False
    assert bundle.metadata["posterior_output_detected"] is False


def test_build_evidence_bundle_preserves_validation_prerequisite_and_checkpoint_handoff() -> None:
    run = JediRunArtifact(
        task_id="task-handoff",
        run_id="run-handoff",
        application_family="variational",
        execution_mode="validate_only",
        command=["/usr/bin/qg4DVar.x", "--validate-only", "config.yaml"],
        return_code=0,
        stdout_path="/tmp/stdout.log",
        stderr_path="/tmp/stderr.log",
        working_directory="/tmp/run",
        status="completed",
    )
    validation = JediValidationReport(
        task_id="task-handoff",
        run_id="run-handoff",
        passed=True,
        status="validated",
        policy_decision="allow",
        prerequisite_evidence={"workspace testinput": ["/tmp/testinput"]},
        checkpoint_refs=["checkpoint://jedi/prerequisite/workspace-testinput"],
    )

    bundle = build_evidence_bundle(run, validation)

    assert bundle.audit_refs == []
    assert bundle.validation is not None
    assert bundle.validation.prerequisite_evidence == {"workspace testinput": ["/tmp/testinput"]}
    assert bundle.validation.checkpoint_refs == [
        "checkpoint://jedi/prerequisite/workspace-testinput"
    ]


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
