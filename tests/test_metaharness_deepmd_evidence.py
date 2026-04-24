from metaharness_ext.deepmd.contracts import (
    DeepMDDiagnosticSummary,
    DeepMDRunArtifact,
    DeepMDValidationReport,
)
from metaharness_ext.deepmd.evidence import build_evidence_bundle


def test_build_evidence_bundle_aggregates_run_and_validation() -> None:
    run = DeepMDRunArtifact(
        task_id="task-1",
        run_id="run-1",
        application_family="dpgen_run",
        execution_mode="dpgen_run",
        command=["dpgen", "run"],
        return_code=0,
        stdout_path="/tmp/stdout.log",
        stderr_path="/tmp/stderr.log",
        working_directory="/tmp/run",
        workspace_files=["/tmp/run/input.data"],
        checkpoint_files=["/tmp/run/checkpoint"],
        model_files=["/tmp/run/model.pb"],
        diagnostic_files=["/tmp/run/record.dpgen"],
        summary=DeepMDDiagnosticSummary(),
        status="completed",
        result_summary={"exit_code": 0},
    )
    run.summary.dpgen_collection = object.__new__(type("_Collection", (), {}))
    run.summary.dpgen_collection.iterations = [object()]
    validation = DeepMDValidationReport(
        task_id="task-1",
        run_id="run-1",
        passed=True,
        status="baseline_success",
        evidence_files=["/tmp/run/record.dpgen", "/tmp/run/model.pb"],
    )

    bundle = build_evidence_bundle(run, validation)

    assert bundle.task_id == "task-1"
    assert bundle.validation is validation
    assert "/tmp/run/input.data" in bundle.evidence_files
    assert "/tmp/run/checkpoint" in bundle.evidence_files
    assert "/tmp/run/model.pb" in bundle.evidence_files
    assert "/tmp/run/record.dpgen" in bundle.evidence_files
    assert bundle.warnings == []


def test_build_evidence_bundle_warns_for_missing_dpgen_evidence() -> None:
    run = DeepMDRunArtifact(
        task_id="task-2",
        run_id="run-2",
        application_family="dpgen_simplify",
        execution_mode="dpgen_simplify",
        command=["dpgen", "simplify"],
        return_code=0,
        stdout_path=None,
        stderr_path=None,
        working_directory="/tmp/run",
        summary=DeepMDDiagnosticSummary(),
        status="completed",
        result_summary={"exit_code": 0},
    )

    bundle = build_evidence_bundle(run)

    codes = {warning.code for warning in bundle.warnings}
    assert "stdout_missing" in codes
    assert "stderr_missing" in codes
    assert "dpgen_iteration_evidence_missing" in codes
