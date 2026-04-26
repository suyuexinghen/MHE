"""Tests for ResourceQuota integration and domain_payload bridge."""

from __future__ import annotations

from typing import Any

from metaharness_ext.qcompute.contracts import (
    QComputeBackendSpec,
    QComputeCircuitSpec,
    QComputeEnvironmentReport,
    QComputeEvidenceBundle,
    QComputeExecutionPolicy,
    QComputeExperimentSpec,
    QComputeNoiseSpec,
    QComputeRunArtifact,
    QComputeStudyTrial,
    QComputeValidationMetrics,
    QComputeValidationReport,
)
from metaharness_ext.qcompute.environment import QComputeEnvironmentProbeComponent
from metaharness_ext.qcompute.study import trial_to_domain_payload
from metaharness_ext.qcompute.types import QComputeValidationStatus


def _build_spec(**overrides: Any) -> QComputeExperimentSpec:
    data: dict[str, Any] = {
        "task_id": "qcompute-resource-1",
        "mode": "simulate",
        "backend": QComputeBackendSpec(platform="qiskit_aer", simulator=True, qubit_count=4),
        "circuit": QComputeCircuitSpec(
            ansatz="custom",
            num_qubits=2,
            openqasm=('OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; h q[0]; cx q[0],q[1];'),
        ),
        "noise": QComputeNoiseSpec(model="none"),
    }
    data.update(overrides)
    return QComputeExperimentSpec(**data)


def _build_trial(
    trial_id: str = "trial-001",
    parameters: dict[str, Any] | None = None,
    fidelity: float | None = 0.95,
    energy_error: float | None = 0.01,
    circuit_depth: int | None = 12,
    backend_actual: str = "qiskit_aer_simulator",
    status: QComputeValidationStatus = QComputeValidationStatus.VALIDATED,
    trajectory_score: float | None = 0.95,
) -> QComputeStudyTrial:
    """Build a minimal QComputeStudyTrial for testing."""
    spec = _build_spec()
    env_report = QComputeEnvironmentReport(
        task_id=spec.task_id,
        backend=spec.backend,
        available=True,
        status="online",
    )
    artifact = QComputeRunArtifact(
        artifact_id="art-001",
        plan_ref="plan-001",
        backend_actual=backend_actual,
        status="completed",
    )
    validation = QComputeValidationReport(
        task_id=spec.task_id,
        plan_ref="plan-001",
        artifact_ref="art-001",
        passed=True,
        status=status,
        metrics=QComputeValidationMetrics(
            fidelity=fidelity,
            energy_error=energy_error,
            circuit_depth_executed=circuit_depth,
        ),
    )
    bundle = QComputeEvidenceBundle(
        bundle_id="bundle-001",
        experiment_ref=spec.task_id,
        environment_report=env_report,
        run_artifact=artifact,
        validation_report=validation,
    )
    return QComputeStudyTrial(
        trial_id=trial_id,
        parameter_snapshot=parameters or {"shots": 1024, "depth": 3},
        evidence_bundle=bundle,
        trajectory_score=trajectory_score,
    )


# ---------------------------------------------------------------------------
# Part 1: ResourceQuota in environment report
# ---------------------------------------------------------------------------


def test_environment_report_includes_quota_when_configured() -> None:
    """probe() builds ResourceQuota when daily_quota is set."""
    policy = QComputeExecutionPolicy(daily_quota=100)
    spec = _build_spec(execution_policy=policy)

    report = QComputeEnvironmentProbeComponent().probe(spec)

    assert report.quota_snapshot is not None
    assert report.quota_snapshot.resource_type == "api_calls"
    assert report.quota_snapshot.limit == 100
    assert report.quota_snapshot.provider == "qiskit_aer"
    assert report.quota_snapshot.metadata.get("chip_id") is None


def test_environment_report_includes_quota_with_chip_id() -> None:
    """quota_snapshot metadata includes chip_id when configured."""
    policy = QComputeExecutionPolicy(daily_quota=50)
    backend = QComputeBackendSpec(
        platform="quafu", simulator=False, qubit_count=6, chip_id="Baihua"
    )
    spec = _build_spec(
        backend=backend,
        execution_policy=policy,
        circuit=QComputeCircuitSpec(
            ansatz="custom",
            num_qubits=2,
            openqasm=('OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; h q[0]; cx q[0],q[1];'),
        ),
    )

    report = QComputeEnvironmentProbeComponent().probe(spec)

    # Even if the backend is unavailable (quafu without SDK), the quota is
    # still built before the availability check returns.
    assert report.quota_snapshot is not None
    assert report.quota_snapshot.metadata["chip_id"] == "Baihua"


def test_environment_report_no_quota_when_not_configured() -> None:
    """probe() sets quota_snapshot=None when daily_quota is not set."""
    spec = _build_spec()  # default execution_policy has daily_quota=None

    report = QComputeEnvironmentProbeComponent().probe(spec)

    assert report.quota_snapshot is None


# ---------------------------------------------------------------------------
# Part 2: domain_payload bridge
# ---------------------------------------------------------------------------


def test_trial_to_domain_payload() -> None:
    """trial_to_domain_payload() converts trial to dict for MutationProposal."""
    trial = _build_trial()

    payload = trial_to_domain_payload(trial)

    assert isinstance(payload, dict)
    required_keys = {
        "trial_id",
        "parameters",
        "trajectory_score",
        "validation_status",
        "fidelity",
        "energy_error",
        "circuit_depth",
        "backend",
    }
    assert set(payload.keys()) == required_keys
    assert payload["trial_id"] == "trial-001"
    assert payload["validation_status"] == "validated"
    assert payload["fidelity"] == 0.95
    assert payload["energy_error"] == 0.01
    assert payload["circuit_depth"] == 12
    assert payload["backend"] == "qiskit_aer_simulator"


def test_trial_to_domain_payload_includes_parameters() -> None:
    """domain_payload preserves original parameter snapshot."""
    params = {"shots": 2048, "depth": 5, "entanglement": "full"}
    trial = _build_trial(parameters=params)

    payload = trial_to_domain_payload(trial)

    assert payload["parameters"] == params
    assert payload["parameters"]["shots"] == 2048
    assert payload["parameters"]["depth"] == 5


def test_trial_to_domain_payload_with_none_scores() -> None:
    """domain_payload handles None trajectory_score and metrics gracefully."""
    trial = _build_trial(
        trajectory_score=None,
        fidelity=None,
        energy_error=None,
        circuit_depth=None,
    )

    payload = trial_to_domain_payload(trial)

    assert payload["trajectory_score"] is None
    assert payload["fidelity"] is None
    assert payload["energy_error"] is None
    assert payload["circuit_depth"] is None
