from __future__ import annotations

from datetime import timezone
from typing import Any

from metaharness.sdk import (
    EnvironmentReportProtocol,
    EvidenceBundleProtocol,
    ExecutionStatus,
    FibonacciPollingStrategy,
    JobHandle,
    ResourceQuota,
    ResourceQuotaProtocol,
    RunArtifactProtocol,
    RunPlanProtocol,
    ValidationOutcomeProtocol,
)
from metaharness_ext.qcompute.contracts import (
    QComputeBackendSpec,
    QComputeEnvironmentReport,
    QComputeEvidenceBundle,
    QComputeExecutionParams,
    QComputeExperimentSpec,
    QComputeNoiseSpec,
    QComputeRunArtifact,
    QComputeRunPlan,
    QComputeValidationMetrics,
    QComputeValidationReport,
)
from metaharness_ext.qcompute.types import QComputeValidationStatus


def _consume_run_plan(plan: RunPlanProtocol) -> tuple[str, Any, Any]:
    return plan.plan_id, plan.target_backend, plan.execution_params


def _consume_run_artifact(artifact: RunArtifactProtocol) -> tuple[str, str, Any, str | None]:
    return artifact.artifact_id, artifact.plan_ref, artifact.status, artifact.raw_output_path


def _consume_environment_report(report: EnvironmentReportProtocol) -> tuple[str, bool, bool]:
    return report.task_id, report.available, report.blocks_promotion


def _consume_validation_report(report: ValidationOutcomeProtocol) -> tuple[str, Any]:
    return report.task_id, report.status


def _consume_evidence_bundle(bundle: EvidenceBundleProtocol) -> str:
    return bundle.bundle_id


def _consume_resource_quota(quota: ResourceQuotaProtocol) -> tuple[str, float | int | None, bool]:
    return quota.resource_type, quota.remaining, quota.exhausted


def _build_experiment_spec() -> QComputeExperimentSpec:
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
    )


def test_execution_status_values_are_stable() -> None:
    assert ExecutionStatus.CREATED.value == "created"
    assert ExecutionStatus.QUEUED.value == "queued"
    assert ExecutionStatus.RUNNING.value == "running"
    assert ExecutionStatus.COMPLETED.value == "completed"
    assert ExecutionStatus.FAILED.value == "failed"
    assert ExecutionStatus.TIMEOUT.value == "timeout"
    assert ExecutionStatus.CANCELLED.value == "cancelled"


def test_job_handle_roundtrip() -> None:
    handle = JobHandle(job_id="job-1", backend="mock", status=ExecutionStatus.QUEUED)

    loaded = JobHandle.model_validate_json(handle.model_dump_json())

    assert loaded == handle
    assert loaded.submitted_at.tzinfo == timezone.utc
    assert loaded.completed_at is None


def test_resource_quota_roundtrip_and_defaults() -> None:
    quota = ResourceQuota(resource_type="gpu", remaining=2, metadata={"queue": "short"})

    loaded = ResourceQuota.model_validate_json(quota.model_dump_json())

    assert loaded == quota
    assert loaded.quota_id is None
    assert loaded.provider is None
    assert loaded.limit is None
    assert loaded.used == 0
    assert loaded.exhausted is False
    assert loaded.metadata == {"queue": "short"}


def test_resource_quota_satisfies_protocol() -> None:
    quota = ResourceQuota(
        quota_id="quota-1",
        resource_type="shots",
        provider="qcompute",
        limit=1000,
        used=1000,
        remaining=0,
        unit="shots",
        scope="session",
        exhausted=True,
    )

    assert _consume_resource_quota(quota) == ("shots", 0, True)
    assert isinstance(quota, ResourceQuotaProtocol)


def test_fibonacci_polling_strategy_sequence_and_cap() -> None:
    strategy = FibonacciPollingStrategy(base_delay=1.0, max_delay=30.0, max_total_wait=600.0)

    assert [strategy.next_delay(attempt) for attempt in range(1, 8)] == [
        1.0,
        1.0,
        2.0,
        3.0,
        5.0,
        8.0,
        13.0,
    ]
    assert strategy.next_delay(9) == 30.0


def test_fibonacci_polling_strategy_schedule_respects_total_wait_cap() -> None:
    strategy = FibonacciPollingStrategy(base_delay=10.0, max_delay=30.0, max_total_wait=65.0)

    assert strategy.schedule(10) == [10.0, 10.0, 20.0, 25.0]
    assert sum(strategy.schedule(10)) == 65.0


def test_qcompute_contracts_satisfy_core_execution_protocols() -> None:
    spec = _build_experiment_spec()
    plan = QComputeRunPlan(
        plan_id="plan-1",
        experiment_ref=spec.task_id,
        circuit_openqasm=spec.circuit.openqasm or "",
        target_backend=spec.backend,
        compilation_strategy="baseline",
        execution_params=QComputeExecutionParams(shots=spec.shots),
    )
    artifact = QComputeRunArtifact(
        artifact_id="artifact-1",
        plan_ref="plan-1",
        backend_actual="qiskit_aer",
        status="completed",
        raw_output_path="artifacts/run.json",
    )
    environment = QComputeEnvironmentReport(
        task_id=spec.task_id,
        backend=spec.backend,
        available=True,
        status="online",
    )
    validation = QComputeValidationReport(
        task_id=spec.task_id,
        plan_ref="plan-1",
        artifact_ref="artifact-1",
        passed=True,
        status=QComputeValidationStatus.VALIDATED,
        metrics=QComputeValidationMetrics(fidelity=0.99),
    )
    bundle = QComputeEvidenceBundle(
        bundle_id="bundle-1",
        experiment_ref=spec.task_id,
        environment_report=environment,
        run_artifact=artifact,
        validation_report=validation,
    )

    assert _consume_run_plan(plan)[0] == "plan-1"
    assert _consume_run_artifact(artifact) == (
        "artifact-1",
        "plan-1",
        "completed",
        "artifacts/run.json",
    )
    assert _consume_environment_report(environment) == (spec.task_id, True, False)
    assert _consume_validation_report(validation) == (
        spec.task_id,
        QComputeValidationStatus.VALIDATED,
    )
    assert _consume_evidence_bundle(bundle) == "bundle-1"
