from __future__ import annotations

from pathlib import Path

import pytest

from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.qcompute.contracts import (
    QComputeBackendSpec,
    QComputeBaselineResult,
    QComputeCircuitSpec,
    QComputeEvidenceBundle,
    QComputeExperimentSpec,
    QComputeNoiseSpec,
)
from metaharness_ext.qcompute.gateway import QComputeGatewayComponent
from metaharness_ext.qcompute.types import QComputeValidationStatus

BELL_STATE_OPENQASM = 'OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; h q[0]; cx q[0],q[1];'


def _build_spec(
    *,
    task_id: str = "gw-bell",
    platform: str = "qiskit_aer",
    qubit_count: int = 2,
    shots: int = 256,
    noise: QComputeNoiseSpec | None = None,
    error_mitigation: list[str] | None = None,
    openqasm: str = BELL_STATE_OPENQASM,
) -> QComputeExperimentSpec:
    return QComputeExperimentSpec(
        task_id=task_id,
        mode="simulate",
        backend=QComputeBackendSpec(
            platform=platform,
            simulator=True,
            qubit_count=qubit_count,
        ),
        circuit=QComputeCircuitSpec(
            ansatz="custom",
            num_qubits=qubit_count,
            openqasm=openqasm,
        ),
        noise=noise,
        shots=shots,
        error_mitigation=error_mitigation or [],
    )


# ---------------------------------------------------------------------------
# compile_experiment
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
async def test_gateway_compile_experiment(tmp_path: Path) -> None:
    """compile_experiment() runs probe + build_plan."""
    spec = _build_spec(task_id="gw-compile")
    gateway = QComputeGatewayComponent()
    await gateway.activate(ComponentRuntime(storage_path=tmp_path))

    env_report, plan = gateway.compile_experiment(spec)

    assert env_report.available
    assert plan.experiment_ref == spec.task_id
    assert plan.circuit_openqasm  # non-empty compiled circuit
    assert plan.target_backend.platform == "qiskit_aer"

    await gateway.deactivate()


# ---------------------------------------------------------------------------
# run_baseline -- Bell state on qiskit_aer
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
async def test_gateway_run_baseline_bell_state(tmp_path: Path) -> None:
    """run_baseline() orchestrates all 5 stages for a Bell state."""
    spec = _build_spec(task_id="gw-bell-aer", shots=512)
    gateway = QComputeGatewayComponent()
    await gateway.activate(ComponentRuntime(storage_path=tmp_path))

    bundle = gateway.run_baseline(spec)

    assert isinstance(bundle, QComputeEvidenceBundle)
    assert bundle.environment_report.available
    assert bundle.run_artifact.status == "completed"
    assert bundle.run_artifact.counts is not None
    assert sum(bundle.run_artifact.counts.values()) == 512

    # Bell state: only |00> and |11>
    for bitstring in bundle.run_artifact.counts:
        assert bitstring in {"00", "11"}

    assert bundle.validation_report.passed
    assert bundle.validation_report.promotion_ready

    await gateway.deactivate()


# ---------------------------------------------------------------------------
# run_baseline -- PennyLane backend
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
async def test_gateway_run_baseline_pennylane(tmp_path: Path) -> None:
    """run_baseline() works with pennylane_aer backend."""
    spec = _build_spec(
        task_id="gw-bell-pennylane",
        platform="pennylane_aer",
        shots=256,
    )
    gateway = QComputeGatewayComponent()
    await gateway.activate(ComponentRuntime(storage_path=tmp_path))

    bundle = gateway.run_baseline(spec)

    assert bundle.run_artifact.status == "completed"
    assert bundle.run_artifact.counts is not None
    assert sum(bundle.run_artifact.counts.values()) == 256
    assert bundle.validation_report.passed

    await gateway.deactivate()


# ---------------------------------------------------------------------------
# run_baseline -- failed environment
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
async def test_gateway_run_baseline_environment_unavailable(tmp_path: Path) -> None:
    """run_baseline() returns bundle even when environment fails."""
    # Use quafu platform which is unsupported in Phase 1
    spec = _build_spec(
        task_id="gw-env-fail",
        platform="quafu",
    )
    gateway = QComputeGatewayComponent()
    await gateway.activate(ComponentRuntime(storage_path=tmp_path))

    bundle = gateway.run_baseline(spec)

    assert isinstance(bundle, QComputeEvidenceBundle)
    assert not bundle.environment_report.available
    assert bundle.run_artifact.status == "failed"
    assert bundle.run_artifact.terminal_error_type == "environment_unavailable"
    assert bundle.validation_report.status == QComputeValidationStatus.EXECUTION_FAILED
    assert not bundle.validation_report.passed

    await gateway.deactivate()


# ---------------------------------------------------------------------------
# run_baseline_full -- includes policy and governance
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
async def test_gateway_run_baseline_full(tmp_path: Path) -> None:
    """run_baseline_full() includes policy evaluation and governance."""
    spec = _build_spec(task_id="gw-full", shots=512)
    gateway = QComputeGatewayComponent()
    await gateway.activate(ComponentRuntime(storage_path=tmp_path))

    result = gateway.run_baseline_full(spec)

    assert isinstance(result, QComputeBaselineResult)
    assert result.environment.available
    assert result.plan_id is not None
    assert result.artifact_id is not None
    assert result.bundle is not None
    assert result.bundle.run_artifact.status == "completed"

    # Policy should allow for a clean Bell state run
    assert result.policy is not None
    assert result.policy.passed
    assert result.policy.decision == "allow"

    # Core validation should be valid
    assert result.core_validation is not None
    assert result.core_validation.valid

    await gateway.deactivate()


# ---------------------------------------------------------------------------
# run_baseline_full with noise + ZNE mitigation
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
async def test_gateway_run_baseline_full_with_mitigation(tmp_path: Path) -> None:
    """Full pipeline with noise and ZNE mitigation."""
    spec = _build_spec(
        task_id="gw-mitigation",
        noise=QComputeNoiseSpec(
            model="depolarizing",
            depolarizing_prob=0.01,
        ),
        error_mitigation=["zne"],
        shots=256,
    )
    gateway = QComputeGatewayComponent()
    await gateway.activate(ComponentRuntime(storage_path=tmp_path))

    result = gateway.run_baseline_full(spec)

    assert result.bundle is not None
    assert result.bundle.run_artifact.status == "completed"
    assert result.bundle.run_artifact.counts is not None
    assert sum(result.bundle.run_artifact.counts.values()) == 256

    # ZNE mitigation metadata should be present
    mitigation = result.bundle.run_artifact.execution_policy.details.get("error_mitigation")
    assert mitigation is not None
    assert mitigation["zne"]["applied"] is True

    assert result.policy is not None
    assert result.policy.decision == "allow"
    assert result.core_validation is not None
    assert result.core_validation.valid

    await gateway.deactivate()


# ---------------------------------------------------------------------------
# issue_task backward compatibility
# ---------------------------------------------------------------------------


def test_gateway_issue_task_backward_compat() -> None:
    """issue_task() still returns the spec unchanged."""
    spec = _build_spec(task_id="gw-issue-task")
    gateway = QComputeGatewayComponent()

    result = gateway.issue_task(experiment=spec)

    assert result is spec
    assert result.task_id == "gw-issue-task"
