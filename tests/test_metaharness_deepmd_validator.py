from __future__ import annotations

import pytest

from metaharness.core.models import ValidationIssueCategory
from metaharness_ext.deepmd.contracts import (
    DeepMDDiagnosticSummary,
    DeepMDRunArtifact,
    DPGenIterationCollection,
    DPGenIterationSummary,
)
from metaharness_ext.deepmd.validator import DeepMDValidatorComponent


def test_deepmd_validator_marks_dpgen_simplify_converged() -> None:
    artifact = DeepMDRunArtifact(
        task_id="dpgen-simplify-task",
        run_id="run-1",
        application_family="dpgen_simplify",
        execution_mode="dpgen_simplify",
        command=["dpgen", "simplify", "param.json", "machine.json"],
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
                        candidate_count=0,
                        accurate_count=2,
                        failed_count=0,
                    )
                ],
                candidate_count=0,
                accurate_count=2,
                failed_count=0,
                messages=[
                    "Detected relabeling clues in DP-GEN workspace.",
                    "DP-GEN workflow appears converged.",
                ],
            )
        ),
        status="completed",
        result_summary={"exit_code": 0},
    )

    report = DeepMDValidatorComponent().validate_run(artifact)

    assert report.passed is True
    assert report.status == "converged"
    assert report.blocks_promotion is False
    assert report.governance_state == "ready"
    assert report.summary_metrics["candidate_count"] == pytest.approx(0.0)
    assert report.summary_metrics["relabeling_detected"] == "true"
    assert report.scored_evidence is not None
    assert report.scored_evidence.score == pytest.approx(1.0)
    assert report.scored_evidence.convergence is not None
    assert report.scored_evidence.convergence.converged is True
    assert any(ref.startswith("deepmd://run/") for ref in report.evidence_refs)


def test_deepmd_validator_marks_runtime_failure_as_blocking() -> None:
    artifact = DeepMDRunArtifact(
        task_id="deepmd-train-task",
        run_id="run-failed",
        application_family="deepmd_train",
        execution_mode="train",
        command=["dp", "train", "input.json"],
        return_code=2,
        stdout_path="/tmp/train.stdout",
        stderr_path="/tmp/train.stderr",
        working_directory="/tmp/deepmd-run",
        status="failed",
        result_summary={"exit_code": 2},
    )

    report = DeepMDValidatorComponent().validate_run(artifact)

    assert report.passed is False
    assert report.status == "runtime_failed"
    assert report.blocks_promotion is True
    assert report.governance_state == "blocked"
    assert report.issues
    assert report.issues[0].category == ValidationIssueCategory.READINESS
    assert report.issues[0].blocks_promotion is True
    assert report.scored_evidence is not None
    assert report.scored_evidence.score == pytest.approx(0.0)
    assert report.scored_evidence.convergence is not None
    assert report.scored_evidence.convergence.converged is False


def test_deepmd_validator_maps_missing_remote_root_to_remote_invalid() -> None:
    artifact = DeepMDRunArtifact(
        task_id="dpgen-run-task",
        run_id="run-remote-invalid",
        application_family="dpgen_run",
        execution_mode="dpgen_run",
        command=["dpgen", "run", "param.json", "machine.json"],
        stdout_path="/tmp/stdout.log",
        stderr_path="/tmp/stderr.log",
        working_directory="/tmp/run",
        status="unavailable",
        result_summary={"fallback_reason": "missing_remote_root", "exit_code": None},
    )

    report = DeepMDValidatorComponent().validate_run(artifact)

    assert report.passed is False
    assert report.status == "remote_invalid"
    assert report.blocks_promotion is True


def test_deepmd_validator_maps_missing_scheduler_command_to_scheduler_invalid() -> None:
    artifact = DeepMDRunArtifact(
        task_id="dpgen-run-task",
        run_id="run-scheduler-invalid",
        application_family="dpgen_run",
        execution_mode="dpgen_run",
        command=["dpgen", "run", "param.json", "machine.json"],
        stdout_path="/tmp/stdout.log",
        stderr_path="/tmp/stderr.log",
        working_directory="/tmp/run",
        status="unavailable",
        result_summary={"fallback_reason": "missing_scheduler_command", "exit_code": None},
    )

    report = DeepMDValidatorComponent().validate_run(artifact)

    assert report.passed is False
    assert report.status == "scheduler_invalid"
    assert report.blocks_promotion is True


def test_deepmd_validator_maps_missing_machine_root_to_machine_invalid() -> None:
    artifact = DeepMDRunArtifact(
        task_id="dpgen-run-task",
        run_id="run-machine-invalid",
        application_family="dpgen_run",
        execution_mode="dpgen_run",
        command=["dpgen", "run", "param.json", "machine.json"],
        stdout_path="/tmp/stdout.log",
        stderr_path="/tmp/stderr.log",
        working_directory="/tmp/run",
        status="unavailable",
        result_summary={"fallback_reason": "missing_machine_root", "exit_code": None},
    )

    report = DeepMDValidatorComponent().validate_run(artifact)

    assert report.passed is False
    assert report.status == "machine_invalid"
    assert report.blocks_promotion is True
