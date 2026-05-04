from metaharness.core.execution_modes import ExecutionMode
from metaharness.core.models import SessionEventType
from metaharness.observability.events import InMemorySessionStore
from metaharness.provenance import AuditLog, ProvGraph
from metaharness_ext.qcompute.contracts import (
    QComputeBackendSpec,
    QComputeCandidateIdentity,
    QComputeEnvironmentReport,
    QComputeExecutionParams,
    QComputeRunArtifact,
    QComputeRunPlan,
    QComputeValidationReport,
)
from metaharness_ext.qcompute.evidence import (
    build_evidence_bundle,
    build_instantiation_record,
    qcompute_core_execution_mode,
)
from metaharness_ext.qcompute.governance import QComputeGovernanceAdapter
from metaharness_ext.qcompute.policy import QComputeEvidencePolicy
from metaharness_ext.qcompute.types import QComputeValidationStatus
from metaharness_ext.qcompute.validator import QComputeValidatorComponent


def _build_inputs() -> tuple[QComputeRunArtifact, QComputeRunPlan, QComputeEnvironmentReport]:
    backend = QComputeBackendSpec(platform="qiskit_aer", simulator=True, qubit_count=1)
    plan = QComputeRunPlan(
        plan_id="plan-1",
        experiment_ref="qcompute-exp-1",
        circuit_openqasm='OPENQASM 2.0; include "qelib1.inc"; qreg q[1]; creg c[1]; h q[0]; measure q[0] -> c[0];',
        target_backend=backend,
        native_execution_mode="simulate",
        compilation_strategy="baseline",
        compilation_metadata={"operation_counts": {"h": 1}, "fidelity_threshold": 0.9},
        estimated_depth=2,
        estimated_swap_count=0,
        estimated_fidelity=0.99,
        execution_params=QComputeExecutionParams(shots=128),
    )
    artifact = QComputeRunArtifact(
        artifact_id="artifact-1",
        plan_ref="plan-1",
        backend_actual="qiskit_aer",
        status="completed",
        native_execution_mode="simulate",
        counts={"0": 64, "1": 64},
        raw_output_path=".runs/qcompute/qcompute-exp-1/plan-1/result.json",
        shots_requested=128,
        shots_completed=128,
        candidate_identity=QComputeCandidateIdentity(candidate_id="cand-1", graph_version_id=7),
    )
    environment = QComputeEnvironmentReport(
        task_id="qcompute-exp-1",
        backend=backend,
        available=True,
        status="online",
    )
    return artifact, plan, environment


def test_qcompute_evidence_bundle_collects_refs_and_warnings() -> None:
    artifact, plan, environment = _build_inputs()
    validation = QComputeValidatorComponent().validate_run(artifact, plan, environment)

    bundle = build_evidence_bundle(artifact, validation, environment)

    assert bundle.experiment_ref == "qcompute-exp-1"
    assert bundle.validation_report is validation
    assert bundle.scored_evidence is validation.scored_evidence
    assert bundle.warnings == []
    assert any(ref.startswith("qcompute://artifact/") for ref in bundle.provenance_refs)


def test_qcompute_policy_allows_complete_evidence() -> None:
    artifact, plan, environment = _build_inputs()
    validation = QComputeValidatorComponent().validate_run(artifact, plan, environment)
    bundle = build_evidence_bundle(artifact, validation, environment)

    report = QComputeEvidencePolicy().evaluate(bundle)

    assert report.passed is True
    assert report.decision == "allow"
    assert report.gates[-1].gate == "qcompute_evidence_ready"


def test_qcompute_simulator_maps_to_simulation_without_external_receipts() -> None:
    artifact, plan, environment = _build_inputs()
    validation = QComputeValidatorComponent().validate_run(artifact, plan, environment)
    bundle = build_evidence_bundle(artifact, validation, environment)
    record = build_instantiation_record(bundle, candidate_id="cand-1", graph_version=7)

    assert qcompute_core_execution_mode("simulate", environment.backend, artifact) == (
        ExecutionMode.SIMULATION
    )
    assert bundle.external_evidence_refs == []
    assert record.execution_mode == ExecutionMode.SIMULATION
    assert record.native_execution_mode == "simulate"
    assert record.external_evidence_refs == []


