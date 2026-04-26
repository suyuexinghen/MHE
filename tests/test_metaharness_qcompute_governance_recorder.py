"""Tests for QCompute governance artifact-store recording and gateway integration."""

from __future__ import annotations

import asyncio
from pathlib import Path

from metaharness.observability.events import InMemorySessionStore
from metaharness.provenance import ArtifactSnapshotStore, AuditLog, ProvGraph
from metaharness.safety.gates import GateDecision, GateResult
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.qcompute.contracts import (
    QComputeBackendSpec,
    QComputeCircuitSpec,
    QComputeEnvironmentReport,
    QComputeEvidenceBundle,
    QComputeExperimentSpec,
    QComputePolicyReport,
    QComputeRunArtifact,
    QComputeValidationMetrics,
    QComputeValidationReport,
)
from metaharness_ext.qcompute.gateway import QComputeGatewayComponent
from metaharness_ext.qcompute.governance import QComputeGovernanceAdapter
from metaharness_ext.qcompute.types import QComputeValidationStatus


def _make_bundle() -> tuple[QComputeEvidenceBundle, QComputePolicyReport]:
    env_report = QComputeEnvironmentReport(
        task_id="test-task",
        backend=QComputeBackendSpec(platform="qiskit_aer"),
        available=True,
        status="ok",
        backend_version="0.1",
        calibration_fresh=True,
    )
    artifact = QComputeRunArtifact(
        artifact_id="art-1",
        plan_ref="plan-1",
        backend_actual="qiskit_aer",
        status="completed",
        shots_requested=1024,
        shots_completed=1024,
    )
    metrics = QComputeValidationMetrics(fidelity=0.95, energy_error=0.01)
    validation = QComputeValidationReport(
        task_id="test-task",
        plan_ref="plan-1",
        artifact_ref="art-1",
        passed=True,
        status=QComputeValidationStatus.VALIDATED,
        metrics=metrics,
        promotion_ready=True,
    )
    bundle = QComputeEvidenceBundle(
        bundle_id="bundle-1",
        experiment_ref="test-task",
        environment_report=env_report,
        run_artifact=artifact,
        validation_report=validation,
    )
    policy = QComputePolicyReport(
        passed=True,
        decision="allow",
        reason="All gates passed",
        gates=[
            GateResult(
                gate="fidelity",
                decision=GateDecision.ALLOW,
                reason="Fidelity above threshold",
            )
        ],
    )
    return bundle, policy


def _build_spec(
    *,
    task_id: str = "gw-rec-test",
    shots: int = 256,
) -> QComputeExperimentSpec:
    return QComputeExperimentSpec(
        task_id=task_id,
        mode="simulate",
        backend=QComputeBackendSpec(platform="qiskit_aer", simulator=True, qubit_count=2),
        circuit=QComputeCircuitSpec(
            ansatz="custom",
            num_qubits=2,
            openqasm='OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; h q[0]; cx q[0],q[1];',
        ),
        shots=shots,
    )


class TestGovernanceRecordWithArtifactStore:
    def test_record_with_artifact_store_persists_snapshots(self) -> None:
        bundle, policy = _make_bundle()
        governance = QComputeGovernanceAdapter(session_id="sess-1")

        session_store = InMemorySessionStore()
        audit_log = AuditLog()
        provenance_graph = ProvGraph()
        artifact_store = ArtifactSnapshotStore()

        refs = governance.record_with_artifact_store(
            bundle,
            policy,
            session_store=session_store,
            audit_log=audit_log,
            provenance_graph=provenance_graph,
            artifact_store=artifact_store,
        )

        assert "audit_refs" in refs
        assert "provenance_refs" in refs
        assert len(refs["provenance_refs"]) > 0

    def test_record_without_artifact_store_backward_compat(self) -> None:
        bundle, policy = _make_bundle()
        governance = QComputeGovernanceAdapter()

        session_store = InMemorySessionStore()
        audit_log = AuditLog()
        provenance_graph = ProvGraph()

        refs = governance.record_with_artifact_store(
            bundle,
            policy,
            session_store=session_store,
            audit_log=audit_log,
            provenance_graph=provenance_graph,
            artifact_store=None,
        )

        assert "audit_refs" in refs
        assert len(refs["audit_refs"]) > 0

    def test_emit_runtime_evidence_unchanged(self) -> None:
        bundle, policy = _make_bundle()
        governance = QComputeGovernanceAdapter(session_id="sess-2")

        session_store = InMemorySessionStore()
        audit_log = AuditLog()
        provenance_graph = ProvGraph()

        refs = governance.emit_runtime_evidence(
            bundle,
            policy,
            session_store=session_store,
            audit_log=audit_log,
            provenance_graph=provenance_graph,
        )

        assert len(refs["audit_refs"]) > 0
        assert len(refs["provenance_refs"]) > 0


class TestGatewayRunBaselineFullWithArtifactStore:
    async def _activated_gateway(self, tmp_path: Path) -> QComputeGatewayComponent:
        gateway = QComputeGatewayComponent()
        await gateway.activate(ComponentRuntime(storage_path=tmp_path))
        return gateway

    def test_gateway_with_artifact_store(self, tmp_path: Path) -> None:
        gateway = asyncio.get_event_loop().run_until_complete(self._activated_gateway(tmp_path))
        spec = _build_spec(task_id="gw-with-art")
        artifact_store = ArtifactSnapshotStore()
        result = gateway.run_baseline_full(spec, artifact_store=artifact_store)

        assert result.bundle is not None
        assert result.policy is not None
        assert result.core_validation is not None

    def test_gateway_without_artifact_store(self, tmp_path: Path) -> None:
        gateway = asyncio.get_event_loop().run_until_complete(self._activated_gateway(tmp_path))
        spec = _build_spec(task_id="gw-no-art")
        result = gateway.run_baseline_full(spec)

        assert result.bundle is not None
        assert result.policy is not None
