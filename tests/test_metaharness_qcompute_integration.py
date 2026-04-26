from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.qcompute.config_compiler import QComputeConfigCompilerComponent
from metaharness_ext.qcompute.contracts import (
    QComputeBackendSpec,
    QComputeCircuitSpec,
    QComputeEnvironmentReport,
    QComputeExperimentSpec,
    QComputeNoiseSpec,
)
from metaharness_ext.qcompute.environment import QComputeEnvironmentProbeComponent
from metaharness_ext.qcompute.evidence import build_evidence_bundle
from metaharness_ext.qcompute.executor import QComputeExecutorComponent
from metaharness_ext.qcompute.governance import QComputeGovernanceAdapter
from metaharness_ext.qcompute.policy import QComputeEvidencePolicy
from metaharness_ext.qcompute.validator import QComputeValidatorComponent

BELL_STATE_OPENQASM = 'OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; h q[0]; cx q[0],q[1];'


def _build_spec(
    *,
    task_id: str = "integration-bell",
    platform: str = "qiskit_aer",
    qubit_count: int = 2,
    shots: int = 1024,
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
# 1. Bell-state full pipeline (qiskit_aer)
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
async def test_qcompute_bell_state_full_pipeline(tmp_path: Path) -> None:
    spec = _build_spec()

    # 1. Probe environment
    environment = QComputeEnvironmentProbeComponent().probe(spec)
    assert environment.available

    # 2. Compile
    compiler = QComputeConfigCompilerComponent()
    plan = compiler.build_plan(spec, environment)

    # 3. Execute
    executor = QComputeExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))
    artifact = executor.execute_plan(plan, environment)

    assert artifact.status == "completed"
    assert artifact.counts is not None
    assert sum(artifact.counts.values()) == spec.shots

    # Only |00> and |11> should appear for an ideal Bell state
    for bitstring in artifact.counts:
        assert bitstring in {"00", "11"}

    # 4. Validate
    validator = QComputeValidatorComponent()
    validation = validator.validate_run(artifact, plan, environment)
    assert validation.passed
    assert validation.promotion_ready

    # 5. Evidence + policy + governance
    bundle = build_evidence_bundle(artifact, validation, environment)

    policy = QComputeEvidencePolicy()
    policy_report = policy.evaluate(bundle)
    assert policy_report.decision == "allow"

    governance = QComputeGovernanceAdapter()
    events = governance.build_session_events(bundle, policy_report)
    assert len(events) >= 2

    # Verify raw output persisted to disk
    assert artifact.raw_output_path is not None
    raw = json.loads(Path(artifact.raw_output_path).read_text())
    assert raw["shots_completed"] == spec.shots


# ---------------------------------------------------------------------------
# 2. Bell-state full pipeline (pennylane_aer)
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
async def test_qcompute_bell_state_pennylane_pipeline(tmp_path: Path) -> None:
    spec = _build_spec(
        task_id="integration-bell-pennylane",
        platform="pennylane_aer",
    )

    # 1. Probe
    environment = QComputeEnvironmentProbeComponent().probe(spec)
    assert environment.available

    # 2. Compile
    compiler = QComputeConfigCompilerComponent()
    plan = compiler.build_plan(spec, environment)

    # 3. Execute
    executor = QComputeExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))
    artifact = executor.execute_plan(plan, environment)

    assert artifact.status == "completed"
    assert artifact.counts is not None
    assert sum(artifact.counts.values()) == spec.shots

    # Bell state: only |00> and |11> outcomes
    for bitstring in artifact.counts:
        assert bitstring in {"00", "11"}

    # 4. Validate
    validator = QComputeValidatorComponent()
    validation = validator.validate_run(artifact, plan, environment)
    assert validation.passed
    assert validation.promotion_ready

    # 5. Evidence + policy + governance
    bundle = build_evidence_bundle(artifact, validation, environment)

    policy = QComputeEvidencePolicy()
    policy_report = policy.evaluate(bundle)
    assert policy_report.decision == "allow"

    governance = QComputeGovernanceAdapter()
    events = governance.build_session_events(bundle, policy_report)
    assert len(events) >= 2