def test_qcompute_real_backend_requires_receipt_for_external_verified() -> None:
    artifact, plan, environment = _build_inputs()
    real_backend = QComputeBackendSpec(platform="quafu", simulator=False, qubit_count=4)
    plan.target_backend = real_backend
    plan.native_execution_mode = "run"
    artifact.backend_actual = "quafu"
    artifact.native_execution_mode = "run"
    environment.backend = real_backend
    validation = QComputeValidatorComponent().validate_run(artifact, plan, environment)
    bundle = build_evidence_bundle(artifact, validation, environment)
    record = build_instantiation_record(bundle, candidate_id="cand-1", graph_version=7)

    assert bundle.external_evidence_refs
    assert record.execution_mode == ExecutionMode.EXTERNAL_VERIFIED
    assert record.external_evidence_refs == bundle.external_evidence_refs


def test_qcompute_real_backend_without_receipt_stays_instantiated() -> None:
    artifact, _, environment = _build_inputs()
    real_backend = QComputeBackendSpec(platform="quafu", simulator=False, qubit_count=4)
    artifact.backend_actual = "quafu"
    artifact.native_execution_mode = "run"
    artifact.raw_output_path = None
    environment.backend = real_backend
    validation = QComputeValidationReport(
        task_id=environment.task_id,
        plan_ref=artifact.plan_ref,
        artifact_ref=artifact.artifact_id,
        passed=True,
        status=QComputeValidationStatus.VALIDATED,
        promotion_ready=True,
    )
    bundle = build_evidence_bundle(artifact, validation, environment)
    record = build_instantiation_record(bundle, candidate_id="cand-1", graph_version=7)

    assert bundle.external_evidence_refs == []
    assert record.execution_mode == ExecutionMode.INSTANTIATED
    assert record.external_evidence_refs == []


def test_qcompute_policy_rejects_blocked_environment() -> None:
    artifact, plan, environment = _build_inputs()
    environment.available = False
    environment.status = "calibration_unavailable"
    environment.blocks_promotion = True
    validation = QComputeValidatorComponent().validate_run(artifact, plan, environment)
    bundle = build_evidence_bundle(artifact, validation, environment)

    report = QComputeEvidencePolicy().evaluate(bundle)

    assert report.passed is False
    assert report.decision == "reject"
    assert any(gate.gate == "environment_readiness" for gate in report.gates)


def test_qcompute_governance_builds_records_and_runtime_evidence() -> None:
    artifact, plan, environment = _build_inputs()
    validation = QComputeValidatorComponent().validate_run(artifact, plan, environment)
    bundle = build_evidence_bundle(artifact, validation, environment)
    policy = QComputeEvidencePolicy().evaluate(bundle)
    governance = QComputeGovernanceAdapter(session_id="session-1")

    core_report = governance.build_core_validation_report(validation, policy)
    candidate = governance.build_candidate_record(bundle, policy)
    events = governance.build_session_events(bundle, policy)
    handoff = governance.emit_runtime_evidence(
        bundle,
        policy,
        session_store=InMemorySessionStore(),
        audit_log=AuditLog(),
        provenance_graph=ProvGraph(),
    )

    assert core_report.valid is True
    assert candidate.candidate_id == "cand-1"
    assert candidate.snapshot.graph_version == 7
    assert candidate.promoted is True
    assert [event.event_type for event in events] == [
        SessionEventType.CANDIDATE_VALIDATED,
        SessionEventType.SAFETY_GATE_EVALUATED,
    ]
    assert handoff["audit_refs"]
    assert handoff["provenance_refs"]
