"""Tests verifying QCompute types satisfy enhanced MHE core Protocols."""

from __future__ import annotations

import inspect

from metaharness.sdk.execution import (
    EnvironmentReportProtocol,
    EvidenceBundleProtocol,
    RunArtifactProtocol,
    RunPlanProtocol,
    ValidationOutcomeProtocol,
)
from metaharness_ext.qcompute.backends.quafu import QuafuBackendAdapter
from metaharness_ext.qcompute.contracts import (
    QComputeBackendSpec,
    QComputeEnvironmentReport,
    QComputeEvidenceBundle,
    QComputeExecutionParams,
    QComputeRunArtifact,
    QComputeRunPlan,
    QComputeValidationReport,
)
from metaharness_ext.qcompute.types import QComputeValidationStatus

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _backend_spec() -> QComputeBackendSpec:
    return QComputeBackendSpec(platform="qiskit_aer", simulator=True, qubit_count=4)


def _run_plan() -> QComputeRunPlan:
    return QComputeRunPlan(
        plan_id="test-plan-001",
        experiment_ref="test-exp-001",
        circuit_openqasm='OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; h q[0]; cx q[0],q[1];',
        target_backend=_backend_spec(),
        compilation_strategy="baseline",
        execution_params=QComputeExecutionParams(),
    )


def _run_artifact() -> QComputeRunArtifact:
    return QComputeRunArtifact(
        artifact_id="test-artifact-001",
        plan_ref="test-plan-001",
        backend_actual="qiskit_aer",
        status="completed",
        counts={"00": 128, "11": 128},
    )


def _environment_report() -> QComputeEnvironmentReport:
    return QComputeEnvironmentReport(
        task_id="test-task-001",
        backend=_backend_spec(),
        available=True,
        status="ready",
    )


def _validation_report() -> QComputeValidationReport:
    return QComputeValidationReport(
        task_id="test-task-001",
        plan_ref="test-plan-001",
        artifact_ref="test-artifact-001",
        passed=True,
        status=QComputeValidationStatus.VALIDATED,
    )


def _evidence_bundle() -> QComputeEvidenceBundle:
    return QComputeEvidenceBundle(
        bundle_id="test-bundle-001",
        experiment_ref="test-exp-001",
        environment_report=_environment_report(),
        run_artifact=_run_artifact(),
        validation_report=_validation_report(),
    )


# ===================================================================
# Part 1: isinstance Protocol conformance checks
# ===================================================================


class TestRunPlanProtocolConformance:
    def test_qcompute_run_plan_satisfies_run_plan_protocol(self) -> None:
        plan = _run_plan()
        assert isinstance(plan, RunPlanProtocol)

    def test_qcompute_run_plan_has_required_fields(self) -> None:
        plan = _run_plan()
        assert hasattr(plan, "plan_id")
        assert hasattr(plan, "experiment_ref")
        assert hasattr(plan, "target_backend")
        assert hasattr(plan, "execution_params")


class TestRunArtifactProtocolConformance:
    def test_qcompute_run_artifact_satisfies_run_artifact_protocol(self) -> None:
        artifact = _run_artifact()
        assert isinstance(artifact, RunArtifactProtocol)

    def test_qcompute_run_artifact_has_required_fields(self) -> None:
        artifact = _run_artifact()
        assert hasattr(artifact, "artifact_id")
        assert hasattr(artifact, "plan_ref")
        assert hasattr(artifact, "status")
        assert hasattr(artifact, "raw_output_path")


class TestEnvironmentReportProtocolConformance:
    def test_qcompute_environment_report_satisfies_protocol(self) -> None:
        report = _environment_report()
        assert isinstance(report, EnvironmentReportProtocol)

    def test_qcompute_environment_report_has_required_fields(self) -> None:
        report = _environment_report()
        assert hasattr(report, "task_id")
        assert hasattr(report, "available")
        assert hasattr(report, "blocks_promotion")


class TestValidationOutcomeProtocolConformance:
    def test_qcompute_validation_report_satisfies_protocol(self) -> None:
        report = _validation_report()
        assert isinstance(report, ValidationOutcomeProtocol)

    def test_qcompute_validation_report_has_required_fields(self) -> None:
        report = _validation_report()
        assert hasattr(report, "task_id")
        assert hasattr(report, "status")


class TestEvidenceBundleProtocolConformance:
    def test_qcompute_evidence_bundle_satisfies_protocol(self) -> None:
        bundle = _evidence_bundle()
        assert isinstance(bundle, EvidenceBundleProtocol)

    def test_qcompute_evidence_bundle_has_required_fields(self) -> None:
        bundle = _evidence_bundle()
        assert hasattr(bundle, "bundle_id")


# ===================================================================
# AsyncExecutorProtocol: structural verification via inspect
# ===================================================================

_ASYNC_METHODS = ("submit", "poll", "cancel", "await_result")


class TestAsyncExecutorProtocolConformance:
    def test_quafu_adapter_has_async_executor_methods(self) -> None:
        adapter = QuafuBackendAdapter()
        for method_name in _ASYNC_METHODS:
            assert hasattr(adapter, method_name), (
                f"QuafuBackendAdapter missing method: {method_name}"
            )

    def test_quafu_adapter_methods_are_async(self) -> None:
        adapter = QuafuBackendAdapter()
        for method_name in _ASYNC_METHODS:
            method = getattr(adapter, method_name)
            assert inspect.iscoroutinefunction(method), (
                f"QuafuBackendAdapter.{method_name} is not async"
            )

    def test_quafu_adapter_submit_signature(self) -> None:
        sig = inspect.signature(QuafuBackendAdapter.submit)
        params = list(sig.parameters.keys())
        assert "plan" in params, "submit() missing 'plan' parameter"

    def test_quafu_adapter_poll_signature(self) -> None:
        sig = inspect.signature(QuafuBackendAdapter.poll)
        params = list(sig.parameters.keys())
        assert "job_id" in params, "poll() missing 'job_id' parameter"

    def test_quafu_adapter_cancel_signature(self) -> None:
        sig = inspect.signature(QuafuBackendAdapter.cancel)
        params = list(sig.parameters.keys())
        assert "job_id" in params, "cancel() missing 'job_id' parameter"

    def test_quafu_adapter_await_result_signature(self) -> None:
        sig = inspect.signature(QuafuBackendAdapter.await_result)
        params = list(sig.parameters.keys())
        assert "job_id" in params, "await_result() missing 'job_id' parameter"
        assert "timeout" in params, "await_result() missing 'timeout' parameter"
