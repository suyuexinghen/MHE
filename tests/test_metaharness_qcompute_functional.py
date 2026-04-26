"""QCompute end-to-end functional tests.

Holistic integration tests that exercise complete user-facing scenarios
through the Gateway five-stage pipeline, verifying all stages
(Environment → Compile → Execute → Validate → Evidence → Policy → Governance)
work together correctly with real quantum execution.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from metaharness.observability.events import InMemorySessionStore
from metaharness.provenance import ArtifactSnapshotStore, AuditLog, ProvGraph
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.qcompute.contracts import (
    QComputeBackendSpec,
    QComputeCircuitSpec,
    QComputeExperimentSpec,
    QComputeNoiseSpec,
    QComputeStudyAxis,
    QComputeStudySpec,
)
from metaharness_ext.qcompute.gateway import QComputeGatewayComponent
from metaharness_ext.qcompute.policy import QComputeEvidencePolicy
from metaharness_ext.qcompute.study import QComputeStudyComponent, trial_to_domain_payload

BELL_STATE_OPENQASM = 'OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; creg c[2]; h q[0]; cx q[0],q[1]; measure q[0]->c[0]; measure q[1]->c[1];'

MEASURED_BELL = 'OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; h q[0]; cx q[0],q[1];'


def _build_spec(
    *,
    task_id: str = "func-bell",
    platform: str = "qiskit_aer",
    shots: int = 1024,
    noise: QComputeNoiseSpec | None = None,
    error_mitigation: list[str] | None = None,
    openqasm: str = MEASURED_BELL,
) -> QComputeExperimentSpec:
    return QComputeExperimentSpec(
        task_id=task_id,
        mode="simulate",
        backend=QComputeBackendSpec(platform=platform, simulator=True, qubit_count=2),
        circuit=QComputeCircuitSpec(ansatz="custom", num_qubits=2, openqasm=openqasm),
        noise=noise,
        shots=shots,
        error_mitigation=error_mitigation or [],
    )


async def _activated_gateway(tmp_path: Path) -> QComputeGatewayComponent:
    gateway = QComputeGatewayComponent()
    await gateway.activate(ComponentRuntime(storage_path=tmp_path))
    return gateway


# ---------------------------------------------------------------------------
# Scenario 1: Bell State — Qiskit Aer 完整管线
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
async def test_functional_bell_state_qiskit_aer(tmp_path: Path) -> None:
    """执行 Bell 态线路，验证量子纠缠输出。"""
    gateway = await _activated_gateway(tmp_path)
    spec = _build_spec(task_id="func-s1")
    bundle = gateway.run_baseline(spec)

    assert bundle.run_artifact.status == "completed"
    assert bundle.run_artifact.counts is not None
    assert sum(bundle.run_artifact.counts.values()) == spec.shots
    for bitstring in bundle.run_artifact.counts:
        assert bitstring in {"00", "11"}

    assert bundle.validation_report.passed
    assert bundle.validation_report.promotion_ready

    # Raw output persisted to disk
    assert bundle.run_artifact.raw_output_path is not None
    raw_path = Path(bundle.run_artifact.raw_output_path)
    assert raw_path.exists()
    raw = json.loads(raw_path.read_text())
    assert raw["shots_completed"] == spec.shots

    assert len(bundle.provenance_refs) > 0


# ---------------------------------------------------------------------------
# Scenario 2: 完整管线含策略与治理 (run_baseline_full)
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
async def test_functional_full_pipeline_with_policy(tmp_path: Path) -> None:
    """执行 Bell 态并通过策略评估和治理记录。"""
    gateway = await _activated_gateway(tmp_path)
    spec = _build_spec(task_id="func-s2")
    result = gateway.run_baseline_full(spec)

    assert result.environment.available
    assert result.policy is not None
    assert result.policy.decision == "allow"
    assert result.core_validation is not None
    assert result.core_validation.valid
    assert result.plan_id is not None
    assert result.artifact_id is not None
    assert result.bundle is not None
    assert result.bundle.run_artifact.status == "completed"


# ---------------------------------------------------------------------------
# Scenario 3: 含 Artifact Store 的增强管线
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
async def test_functional_with_artifact_store(tmp_path: Path) -> None:
    """执行实验并通过 ArtifactSnapshotStore 持久化快照。"""
    gateway = await _activated_gateway(tmp_path)
    spec = _build_spec(task_id="func-s3")
    artifact_store = ArtifactSnapshotStore()
    result = gateway.run_baseline_full(spec, artifact_store=artifact_store)

    assert result.policy is not None
    assert result.policy.decision == "allow"
    assert result.bundle is not None
    assert result.bundle.run_artifact.status == "completed"


# ---------------------------------------------------------------------------
# Scenario 4: PennyLane 后端完整管线
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
async def test_functional_bell_state_pennylane(tmp_path: Path) -> None:
    """使用 PennyLane 模拟器执行 Bell 态。"""
    gateway = await _activated_gateway(tmp_path)
    spec = _build_spec(task_id="func-s4", platform="pennylane_aer")
    bundle = gateway.run_baseline(spec)

    assert bundle.run_artifact.status == "completed"
    assert bundle.run_artifact.counts is not None
    assert sum(bundle.run_artifact.counts.values()) == spec.shots
    for bitstring in bundle.run_artifact.counts:
        assert bitstring in {"00", "11"}

    assert bundle.validation_report.passed


# ---------------------------------------------------------------------------
# Scenario 5: 噪声模拟 + ZNE 误差缓解
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
async def test_functional_noisy_zne_mitigation(tmp_path: Path) -> None:
    """在退极化噪声下执行线路，使用 ZNE 缓解。"""
    gateway = await _activated_gateway(tmp_path)
    spec = _build_spec(
        task_id="func-s5",
        noise=QComputeNoiseSpec(
            model="depolarizing",
            depolarizing_prob=0.01,
        ),
        error_mitigation=["zne"],
    )
    bundle = gateway.run_baseline(spec)

    assert bundle.run_artifact.status == "completed"
    assert bundle.run_artifact.counts is not None

    mitigation = bundle.run_artifact.execution_policy.details["error_mitigation"]
    assert mitigation["zne"]["applied"] is True
    assert mitigation["requested"] == ["zne"]
    assert "expectation_zero" in mitigation["zne"]

    assert bundle.validation_report.passed


# ---------------------------------------------------------------------------
# Scenario 6: ZNE + REM 组合误差缓解
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
async def test_functional_zne_rem_combined(tmp_path: Path) -> None:
    """同时使用 ZNE 和 REM 缓解策略。"""
    gateway = await _activated_gateway(tmp_path)
    spec = _build_spec(
        task_id="func-s6",
        noise=QComputeNoiseSpec(
            model="depolarizing",
            depolarizing_prob=0.01,
            readout_error=0.02,
        ),
        error_mitigation=["zne", "rem"],
    )
    bundle = gateway.run_baseline(spec)

    assert bundle.run_artifact.status == "completed"

    mitigation = bundle.run_artifact.execution_policy.details["error_mitigation"]
    assert mitigation["zne"]["applied"] is True
    assert mitigation["rem"]["applied"] is True

    assert bundle.validation_report.passed


# ---------------------------------------------------------------------------
# Scenario 7: 环境不可用 → 失败路径
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
async def test_functional_unsupported_platform_failure(tmp_path: Path) -> None:
    """不支持的平台触发完整失败管线。"""
    gateway = await _activated_gateway(tmp_path)
    spec = _build_spec(
        task_id="func-s7",
        platform="ibm_quantum",
    )
    bundle = gateway.run_baseline(spec)

    assert bundle.environment_report.available is False
    assert bundle.run_artifact.status == "failed"

    policy = QComputeEvidencePolicy()
    policy_report = policy.evaluate(bundle)
    assert policy_report.decision == "reject"


# ---------------------------------------------------------------------------
# Scenario 8: 参数 Study — Grid 策略
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
async def test_functional_study_grid(tmp_path: Path) -> None:
    """对 shots 参数做网格搜索。"""
    base_spec = _build_spec(
        task_id="func-s8-template",
        openqasm=('OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; ry(0) q[0]; cx q[0],q[1];'),
    )
    study_spec = QComputeStudySpec(
        study_id="func-grid-study",
        experiment_template=base_spec,
        axes=[
            QComputeStudyAxis(
                parameter_path="shots",
                values=[256, 512, 1024],
            ),
        ],
        strategy="grid",
        max_trials=5,
        objective="fidelity",
    )

    study = QComputeStudyComponent()
    await study.activate(ComponentRuntime(storage_path=tmp_path))
    report = study.run_study(study_spec)

    assert len(report.trials) <= 5
    assert report.best_trial_id is not None
    assert "trial_count" in report.convergence_analysis
    assert "best_score" in report.convergence_analysis


# ---------------------------------------------------------------------------
# Scenario 9: 参数 Study — Agentic 策略
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
async def test_functional_study_agentic(tmp_path: Path) -> None:
    """使用智能体策略探索参数空间。"""
    base_spec = _build_spec(
        task_id="func-s9-template",
        openqasm=('OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; ry(0) q[0]; cx q[0],q[1];'),
    )
    study_spec = QComputeStudySpec(
        study_id="func-agentic-study",
        experiment_template=base_spec,
        axes=[
            QComputeStudyAxis(
                parameter_path="fidelity_threshold",
                range=(0.5, 0.99),
                step=0.1,
            ),
        ],
        strategy="agentic",
        max_trials=10,
        objective="fidelity",
    )

    study = QComputeStudyComponent()
    await study.activate(ComponentRuntime(storage_path=tmp_path))
    report = study.run_study(study_spec)

    assert len(report.trials) <= 10

    # Verify domain payload bridge
    if report.best_trial_id is not None:
        best_trial = next(t for t in report.trials if t.trial_id == report.best_trial_id)
        payload = trial_to_domain_payload(best_trial)
        assert "trial_id" in payload
        assert "parameters" in payload
        assert "backend" in payload
        assert payload["backend"] == "qiskit_aer"


# ---------------------------------------------------------------------------
# Scenario 10: Governance E2E — Session Events + Audit Log
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
async def test_functional_governance_e2e(tmp_path: Path) -> None:
    """验证治理管线产出完整的会话事件和审计日志。"""
    from metaharness_ext.qcompute.governance import QComputeGovernanceAdapter

    gateway = await _activated_gateway(tmp_path)
    spec = _build_spec(task_id="func-s10")
    bundle = gateway.run_baseline(spec)

    policy = QComputeEvidencePolicy()
    policy_report = policy.evaluate(bundle)

    session_store = InMemorySessionStore()
    audit_log = AuditLog()
    provenance_graph = ProvGraph()

    governance = QComputeGovernanceAdapter(session_id="func-session-10")
    refs = governance.emit_runtime_evidence(
        bundle,
        policy_report,
        session_store=session_store,
        audit_log=audit_log,
        provenance_graph=provenance_graph,
    )

    assert len(refs["audit_refs"]) > 0
    assert len(refs["provenance_refs"]) > 0
    assert len(session_store.get_events("func-session-10")) >= 2
    assert len(audit_log.records()) >= 2

    # Verify candidate record
    candidate = governance.build_candidate_record(bundle, policy_report)
    assert candidate.promoted is True
    assert candidate.candidate_id is not None
