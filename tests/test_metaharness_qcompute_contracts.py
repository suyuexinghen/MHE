from __future__ import annotations

from datetime import datetime, timezone

from metaharness.core.models import ScoredEvidence
from metaharness_ext.qcompute.backends import MockQuantumBackend
from metaharness_ext.qcompute.contracts import (
    QComputeBackendSpec,
    QComputeEnvironmentReport,
    QComputeEvidenceBundle,
    QComputeExecutionParams,
    QComputeExperimentSpec,
    QComputeNoiseSpec,
    QComputeRunArtifact,
    QComputeRunPlan,
    QComputeStudyAxis,
    QComputeStudySpec,
    QComputeStudyTrial,
    QComputeValidationMetrics,
    QComputeValidationReport,
)
from metaharness_ext.qcompute.types import QComputeValidationStatus


def build_experiment_spec() -> QComputeExperimentSpec:
    return QComputeExperimentSpec(
        task_id="qcompute-exp-1",
        mode="simulate",
        backend=QComputeBackendSpec(platform="qiskit_aer", simulator=True, qubit_count=2),
        circuit={
            "ansatz": "custom",
            "num_qubits": 2,
            "openqasm": 'OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; h q[0]; cx q[0],q[1];',
        },
        noise=QComputeNoiseSpec(model="depolarizing", depolarizing_prob=0.001),
        shots=2048,
        fidelity_threshold=0.95,
        metadata={"family": "bell"},
    )


def build_validation_report() -> QComputeValidationReport:
    return QComputeValidationReport(
        task_id="qcompute-exp-1",
        plan_ref="plan-1",
        artifact_ref="artifact-1",
        passed=False,
        status=QComputeValidationStatus.BELOW_FIDELITY_THRESHOLD,
        metrics=QComputeValidationMetrics(fidelity=0.85, noise_impact_score=0.2),
        scored_evidence=ScoredEvidence(score=0.85),
    )


def test_experiment_spec_roundtrip() -> None:
    spec = build_experiment_spec()

    dumped = spec.model_dump_json()
    loaded = QComputeExperimentSpec.model_validate_json(dumped)

    assert loaded == spec
    assert loaded.circuit.ansatz == "custom"
    assert loaded.backend.platform == "qiskit_aer"


def test_governance_metadata_defaults() -> None:
    spec = build_experiment_spec()

    assert spec.candidate_identity.candidate_id is None
    assert spec.promotion_metadata.outcome == "pending"
    assert spec.checkpoint_refs == []
    assert spec.provenance_refs == []
    assert spec.trace_refs == []
    assert spec.execution_policy.max_retry == 3


def test_study_spec_roundtrip() -> None:
    experiment = build_experiment_spec()
    report = build_validation_report()
    artifact = QComputeRunArtifact(
        artifact_id="artifact-1",
        plan_ref="plan-1",
        backend_actual="qiskit_aer",
        status="completed",
        counts={"00": 1024, "11": 1024},
    )
    bundle = QComputeEvidenceBundle(
        bundle_id="bundle-1",
        experiment_ref=experiment.task_id,
        environment_report=QComputeEnvironmentReport(
            task_id=experiment.task_id,
            backend=experiment.backend,
            available=True,
            status="online",
        ),
        run_artifact=artifact,
        validation_report=report,
    )
    study = QComputeStudySpec(
        study_id="study-1",
        experiment_template=experiment,
        axes=[QComputeStudyAxis(parameter_path="circuit.repetitions", values=[1, 2, 3])],
        strategy="grid",
        objective="fidelity",
    )
    trial = QComputeStudyTrial(
        trial_id="trial-1",
        parameter_snapshot={"circuit.repetitions": 1},
        evidence_bundle=bundle,
        trajectory_score=0.85,
    )

    loaded = QComputeStudySpec.model_validate_json(study.model_dump_json())

    assert loaded == study
    assert (
        trial.evidence_bundle.validation_report.status
        is QComputeValidationStatus.BELOW_FIDELITY_THRESHOLD
    )


def test_validation_report_status_and_defaults() -> None:
    report = build_validation_report()

    assert report.status is QComputeValidationStatus.BELOW_FIDELITY_THRESHOLD
    assert report.metrics.fidelity == 0.85
    assert report.promotion_ready is False
    assert report.evidence_refs == []
    assert report.scored_evidence is not None


def test_run_plan_and_mock_backend_behave_deterministically() -> None:
    spec = build_experiment_spec()
    plan = QComputeRunPlan(
        plan_id="plan-1",
        experiment_ref=spec.task_id,
        circuit_openqasm=spec.circuit.openqasm or "",
        target_backend=spec.backend,
        compilation_strategy="baseline",
        execution_params=QComputeExecutionParams(shots=spec.shots),
    )
    backend = MockQuantumBackend({"00": 512, "11": 512})

    assert plan.execution_params.shots == 2048
    assert backend.run(circuit=object(), shots=2048) == {"00": 512, "11": 512}


def test_evidence_bundle_created_at_defaults() -> None:
    experiment = build_experiment_spec()
    bundle = QComputeEvidenceBundle(
        bundle_id="bundle-time",
        experiment_ref=experiment.task_id,
        environment_report=QComputeEnvironmentReport(
            task_id=experiment.task_id,
            backend=experiment.backend,
            available=True,
            status="online",
        ),
        run_artifact=QComputeRunArtifact(
            artifact_id="artifact-time",
            plan_ref="plan-time",
            backend_actual="qiskit_aer",
            status="created",
        ),
        validation_report=QComputeValidationReport(
            task_id=experiment.task_id,
            plan_ref="plan-time",
            artifact_ref="artifact-time",
            metrics=QComputeValidationMetrics(),
        ),
    )

    assert isinstance(bundle.created_at, datetime)
    assert bundle.created_at.tzinfo == timezone.utc
