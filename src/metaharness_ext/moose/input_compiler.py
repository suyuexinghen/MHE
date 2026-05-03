from __future__ import annotations

import hashlib
import json
from pathlib import Path

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.moose.capabilities import CAP_MOOSE_INPUT_COMPILE
from metaharness_ext.moose.contracts import MooseEnvironmentReport, MooseProblemSpec, MooseRunPlan
from metaharness_ext.moose.slots import MOOSE_INPUT_COMPILER_SLOT


class MooseInputCompilerComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(MOOSE_INPUT_COMPILER_SLOT)
        api.declare_input("task", "MooseProblemSpec")
        api.declare_input("environment", "MooseEnvironmentReport", required=False)
        api.declare_output("plan", "MooseRunPlan", mode="sync")
        api.provide_capability(CAP_MOOSE_INPUT_COMPILE)

    def compile(
        self,
        spec: MooseProblemSpec,
        environment: MooseEnvironmentReport | None = None,
        *,
        run_id: str | None = None,
        workspace_dir: str | None = None,
    ) -> MooseRunPlan:
        if environment is not None and not environment.available:
            raise ValueError(f"MOOSE environment unavailable: {environment.status}")

        plan_id = self._build_plan_id(spec)
        resolved_run_id = run_id or f"run-{plan_id}"
        resolved_workspace = workspace_dir or self._default_workspace(spec.task_id, resolved_run_id)
        input_source = self._render_input_source(spec)
        command = [
            spec.executable.binary_name,
            "-i",
            spec.input.input_filename,
            *spec.input.extra_args,
        ]
        if spec.input.mesh_only:
            command.append("--mesh-only")
            if spec.input.mesh_output_path:
                command.append(spec.input.mesh_output_path)

        return MooseRunPlan(
            plan_id=plan_id,
            task_id=spec.task_id,
            run_id=resolved_run_id,
            spec=spec,
            workspace_dir=resolved_workspace,
            input_filename=spec.input.input_filename,
            input_source=input_source,
            command=command,
            expected_outputs=list(spec.expected_outputs),
            graph_metadata=dict(spec.graph_metadata),
            promotion_metadata=dict(spec.promotion_metadata),
            evidence_refs=[f"moose://plan/{spec.task_id}/{plan_id}"],
        )

    def _build_plan_id(self, spec: MooseProblemSpec) -> str:
        payload = json.dumps(spec.model_dump(mode="json"), sort_keys=True)
        digest = hashlib.sha256(payload.encode()).hexdigest()[:12]
        return f"moose-{spec.task_id}-{digest}"

    def _default_workspace(self, task_id: str, run_id: str) -> str:
        return f".runs/moose/{task_id}/{run_id}"

    def _render_input_source(self, spec: MooseProblemSpec) -> str:
        source = self._load_input_source(spec)
        rendered = source
        for key, value in sorted(spec.parameters.items()):
            rendered = rendered.replace(f"{{{{{key}}}}}", self._render_value(value))
        return rendered

    def _load_input_source(self, spec: MooseProblemSpec) -> str:
        if spec.input.mode == "file":
            return Path(spec.input.input_path or "").read_text()
        return spec.input.inline_source or ""

    def _render_value(self, value: object) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        return str(value)
