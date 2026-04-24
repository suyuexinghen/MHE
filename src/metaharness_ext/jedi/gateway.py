from __future__ import annotations

from typing import Literal

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.manifest import ComponentManifest
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.jedi.capabilities import CAP_JEDI_CASE_COMPILE
from metaharness_ext.jedi.contracts import (
    JediEnvironmentReport,
    JediExecutableSpec,
    JediLocalEnsembleDASpec,
    JediVariationalSpec,
)
from metaharness_ext.jedi.slots import JEDI_GATEWAY_SLOT
from metaharness_ext.jedi.smoke_policy import JediSmokePolicyComponent
from metaharness_ext.jedi.types import JediExecutionMode


class JediGatewayComponent(HarnessComponent):
    def __init__(self, manifest: ComponentManifest | None = None) -> None:
        self._manifest = manifest
        self._runtime: ComponentRuntime | None = None

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(JEDI_GATEWAY_SLOT)
        api.declare_output("task", "JediExperimentSpec", mode="sync")
        api.provide_capability(CAP_JEDI_CASE_COMPILE)

    def issue_task(
        self,
        *,
        task_id: str = "jedi-task-1",
        execution_mode: JediExecutionMode = "validate_only",
        binary_name: str = "qg4DVar.x",
        launcher: str = "direct",
        process_count: int | None = None,
        background_path: str | None = None,
        background_error_path: str | None = None,
        observation_paths: list[str] | None = None,
        working_directory: str | None = None,
        scientific_check: Literal["runtime_only", "rms_improves"] = "runtime_only",
        subject_id: str | None = None,
        credentials: dict[str, str] | None = None,
        claims: dict[str, str] | None = None,
        candidate_id: str | None = None,
        graph_version_id: int | None = None,
        session_id: str | None = None,
        audit_refs: list[str] | None = None,
    ) -> JediVariationalSpec:
        self._enforce_ingress_policy(
            subject_id=subject_id,
            credentials=credentials,
            claims=claims,
        )
        return JediVariationalSpec(
            task_id=task_id,
            candidate_id=candidate_id,
            graph_version_id=graph_version_id,
            session_id=session_id,
            audit_refs=list(audit_refs or []),
            executable=JediExecutableSpec(
                binary_name=binary_name,
                launcher=launcher,
                execution_mode=execution_mode,
                process_count=process_count,
            ),
            background_path=background_path,
            background_error_path=background_error_path,
            observation_paths=list(observation_paths or []),
            working_directory=working_directory,
            variational={"minimizer": {"algorithm": "RPCG", "iterations": 20}},
            output={"filename": "analysis.out"},
            final={"diagnostics": {"filename": "departures.json"}},
            test={"reference": {"filename": "reference.json"}},
            expected_diagnostics=["departures.json"],
            scientific_check=scientific_check,
        )

    def issue_smoke_task(
        self,
        environment: JediEnvironmentReport,
        *,
        task_id: str = "jedi-smoke-task-1",
        execution_mode: JediExecutionMode = "validate_only",
        background_path: str | None = None,
        observation_paths: list[str] | None = None,
        ensemble_paths: list[str] | None = None,
    ) -> JediVariationalSpec | JediLocalEnsembleDASpec:
        policy = JediSmokePolicyComponent().select_baseline(environment)
        if not policy.ready:
            raise ValueError(policy.reason)
        if policy.recommended_family == "local_ensemble_da":
            if not ensemble_paths:
                raise ValueError("local_ensemble_da smoke baseline requires ensemble_paths")
            return self.issue_local_ensemble_task(
                task_id=task_id,
                execution_mode=execution_mode,
                binary_name=policy.recommended_binary or "qgLETKF.x",
                ensemble_paths=list(ensemble_paths),
                background_path=background_path,
                observation_paths=list(observation_paths or []),
            )
        if policy.recommended_family not in {None, "variational", "hofx"}:
            raise NotImplementedError(
                f"Smoke task issuance is not implemented for {policy.recommended_family}"
            )
        return self.issue_task(
            task_id=task_id,
            execution_mode=execution_mode,
            binary_name=policy.recommended_binary or "qg4DVar.x",
            background_path=background_path,
            observation_paths=list(observation_paths or []),
        )

    def issue_local_ensemble_task(
        self,
        *,
        task_id: str = "jedi-letkf-task-1",
        execution_mode: JediExecutionMode = "validate_only",
        binary_name: str = "qgLETKF.x",
        launcher: str = "direct",
        process_count: int | None = None,
        ensemble_paths: list[str] | None = None,
        background_path: str | None = None,
        observation_paths: list[str] | None = None,
        working_directory: str | None = None,
        scientific_check: Literal["runtime_only", "ensemble_outputs_present"] = "runtime_only",
        subject_id: str | None = None,
        credentials: dict[str, str] | None = None,
        claims: dict[str, str] | None = None,
        candidate_id: str | None = None,
        graph_version_id: int | None = None,
        session_id: str | None = None,
        audit_refs: list[str] | None = None,
    ) -> JediLocalEnsembleDASpec:
        self._enforce_ingress_policy(
            subject_id=subject_id,
            credentials=credentials,
            claims=claims,
        )
        return JediLocalEnsembleDASpec(
            task_id=task_id,
            candidate_id=candidate_id,
            graph_version_id=graph_version_id,
            session_id=session_id,
            audit_refs=list(audit_refs or []),
            executable=JediExecutableSpec(
                binary_name=binary_name,
                launcher=launcher,
                execution_mode=execution_mode,
                process_count=process_count,
            ),
            ensemble_paths=list(ensemble_paths or []),
            background_path=background_path,
            observation_paths=list(observation_paths or []),
            working_directory=working_directory,
            driver={"task": "local_ensemble_da"},
            ensemble={"solver": {"algorithm": "LETKF", "iterations": 5}},
            output={"filename": "letkf.out"},
            final={"diagnostics": {"filename": "posterior.out"}},
            test={"reference": {"filename": "ensemble_reference.json"}},
            expected_diagnostics=["posterior.out"],
            scientific_check=scientific_check,
        )

    def _enforce_ingress_policy(
        self,
        *,
        subject_id: str | None,
        credentials: dict[str, str] | None,
        claims: dict[str, str] | None,
    ) -> None:
        runtime = getattr(self, "_runtime", None)
        manifest = getattr(self, "_manifest", None)
        if runtime is None or manifest is None:
            return
        runtime.require_sandbox_tier(manifest.policy.sandbox.tier)
        runtime.require_credentials(
            subject_id=subject_id,
            credentials=credentials,
            requires_subject=manifest.policy.credentials.requires_subject,
            allow_inline_credentials=manifest.policy.credentials.allow_inline_credentials,
        )
        required_claims = manifest.policy.credentials.required_claims
        if not required_claims:
            return
        present_claims = set((claims or {}).keys())
        missing = [claim for claim in required_claims if claim not in present_claims]
        if missing:
            raise ValueError("credential policy missing required claims: " + ", ".join(missing))
