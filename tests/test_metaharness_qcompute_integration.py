from __future__ import annotations

import json
from pathlib import Path

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
