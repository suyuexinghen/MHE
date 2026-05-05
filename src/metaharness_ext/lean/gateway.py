from __future__ import annotations

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.lean.backends import MockLeanBackend
from metaharness_ext.lean.blueprint_compiler import LeanBlueprintCompilerComponent
from metaharness_ext.lean.capabilities import CAP_LEAN_ORCHESTRATE_WORKFLOW
from metaharness_ext.lean.contracts import (
    LeanEvidenceBundle,
    LeanProvenance,
    LeanRunPlan,
    LeanTaskSpec,
)
from metaharness_ext.lean.environment import LeanEnvironmentComponent
from metaharness_ext.lean.evidence import LeanEvidenceComponent
from metaharness_ext.lean.executor import LeanExecutorComponent
from metaharness_ext.lean.proof_workspace import LeanProofWorkspaceComponent
from metaharness_ext.lean.slots import LEAN_GATEWAY_SLOT
from metaharness_ext.lean.types import LeanValidationStatus
from metaharness_ext.lean.validator import LeanValidatorComponent


class LeanGatewayComponent(HarnessComponent):
    def __init__(self, backend: MockLeanBackend | None = None) -> None:
        self._backend = backend or MockLeanBackend()
        self._environment = LeanEnvironmentComponent()
        self._blueprint_compiler = LeanBlueprintCompilerComponent()
        self._proof_workspace = LeanProofWorkspaceComponent()
        self._executor = LeanExecutorComponent(self._backend)
        self._validator = LeanValidatorComponent()
        self._evidence = LeanEvidenceComponent()

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime
        await self._environment.activate(runtime)
        await self._blueprint_compiler.activate(runtime)
        await self._proof_workspace.activate(runtime)
        await self._executor.activate(runtime)
        await self._validator.activate(runtime)
        await self._evidence.activate(runtime)

    async def deactivate(self) -> None:
        await self._evidence.deactivate()
        await self._validator.deactivate()
        await self._executor.deactivate()
        await self._proof_workspace.deactivate()
        await self._blueprint_compiler.deactivate()
        await self._environment.deactivate()
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(LEAN_GATEWAY_SLOT)
        api.declare_output("task", "LeanTaskSpec", mode="sync")
        api.provide_capability(CAP_LEAN_ORCHESTRATE_WORKFLOW)

    def prove_sorry(self, task: LeanTaskSpec) -> LeanEvidenceBundle:
        task_ref = task.target_lemma or task.target_file
        environment_report = self._environment.probe(task)
        plan = LeanRunPlan(
            plan_id=f"plan:{task_ref}",
            task_ref=task_ref,
            target_file=task.target_file,
            workspace_path=task.target_file,
            execution_params={
                "budget": task.budget,
                "attempts": 1,
                "project_root": task.project.project_root if task.project else None,
            },
        )
        artifact = self._executor.execute_plan(
            plan,
            environment_report=environment_report,
            policy=task.execution_policy,
        )
        validation = self._validator.validate_run(artifact, plan, environment_report)
        return self._evidence.build(
            task_ref=task_ref,
            environment_report=environment_report,
            validation_report=validation,
            artifacts=[artifact],
            provenance=LeanProvenance(
                execution_mode=artifact.execution_mode,
                backend=artifact.backend,
                command=["lake", "env", "lean", task.target_file]
                if artifact.execution_mode == "real_lean"
                else [],
                cwd=task.project.project_root if task.project else None,
            ),
        )

    def audit(self, task: LeanTaskSpec) -> LeanEvidenceBundle:
        task_ref = f"audit:{task.target_file}"
        environment_report = self._environment.probe(task)
        plan = LeanRunPlan(
            plan_id=f"plan:{task_ref}",
            task_ref=task_ref,
            target_file=task.target_file,
            workspace_path=None,
            execution_params={
                "audit": True,
                "budget": task.budget,
                "attempts": 1,
                "project_root": task.project.project_root if task.project else None,
            },
        )
        artifact = self._executor.execute_plan(
            plan,
            environment_report=environment_report,
            policy=task.execution_policy,
        )
        validation = self._validator.validate_run(artifact, plan, environment_report)
        validation.audit_files = [task.target_file]
        return self._evidence.build(
            task_ref=task_ref,
            environment_report=environment_report,
            validation_report=validation,
            artifacts=[artifact],
            provenance=LeanProvenance(
                execution_mode=artifact.execution_mode,
                backend=artifact.backend,
                command=["lake", "env", "lean", task.target_file]
                if artifact.execution_mode == "real_lean"
                else [],
                cwd=task.project.project_root if task.project else None,
            ),
        )

    def run_project(self, task: LeanTaskSpec) -> LeanEvidenceBundle:
        task_ref = f"project:{task.target_file}"
        environment_report = self._environment.probe(task)
        blueprint = self._blueprint_compiler.compile(task)
        artifacts = []
        validations = []
        for item in blueprint.items:
            plan = self._proof_workspace.prepare(item)
            plan.execution_params["project_root"] = (
                task.project.project_root if task.project else None
            )
            artifact = self._executor.execute_plan(
                plan,
                environment_report=environment_report,
                policy=task.execution_policy,
            )
            validation = self._validator.validate_run(artifact, plan, environment_report)
            artifacts.append(artifact)
            validations.append(validation)
            if validation.status is not LeanValidationStatus.FULLY_PROVEN:
                break
        validation = next(
            (
                report
                for report in validations
                if report.status is not LeanValidationStatus.FULLY_PROVEN
            ),
            validations[-1],
        )
        return self._evidence.build(
            task_ref=task_ref,
            environment_report=environment_report,
            validation_report=validation,
            artifacts=artifacts,
            blueprint=blueprint,
            provenance=LeanProvenance(
                execution_mode=artifacts[-1].execution_mode,
                backend=artifacts[-1].backend,
                cwd=task.project.project_root if task.project else None,
            ),
        )
