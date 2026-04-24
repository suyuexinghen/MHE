import pytest

from metaharness_ext.deepmd.contracts import (
    DeepMDDiagnosticSummary,
    DeepMDRunArtifact,
    DeepMDValidationReport,
    DPGenIterationCollection,
    DPGenIterationSummary,
)
from metaharness_ext.deepmd.evidence import build_evidence_bundle
from metaharness_ext.deepmd.policy import DeepMDEvidencePolicy


def test_deepmd_policy_rejects_failed_validation() -> None:
    run = DeepMDRunArtifact(
        task_id="task-1",
        run_id="run-1",
        application_family="deepmd_train",
        execution_mode="train",
        command=["dp", "train"],
        return_code=1,
        stdout_path="/tmp/stdout.log",
        stderr_path="/tmp/stderr.log",
        working_directory="/tmp/run",
        summary=DeepMDDiagnosticSummary(),
        status="failed",
        result_summary={"exit_code": 1},
    )
    validation = DeepMDValidationReport(
        task_id="task-1",
        run_id="run-1",
        passed=False,
        status="runtime_failed",
        evidence_files=[],
    )

    report = DeepMDEvidencePolicy().evaluate(build_evidence_bundle(run, validation))

    assert report.decision == "reject"
    assert report.passed is False
    assert report.gates[0].reason == "Validation status is runtime_failed."


@pytest.mark.parametrize("status", ["remote_invalid", "scheduler_invalid", "machine_invalid"])
def test_deepmd_policy_rejects_unavailable_artifact_validation_statuses(status: str) -> None:
    run = DeepMDRunArtifact(
        task_id="task-unavailable",
        run_id="run-unavailable",
        application_family="deepmd_train",
        execution_mode="train",
        command=["dp", "train"],
        return_code=0,
        stdout_path="/tmp/stdout.log",
        stderr_path="/tmp/stderr.log",
        working_directory="/tmp/run",
        summary=DeepMDDiagnosticSummary(),
        status="completed",
        result_summary={"exit_code": 0},
    )
    validation = DeepMDValidationReport(
        task_id="task-unavailable",
        run_id="run-unavailable",
        passed=False,
        status=status,
        evidence_files=[],
    )

    report = DeepMDEvidencePolicy().evaluate(build_evidence_bundle(run, validation))

    assert report.decision == "reject"
    assert report.passed is False
    assert report.gates[0].gate == "run_status"
    assert report.gates[0].reason == f"Validation status is {status}."
    assert report.evidence["status"] == status


def test_deepmd_policy_defers_incomplete_dpgen_evidence() -> None:
    run = DeepMDRunArtifact(
        task_id="task-2",
        run_id="run-2",
        application_family="dpgen_run",
        execution_mode="dpgen_run",
        command=["dpgen", "run"],
        return_code=0,
        stdout_path="/tmp/stdout.log",
        stderr_path="/tmp/stderr.log",
        working_directory="/tmp/run",
        summary=DeepMDDiagnosticSummary(),
        status="completed",
        result_summary={"exit_code": 0},
    )
    validation = DeepMDValidationReport(
        task_id="task-2",
        run_id="run-2",
        passed=True,
        status="baseline_success",
        evidence_files=[],
    )

    report = DeepMDEvidencePolicy().evaluate(build_evidence_bundle(run, validation))

    assert report.decision == "defer"
    assert report.passed is False
    assert any(gate.gate == "dpgen_iteration_evidence" for gate in report.gates)