# ---------------------------------------------------------------------------
# 3. Noisy pipeline with ZNE mitigation
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
async def test_qcompute_noisy_pipeline_with_mitigation(tmp_path: Path) -> None:
    spec = _build_spec(
        task_id="integration-noisy-zne",
        noise=QComputeNoiseSpec(
            model="depolarizing",
            depolarizing_prob=0.01,
        ),
        error_mitigation=["zne"],
    )

    # 1. Probe
    environment = QComputeEnvironmentProbeComponent().probe(spec)
    assert environment.available

    # 2. Compile
    compiler = QComputeConfigCompilerComponent()
    plan = compiler.build_plan(spec, environment)

    # 3. Execute
    executor = QComputeExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))
    artifact = executor.execute_plan(plan, environment)

    assert artifact.status == "completed"
    assert artifact.counts is not None
    assert sum(artifact.counts.values()) == spec.shots

    # Verify mitigation metadata present
    mitigation = artifact.execution_policy.details["error_mitigation"]
    assert mitigation["zne"]["applied"] is True
    assert mitigation["requested"] == ["zne"]
    assert "expectation_zero" in mitigation["zne"]

    # 4. Validate
    validator = QComputeValidatorComponent()
    validation = validator.validate_run(artifact, plan, environment)
    assert validation.passed
    assert validation.promotion_ready

    # 5. Evidence + policy + governance
    bundle = build_evidence_bundle(artifact, validation, environment)

    policy = QComputeEvidencePolicy()
    policy_report = policy.evaluate(bundle)
    assert policy_report.decision == "allow"

    governance = QComputeGovernanceAdapter()
    events = governance.build_session_events(bundle, policy_report)
    assert len(events) >= 2


# ---------------------------------------------------------------------------
# 4. Failed execution pipeline (unavailable environment)
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
async def test_qcompute_failed_execution_pipeline(tmp_path: Path) -> None:
    # Build a valid spec, then fabricate an unavailable environment report
    # to simulate the failure path through executor -> validator -> policy.
    spec = _build_spec(task_id="integration-failed")

    # 1. Manually create an unavailable environment report
    environment = QComputeEnvironmentReport(
        task_id=spec.task_id,
        backend=spec.backend,
        available=False,
        status="dependency_missing",
        prerequisite_errors=["Simulated: qiskit dependency missing"],
        blocks_promotion=True,
    )

    # 2. Compile without the environment (bypass the availability check)
    compiler = QComputeConfigCompilerComponent()
    plan = compiler.build_plan(spec)

    # 3. Execute with the unavailable environment report
    executor = QComputeExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))
    artifact = executor.execute_plan(plan, environment)

    assert artifact.status == "failed"
    assert artifact.terminal_error_type == "environment_unavailable"
    assert artifact.error_message is not None

    # 4. Validate the failed run
    validator = QComputeValidatorComponent()
    validation = validator.validate_run(artifact, plan, environment)
    assert not validation.passed

    # 5. Evidence + policy -- should reject
    bundle = build_evidence_bundle(artifact, validation, environment)

    policy = QComputeEvidencePolicy()
    policy_report = policy.evaluate(bundle)
    assert policy_report.decision == "reject"

    governance = QComputeGovernanceAdapter()
    events = governance.build_session_events(bundle, policy_report)
    # At least CANDIDATE_VALIDATED + SAFETY_GATE_EVALUATED + CANDIDATE_REJECTED
    assert len(events) >= 3


