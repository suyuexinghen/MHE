from metaharness_ext.deepmd.contracts import (
    DeepMDDiagnosticSummary,
    DeepMDEnvironmentReport,
    DeepMDRunArtifact,
    DeepMDValidationReport,
    DPGenIterationCollection,
    DPGenIterationSummary,
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
        summary=DeepMDDiagnosticSummary(
            dpgen_collection=DPGenIterationCollection(
                iterations=[
                    DPGenIterationSummary(
                        iteration_id="iter.000001",
                        path="/tmp/run/iter.000001",
                    )
                ]
            )
        ),
        status="completed",
        result_summary={"exit_code": 0},
    )
    validation = DeepMDValidationReport(
        task_id="task-1",
        run_id="run-1",
        passed=True,
        status="baseline_success",
        evidence_files=["/tmp/run/record.dpgen", "/tmp/run/model.pb"],
    )
    environment = DeepMDEnvironmentReport(
        application_family="dpgen_run",
        execution_mode="dpgen_run",
        dp_available=True,
        dpgen_available=True,
        python_available=True,
        required_paths_present=True,
        evidence_refs=["deepmd://environment/task-1", "deepmd://binary/dpgen"],
        messages=["environment ready"],
    )

    bundle = build_evidence_bundle(run, validation, environment)

    assert bundle.task_id == "task-1"
    assert bundle.validation is validation
    assert "/tmp/run/input.data" in bundle.evidence_files
    assert "/tmp/run/checkpoint" in bundle.evidence_files
    assert "/tmp/run/model.pb" in bundle.evidence_files
    assert "/tmp/run/record.dpgen" in bundle.evidence_files
    assert bundle.warnings == []
    assert bundle.scored_evidence is validation.scored_evidence
    assert f"deepmd://validation/{run.task_id}/{run.run_id}" in bundle.provenance_refs
    assert set(validation.evidence_refs).issubset(set(bundle.provenance_refs))
    assert set(environment.evidence_refs).issubset(set(bundle.provenance_refs))
    assert bundle.provenance["execution_mode"] == "dpgen_run"
    assert bundle.metadata["environment"] == {
        "fallback_reason": None,
        "missing_prerequisites": [],
        "missing_required_paths": [],
        "machine_spec_valid": True,
        "remote_root_configured": True,
        "scheduler_command_configured": True,
        "messages": ["environment ready"],
    }


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


def test_build_evidence_bundle_warns_for_missing_environment_findings() -> None:
    run = DeepMDRunArtifact(
        task_id="task-3",
        run_id="run-3",
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
    environment = DeepMDEnvironmentReport(
        application_family="deepmd_train",
        execution_mode="train",
        dp_available=True,
        python_available=True,
        required_paths_present=False,
        missing_required_paths=["/tmp/missing-dataset"],
        missing_prerequisites=["python"],
        messages=["Missing dataset path: /tmp/missing-dataset"],
        fallback_reason="missing_python_runtime",
    )

    bundle = build_evidence_bundle(run, environment=environment)

    assert bundle.metadata["environment"] == {
        "fallback_reason": "missing_python_runtime",
        "missing_prerequisites": ["python"],
        "missing_required_paths": ["/tmp/missing-dataset"],
        "machine_spec_valid": True,
        "remote_root_configured": True,
        "scheduler_command_configured": True,
        "messages": ["Missing dataset path: /tmp/missing-dataset"],
    }
    warnings = [(warning.code, warning.evidence) for warning in bundle.warnings]
    assert (
        "environment_prerequisite_missing",
        {"run_id": "run-3", "prerequisite": "python"},
    ) in warnings
    assert (
        "environment_required_path_missing",
        {"run_id": "run-3", "path": "/tmp/missing-dataset"},
    ) in warnings
