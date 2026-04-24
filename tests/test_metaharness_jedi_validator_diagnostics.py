from __future__ import annotations

from metaharness_ext.jedi.contracts import JediDiagnosticSummary, JediRunArtifact
from metaharness_ext.jedi.validator import JediValidatorComponent


class TestJediValidatorWithDiagnostics:
    def test_validator_enriches_report_with_diagnostics(self) -> None:
        artifact = JediRunArtifact(
            task_id="task-1",
            run_id="run-1",
            application_family="hofx",
            execution_mode="real_run",
            command=["/usr/bin/qgHofX4D.x", "config.yaml"],
            return_code=0,
            config_path="/tmp/config.yaml",
            stdout_path="/tmp/stdout.log",
            stderr_path="/tmp/stderr.log",
            working_directory="/tmp/run-1",
            output_files=["/tmp/run-1/analysis.out"],
            diagnostic_files=["/tmp/run-1/departures.json"],
            status="completed",
        )

        diagnostics = JediDiagnosticSummary(
            ioda_groups_found=["MetaData", "ObsValue", "HofX"],
            ioda_groups_missing=["ObsError", "PreQC"],
            files_scanned=["/tmp/run-1/departures.json"],
            messages=[],
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

        validator = JediValidatorComponent()
        report = validator.validate_run_with_diagnostics(artifact, diagnostics)

        assert report.passed is True
        assert report.status == "executed"
        assert report.policy_decision == "allow"
        assert report.blocking_reasons == []
        assert report.candidate_id == "run-1"
        assert report.graph_version_id is None
        assert report.session_id == "task-1"
        assert len(report.session_events) == 1
        assert report.session_events[0].candidate_id == "run-1"
        assert report.audit_refs == []
        assert report.summary_metrics["ioda_groups_found"] == 3
        assert report.summary_metrics["ioda_groups_missing"] == 2
        assert report.summary_metrics["minimizer_iterations"] == 4.0
        assert report.summary_metrics["outer_iterations"] == 2.0
        assert report.summary_metrics["inner_iterations"] == 5.0
        assert report.summary_metrics["initial_cost_function"] == 12.5
        assert report.summary_metrics["final_cost_function"] == 3.125
        assert report.summary_metrics["initial_gradient_norm"] == 8.0
        assert report.summary_metrics["final_gradient_norm"] == 0.5
        assert report.summary_metrics["gradient_norm_reduction"] == 0.0625
        assert report.summary_metrics["observer_output_detected"] == "True"
        assert "MetaData, ObsValue, HofX" in report.messages[-4]
        assert "ObsError, PreQC" in report.messages[-3]
        assert "Gradient norm reduction: 0.062500." == report.messages[-2]
        assert "Observer output evidence detected." == report.messages[-1]
        assert "/tmp/run-1/departures.json" in report.evidence_files

    def test_validator_enriches_failed_run_with_diagnostics(self) -> None:
        artifact = JediRunArtifact(
            task_id="task-1",
            run_id="run-1",
            application_family="hofx",
            execution_mode="real_run",
            command=["/usr/bin/qgHofX4D.x", "config.yaml"],
            return_code=1,
            config_path="/tmp/config.yaml",
            working_directory="/tmp/run-1",
            output_files=["/tmp/run-1/analysis.out"],
            diagnostic_files=["/tmp/run-1/departures.json"],
            status="completed",
        )

        diagnostics = JediDiagnosticSummary(
            ioda_groups_found=["MetaData", "ObsValue"],
            ioda_groups_missing=["ObsError", "PreQC"],
            files_scanned=["/tmp/run-1/departures.json"],
            messages=[],
        )

        validator = JediValidatorComponent()
        report = validator.validate_run_with_diagnostics(artifact, diagnostics)

        assert report.passed is False
        assert report.status == "runtime_failed"
        assert report.policy_decision == "defer"
        assert report.blocking_reasons == report.messages[:1]
        assert len(report.session_events) == 1
        assert report.session_events[0].event_type.value == "candidate_validated"
        assert report.summary_metrics["ioda_groups_found"] == 2
        assert report.summary_metrics["ioda_groups_missing"] == 2
        assert "MetaData, ObsValue" in report.messages[-2]

    def test_validator_deduplicates_evidence_files(self) -> None:
        artifact = JediRunArtifact(
            task_id="task-1",
            run_id="run-1",
            application_family="hofx",
            execution_mode="real_run",
            command=["/usr/bin/qgHofX4D.x", "config.yaml"],
            return_code=0,
            config_path="/tmp/config.yaml",
            working_directory="/tmp/run-1",
            output_files=["/tmp/run-1/analysis.out"],
            diagnostic_files=["/tmp/run-1/departures.json"],
            status="completed",
        )

        diagnostics = JediDiagnosticSummary(
            ioda_groups_found=["MetaData"],
            ioda_groups_missing=[],
            files_scanned=["/tmp/run-1/departures.json"],
            messages=[],
        )

        validator = JediValidatorComponent()
        report = validator.validate_run_with_diagnostics(artifact, diagnostics)

        assert report.evidence_files.count("/tmp/run-1/departures.json") == 1

    def test_validator_falls_back_without_diagnostics(self) -> None:
        artifact = JediRunArtifact(
            task_id="task-1",
            run_id="run-1",
            application_family="variational",
            execution_mode="real_run",
            command=["/usr/bin/qg4DVar.x", "config.yaml"],
            return_code=0,
            config_path="/tmp/config.yaml",
            working_directory="/tmp/run-1",
            output_files=["/tmp/run-1/analysis.out"],
            diagnostic_files=["/tmp/run-1/departures.json"],
            status="completed",
        )

        validator = JediValidatorComponent()
        report = validator.validate_run_with_diagnostics(artifact, None)

        assert report.passed is True
        assert report.status == "executed"
        assert report.candidate_id == "run-1"
        assert len(report.session_events) == 1
        assert "ioda_groups_found" not in report.summary_metrics

    def test_validator_preserves_base_evidence_when_diagnostics_add_scan_results(self) -> None:
        artifact = JediRunArtifact(
            task_id="task-1",
            run_id="run-1",
            application_family="forecast",
            execution_mode="real_run",
            command=["/usr/bin/qgForecast.x", "config.yaml"],
            return_code=0,
            config_path="/tmp/config.yaml",
            stdout_path="/tmp/stdout.log",
            working_directory="/tmp/run-1",
            output_files=["/tmp/run-1/forecast.out"],
            diagnostic_files=["/tmp/run-1/diag.nc"],
            reference_files=["/tmp/run-1/reference.nc"],
            status="completed",
        )
        diagnostics = JediDiagnosticSummary(
            ioda_groups_found=["MetaData"],
            ioda_groups_missing=[],
            files_scanned=["/tmp/run-1/diag.nc", "/tmp/run-1/reference.nc"],
            messages=[],
        )

        report = JediValidatorComponent().validate_run_with_diagnostics(artifact, diagnostics)

        assert report.passed is True
        assert report.status == "executed"
        assert report.evidence_files[0] == "/tmp/config.yaml"
        assert "/tmp/stdout.log" in report.evidence_files
        assert "/tmp/run-1/diag.nc" in report.evidence_files
        assert "/tmp/run-1/reference.nc" in report.evidence_files
        assert report.evidence_files.count("/tmp/run-1/diag.nc") == 1
