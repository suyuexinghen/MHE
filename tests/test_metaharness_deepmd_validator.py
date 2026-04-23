from __future__ import annotations

import pytest

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
    assert report.summary_metrics["candidate_count"] == pytest.approx(0.0)
    assert report.summary_metrics["relabeling_detected"] == "true"
