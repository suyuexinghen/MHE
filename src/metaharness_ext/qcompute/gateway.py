from __future__ import annotations

import uuid

from metaharness.core.models import ValidationIssue, ValidationIssueCategory
from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.manifest import ComponentManifest
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.qcompute.capabilities import CAP_QCOMPUTE_CASE_COMPILE
from metaharness_ext.qcompute.config_compiler import QComputeConfigCompilerComponent
from metaharness_ext.qcompute.contracts import (
    QComputeBaselineResult,
    QComputeEnvironmentReport,
    QComputeEvidenceBundle,
    QComputeExperimentSpec,
    QComputeRunArtifact,
    QComputeRunPlan,
    QComputeValidationReport,
)
from metaharness_ext.qcompute.environment import QComputeEnvironmentProbeComponent
from metaharness_ext.qcompute.executor import QComputeExecutorComponent
from metaharness_ext.qcompute.governance import QComputeGovernanceAdapter
from metaharness_ext.qcompute.policy import QComputeEvidencePolicy
from metaharness_ext.qcompute.slots import QCOMPUTE_GATEWAY_SLOT
from metaharness_ext.qcompute.types import QComputeValidationStatus
from metaharness_ext.qcompute.validator import QComputeValidatorComponent


class QComputeGatewayComponent(HarnessComponent):
    def __init__(self, manifest: ComponentManifest | None = None) -> None:
        self._manifest = manifest
        self._runtime: ComponentRuntime | None = None
        self._environment: QComputeEnvironmentProbeComponent | None = None
        self._compiler: QComputeConfigCompilerComponent | None = None
        self._executor: QComputeExecutorComponent | None = None
        self._validator: QComputeValidatorComponent | None = None

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime
        self._environment = QComputeEnvironmentProbeComponent()
        self._compiler = QComputeConfigCompilerComponent()
        self._executor = QComputeExecutorComponent()
        self._validator = QComputeValidatorComponent()
        await self._environment.activate(runtime)
        await self._compiler.activate(runtime)
        await self._executor.activate(runtime)
        await self._validator.activate(runtime)

    async def deactivate(self) -> None:
        for component in [self._validator, self._executor, self._compiler, self._environment]:
            if component is not None:
                await component.deactivate()
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(QCOMPUTE_GATEWAY_SLOT)
        api.declare_output("task", "QComputeExperimentSpec", mode="sync")
        api.provide_capability(CAP_QCOMPUTE_CASE_COMPILE)

    def issue_task(self, *, experiment: QComputeExperimentSpec) -> QComputeExperimentSpec:
        return experiment

    def compile_experiment(
        self, spec: QComputeExperimentSpec
    ) -> tuple[QComputeEnvironmentReport, QComputeRunPlan]:
        """Stage 1-2: Environment probe + Config compilation."""
        assert self._environment is not None, "Gateway not activated"
        assert self._compiler is not None, "Gateway not activated"
        env_report = self._environment.probe(spec)
        plan = self._compiler.build_plan(spec, environment_report=env_report)
        return env_report, plan

    def run_baseline(self, spec: QComputeExperimentSpec) -> QComputeEvidenceBundle:
        """Full five-stage pipeline: Environment -> Compile -> Execute -> Validate -> Evidence."""
        assert self._environment is not None, "Gateway not activated"
        assert self._compiler is not None, "Gateway not activated"
        assert self._executor is not None, "Gateway not activated"
        assert self._validator is not None, "Gateway not activated"

        # Stage 1: Environment
        env_report = self._environment.probe(spec)
        if not env_report.available:
            return self._failed_environment_bundle(spec, env_report)

        # Stage 2: Compile
        plan = self._compiler.build_plan(spec, environment_report=env_report)

        # Stage 3: Execute
        artifact = self._executor.execute_plan(plan, environment_report=env_report)

        # Stage 4: Validate
        validation = self._validator.validate_run(artifact, plan, env_report)

        # Stage 5: Evidence bundle
        bundle = self._validator.build_evidence_bundle(artifact, validation, env_report)
        return bundle

    def run_baseline_full(self, spec: QComputeExperimentSpec) -> QComputeBaselineResult:
        """Full five-stage pipeline with policy and governance."""
        bundle = self.run_baseline(spec)

        policy = QComputeEvidencePolicy().evaluate(bundle)
        governance = QComputeGovernanceAdapter()
        core_report = governance.build_core_validation_report(bundle.validation_report, policy)
        return QComputeBaselineResult(
            environment=bundle.environment_report,
            plan_id=bundle.validation_report.plan_ref,
            artifact_id=bundle.validation_report.artifact_ref,
            bundle=bundle,
            policy=policy,
            core_validation=core_report,
        )

    def _failed_environment_bundle(
        self,
        spec: QComputeExperimentSpec,
        env_report: QComputeEnvironmentReport,
    ) -> QComputeEvidenceBundle:
        """Build a minimal evidence bundle when environment probe fails."""
        failed_plan_id = uuid.uuid4().hex[:8]
        failed_artifact_id = uuid.uuid4().hex[:8]

        artifact = QComputeRunArtifact(
            artifact_id=failed_artifact_id,
            plan_ref=failed_plan_id,
            backend_actual=spec.backend.platform,
            status="failed",
            error_message=(f"Environment probe reported unavailable backend: {env_report.status}"),
            terminal_error_type="environment_unavailable",
            shots_requested=spec.shots,
            shots_completed=0,
        )

        issues = [
            ValidationIssue(
                code="qcompute_environment_unavailable",
                message=(
                    f"QCompute environment status is {env_report.status}. "
                    f"Cannot execute experiment {spec.task_id}."
                ),
                subject=spec.task_id,
                category=ValidationIssueCategory.READINESS,
                blocks_promotion=True,
            )
        ]

        validation = QComputeValidationReport(
            task_id=spec.task_id,
            plan_ref=failed_plan_id,
            artifact_ref=failed_artifact_id,
            passed=False,
            status=QComputeValidationStatus.EXECUTION_FAILED,
            issues=issues,
            promotion_ready=False,
        )

        return QComputeEvidenceBundle(
            bundle_id=uuid.uuid4().hex[:12],
            experiment_ref=spec.task_id,
            environment_report=env_report,
            run_artifact=artifact,
            validation_report=validation,
        )
