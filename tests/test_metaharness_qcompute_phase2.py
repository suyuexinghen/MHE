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
)
from metaharness_ext.qcompute.evidence import build_evidence_bundle
from metaharness_ext.qcompute.governance import QComputeGovernanceAdapter
from metaharness_ext.qcompute.policy import QComputeEvidencePolicy
from metaharness_ext.qcompute.validator import QComputeValidatorComponent


def _build_inputs() -> tuple[QComputeRunArtifact, QComputeRunPlan, QComputeEnvironmentReport]:
    backend = QComputeBackendSpec(platform="qiskit_aer", simulator=True, qubit_count=1)
    plan = QComputeRunPlan(
        plan_id="plan-1",
        experiment_ref="qcompute-exp-1",
        circuit_openqasm='OPENQASM 2.0; include "qelib1.inc"; qreg q[1]; creg c[1]; h q[0]; measure q[0] -> c[0];',
        target_backend=backend,
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
        counts={"0": 64, "1": 64},
        raw_output_path="qcompute_runs/qcompute-exp-1/plan-1/result.json",
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