def test_deepmd_policy_allows_complete_converged_simplify() -> None:
    run = DeepMDRunArtifact(
        task_id="task-3",
        run_id="run-3",
        application_family="dpgen_simplify",
        execution_mode="dpgen_simplify",
        command=["dpgen", "simplify"],
        return_code=0,
        stdout_path="/tmp/stdout.log",
        stderr_path="/tmp/stderr.log",
        working_directory="/tmp/run",
        summary=DeepMDDiagnosticSummary(
            dpgen_collection=DPGenIterationCollection(
                record_path="/tmp/run/record.dpgen",
                iterations=[
                    DPGenIterationSummary(
                        iteration_id="iter.000000",
                        path="/tmp/run/iter.000000",
                        train_path="/tmp/run/iter.000000/00.train",
                        model_devi_path="/tmp/run/iter.000000/01.model_devi",
                        fp_path="/tmp/run/iter.000000/02.fp",
                    )
                ],
                messages=["DP-GEN workflow appears converged."],
            )
        ),
        status="completed",
        result_summary={"exit_code": 0},
    )
    validation = DeepMDValidationReport(
        task_id="task-3",
        run_id="run-3",
        passed=True,
        status="converged",
        summary_metrics={"relabeling_detected": "true"},
        evidence_files=["/tmp/run/record.dpgen"],
    )

    report = DeepMDEvidencePolicy().evaluate(build_evidence_bundle(run, validation))

    assert report.decision == "allow"
    assert report.passed is True
    warning_codes = {warning.code for warning in report.warnings}
    assert "relabeling_detected" in warning_codes
    assert report.gates[-1].gate == "evidence_ready"


def test_deepmd_policy_defers_for_environment_findings() -> None:
    run = DeepMDRunArtifact(
        task_id="task-env",
        run_id="run-env",
        application_family="deepmd_train",
        execution_mode="train",
        command=["dp", "train"],
        return_code=0,
        stdout_path="/tmp/stdout.log",
        stderr_path="/tmp/stderr.log",
        working_directory="/tmp/run",
        summary=DeepMDDiagnosticSummary(),
        status="completed",
        result_summary={"exit_code": 0},
    )
    validation = DeepMDValidationReport(
        task_id="task-env",
        run_id="run-env",
        passed=True,
        status="trained",
        evidence_files=[],
    )
    bundle = build_evidence_bundle(run, validation)
    bundle.metadata["environment"] = {
        "fallback_reason": None,
        "missing_prerequisites": ["python"],
        "missing_required_paths": ["/tmp/missing-dataset"],
        "machine_spec_valid": True,
        "remote_root_configured": True,
        "scheduler_command_configured": True,
        "messages": ["environment findings present"],
    }

    report = DeepMDEvidencePolicy().evaluate(bundle)

    assert report.decision == "defer"
    assert report.passed is False
    assert report.gates[0].gate == "environment_prerequisites"
    assert report.gates[0].reason == "Environment findings report missing prerequisites or required paths."


def test_deepmd_policy_keeps_run_status_rejection_when_environment_findings_exist() -> None:
    run = DeepMDRunArtifact(
        task_id="task-env-reject",
        run_id="run-env-reject",
        application_family="deepmd_train",
        execution_mode="train",
        command=["dp", "train"],
        return_code=1,
        stdout_path="/tmp/stdout.log",
        stderr_path="/tmp/stderr.log",
        working_directory="/tmp/run",
        summary=DeepMDDiagnosticSummary(),
        status="failed",
        result_summary={"exit_code": 1},
    )
    validation = DeepMDValidationReport(
        task_id="task-env-reject",
        run_id="run-env-reject",
        passed=False,
        status="environment_invalid",
        evidence_files=[],
    )
    bundle = build_evidence_bundle(run, validation)
    bundle.metadata["environment"] = {
        "fallback_reason": "binary_not_found",
        "missing_prerequisites": ["dp"],
        "missing_required_paths": ["/tmp/missing-dataset"],
        "machine_spec_valid": False,
        "remote_root_configured": True,
        "scheduler_command_configured": True,
        "messages": ["binary missing"],
    }

    report = DeepMDEvidencePolicy().evaluate(bundle)

    assert report.decision == "reject"
    assert report.passed is False
    assert [gate.gate for gate in report.gates] == ["environment_prerequisites", "run_status"]
    assert report.gates[1].reason == "Validation status is environment_invalid."