# ---------------------------------------------------------------------------
# 5. VQE H2 energy estimation (Phase 1 acceptance criterion)
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_qcompute_vqe_h2_energy_estimation():
    """VQE H2 minimal baseline: energy error < 0.1 Hartree on Qiskit Aer.

    Phase 1 acceptance criterion from roadmap 6.3.3.
    Uses a hardware-efficient VQE ansatz with H2 Hamiltonian coefficients
    to estimate the ground state energy and compares against the known
    STO-3G value.
    """
    from qiskit import QuantumCircuit
    from qiskit_aer import AerSimulator

    # H2 STO-3G Hamiltonian coefficients (2 qubits, Jordan-Wigner mapped)
    # H = c0*I + c1*Z0 + c2*Z1 + c3*Z0Z1 + c4*X0X1 + c5*Y0Y1
    # Coefficients from standard H2 at R=0.735 Angstrom
    c0 = -0.8105  # identity offset
    c1 = 0.1721  # Z0
    c2 = 0.1721  # Z1
    c3 = 0.1686  # Z0Z1
    c4 = 0.0454  # X0X1
    c5 = 0.0454  # Y0Y1

    # Reference energy from exact diagonalization
    reference_energy = -1.1373  # Hartree

    simulator = AerSimulator()

    def _build_ansatz(t0: float, t1: float) -> QuantumCircuit:
        """Two-parameter hardware-efficient ansatz: RY(t0) q0, RY(t1) q1, CX."""
        qc = QuantumCircuit(2)
        qc.ry(t0, 0)
        qc.ry(t1, 1)
        qc.cx(0, 1)
        return qc

    def compute_energy(t0: float, t1: float) -> float:
        # Z-basis measurement for Z0, Z1, Z0Z1
        z_circ = _build_ansatz(t0, t1)
        z_circ.measure_all()
        z_result = simulator.run(z_circ, shots=8192).result()
        counts = z_result.get_counts()
        total = sum(counts.values())
        p00 = counts.get("00", 0) / total
        p01 = counts.get("01", 0) / total
        p10 = counts.get("10", 0) / total
        p11 = counts.get("11", 0) / total

        z0_exp = p00 + p01 - p10 - p11
        z1_exp = p00 - p01 + p10 - p11
        z0z1_exp = p00 - p01 - p10 + p11

        # X-basis measurement for X0X1 (Hadamard rotation before measure)
        x_circ = _build_ansatz(t0, t1)
        x_circ.h(0)
        x_circ.h(1)
        x_circ.measure_all()
        x_result = simulator.run(x_circ, shots=8192).result()
        x_counts = x_result.get_counts()
        x_total = sum(x_counts.values())
        x0x1_exp = (
            x_counts.get("00", 0) / x_total
            - x_counts.get("01", 0) / x_total
            - x_counts.get("10", 0) / x_total
            + x_counts.get("11", 0) / x_total
        )

        # Y-basis measurement for Y0Y1 (Sdg + H rotation before measure)
        y_circ = _build_ansatz(t0, t1)
        y_circ.sdg(0)
        y_circ.h(0)
        y_circ.sdg(1)
        y_circ.h(1)
        y_circ.measure_all()
        y_result = simulator.run(y_circ, shots=8192).result()
        y_counts = y_result.get_counts()
        y_total = sum(y_counts.values())
        y0y1_exp = (
            y_counts.get("00", 0) / y_total
            - y_counts.get("01", 0) / y_total
            - y_counts.get("10", 0) / y_total
            + y_counts.get("11", 0) / y_total
        )

        return c0 + c1 * z0_exp + c2 * z1_exp + c3 * z0z1_exp + c4 * x0x1_exp + c5 * y0y1_exp

    # 2D grid search over (theta0, theta1)
    best_energy = float("inf")
    best_t0, best_t1 = 0.0, 0.0
    for t0 in np.linspace(0, 2 * np.pi, 15):
        for t1 in np.linspace(0, 2 * np.pi, 15):
            e = compute_energy(float(t0), float(t1))
            if e < best_energy:
                best_energy = e
                best_t0, best_t1 = float(t0), float(t1)

    # Fine-grained search around the best point
    for t0 in np.linspace(best_t0 - 0.4, best_t0 + 0.4, 8):
        for t1 in np.linspace(best_t1 - 0.4, best_t1 + 0.4, 8):
            e = compute_energy(float(t0), float(t1))
            if e < best_energy:
                best_energy = e

    energy_error = abs(best_energy - reference_energy)
    assert energy_error < 0.1, (
        f"VQE H2 energy error {energy_error:.4f} Hartree exceeds 0.1 Hartree "
        f"threshold. Estimated: {best_energy:.4f}, Reference: "
        f"{reference_energy:.4f}"
    )
