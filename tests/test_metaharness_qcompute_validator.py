from metaharness.core.models import ValidationIssueCategory
from metaharness_ext.qcompute.contracts import (
    QComputeBackendSpec,
    QComputeEnvironmentReport,
    QComputeExecutionParams,
    QComputeNoiseSpec,
    QComputeRunArtifact,
    QComputeRunPlan,
)
from metaharness_ext.qcompute.types import QComputeValidationStatus
from metaharness_ext.qcompute.validator import QComputeValidatorComponent


def _build_plan(**overrides) -> QComputeRunPlan:
    data = {
        "plan_id": "plan-1",
        "experiment_ref": "qcompute-exp-1",
        "circuit_openqasm": 'OPENQASM 2.0; include "qelib1.inc"; qreg q[1]; creg c[1]; h q[0]; measure q[0] -> c[0];',
        "target_backend": QComputeBackendSpec(platform="qiskit_aer", simulator=True, qubit_count=1),
        "compilation_strategy": "baseline",
        "compilation_metadata": {
            "operation_counts": {"h": 1, "measure": 1},
            "fidelity_threshold": 0.9,
        },
        "estimated_depth": 2,
        "estimated_swap_count": 0,
        "estimated_fidelity": 0.99,
        "execution_params": QComputeExecutionParams(shots=128),
    }
    data.update(overrides)
    return QComputeRunPlan(**data)


def _build_artifact(**overrides) -> QComputeRunArtifact:
    data = {
        "artifact_id": "artifact-1",
        "plan_ref": "plan-1",
        "backend_actual": "qiskit_aer",
        "status": "completed",
        "counts": {"0": 64, "1": 64},
        "probabilities": {"0": 0.5, "1": 0.5},
        "raw_output_path": "qcompute_runs/qcompute-exp-1/plan-1/result.json",
        "shots_requested": 128,
        "shots_completed": 128,
    }
    data.update(overrides)
    return QComputeRunArtifact(**data)


def _build_environment(**overrides) -> QComputeEnvironmentReport:
    data = {
        "task_id": "qcompute-exp-1",
        "backend": QComputeBackendSpec(platform="qiskit_aer", simulator=True, qubit_count=1),
        "available": True,
        "status": "online",
    }
    data.update(overrides)
    return QComputeEnvironmentReport(**data)


def test_qcompute_validator_accepts_complete_run() -> None:
    report = QComputeValidatorComponent().validate_run(
        _build_artifact(),
        _build_plan(),
        _build_environment(),
    )

    assert report.passed is True
    assert report.promotion_ready is True
    assert report.status is QComputeValidationStatus.VALIDATED
    assert report.metrics.fidelity == 0.99
    assert report.metrics.circuit_depth_executed == 2
    assert report.issues == []
    assert report.scored_evidence is not None
    assert report.scored_evidence.safety_score == 1.0


def test_qcompute_validator_blocks_unavailable_environment() -> None:
    report = QComputeValidatorComponent().validate_run(
        _build_artifact(),
        _build_plan(),
        _build_environment(
            available=False,
            status="dependency_missing",
            blocks_promotion=True,
            prerequisite_errors=["qiskit_aer missing"],
        ),
    )

    assert report.passed is False
    assert report.status is QComputeValidationStatus.ENVIRONMENT_INVALID
    assert report.issues[0].category is ValidationIssueCategory.READINESS
    assert report.issues[0].blocks_promotion is True


def test_qcompute_validator_detects_incomplete_result() -> None:
    report = QComputeValidatorComponent().validate_run(
        _build_artifact(counts={}, shots_completed=64),
        _build_plan(),
        _build_environment(),
    )

    assert report.status is QComputeValidationStatus.RESULT_INCOMPLETE
    assert report.promotion_ready is False
    assert report.issues[0].code == "qcompute_result_incomplete"


def test_qcompute_validator_defers_high_noise_impact() -> None:
    report = QComputeValidatorComponent().validate_run(
        _build_artifact(),
        _build_plan(
            noise=QComputeNoiseSpec(
                model="depolarizing",
                depolarizing_prob=0.1,
                readout_error=0.1,
                gate_error_map={"h": 0.6},
            ),
        ),
        _build_environment(),
    )

    assert report.status is QComputeValidationStatus.NOISE_CORRUPTED
    assert report.promotion_ready is False
    assert report.issues[0].blocks_promotion is False
    assert report.metrics.noise_impact_score is not None
    assert abs(report.metrics.noise_impact_score - 0.8) < 1e-12
