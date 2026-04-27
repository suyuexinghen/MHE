from __future__ import annotations

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.octave.capabilities import CAP_OCTAVE_TASK_ISSUE
from metaharness_ext.octave.contracts import (
    OctaveEnvironmentReport,
    OctaveExperimentSpec,
    OctaveRunArtifact,
    OctaveRunPlan,
)
from metaharness_ext.octave.environment import OctaveEnvironmentProbeComponent
from metaharness_ext.octave.executor import OctaveExecutorComponent
from metaharness_ext.octave.script_compiler import OctaveScriptCompilerComponent
from metaharness_ext.octave.slots import OCTAVE_GATEWAY_SLOT


class OctaveGatewayComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(OCTAVE_GATEWAY_SLOT)
        api.declare_input("experiment_spec", "OctaveExperimentSpec")
        api.declare_output("task", "OctaveExperimentSpec", mode="sync")
        api.provide_capability(CAP_OCTAVE_TASK_ISSUE)

    def issue_task(self, spec: OctaveExperimentSpec) -> OctaveExperimentSpec:
        self._validate_spec(spec)
        return spec

    def compile_experiment(
        self,
        spec: OctaveExperimentSpec,
        environment: OctaveEnvironmentReport | None = None,
        compiler: OctaveScriptCompilerComponent | None = None,
    ) -> OctaveRunPlan:
        issued = self.issue_task(spec)
        compiler = compiler or OctaveScriptCompilerComponent()
        return compiler.compile(issued, environment)

    def run_baseline(
        self,
        spec: OctaveExperimentSpec,
        *,
        environment_probe: OctaveEnvironmentProbeComponent | None = None,
        compiler: OctaveScriptCompilerComponent | None = None,
        executor: OctaveExecutorComponent | None = None,
    ) -> OctaveRunArtifact:
        issued = self.issue_task(spec)
        runtime = getattr(self, "_runtime", None)
        environment_probe = environment_probe or OctaveEnvironmentProbeComponent()
        compiler = compiler or OctaveScriptCompilerComponent()
        executor = executor or OctaveExecutorComponent()
        for component in (environment_probe, compiler, executor):
            component._runtime = runtime
        environment = environment_probe.probe(issued)
        plan = compiler.compile(issued, environment if environment.available else None)
        return executor.execute_plan(plan, environment)

    def _validate_spec(self, spec: OctaveExperimentSpec) -> None:
        if spec.family not in {"script_run", "function_eval", "numeric_benchmark"}:
            raise ValueError(f"Unsupported Octave family: {spec.family}")
        if spec.executable.binary_name != "octave-cli":
            raise ValueError("Octave gateway only supports octave-cli")
        if any(arg for arg in ("--gui", "--force-gui") if arg in spec.executable.env.values()):
            raise ValueError("GUI Octave execution is not supported")
        if not spec.expected_outputs:
            raise ValueError("Octave tasks must declare expected outputs")
        if spec.script.mode == "function" and spec.family == "script_run":
            raise ValueError("function mode requires function_eval or numeric_benchmark family")
