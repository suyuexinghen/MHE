from __future__ import annotations

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.fealpy.capabilities import CAP_FEALPY_TASK_ISSUE
from metaharness_ext.fealpy.compiler import FealpyCompilerComponent
from metaharness_ext.fealpy.contracts import (
    FealpyEnvironmentReport,
    FealpyProblemSpec,
    FealpyRunArtifact,
    FealpyRunPlan,
)
from metaharness_ext.fealpy.environment import FealpyEnvironmentProbeComponent
from metaharness_ext.fealpy.executor import FealpyExecutorComponent
from metaharness_ext.fealpy.slots import FEALPY_GATEWAY_SLOT

_VALID_FAMILIES = frozenset(
    {
        "poisson",
        "stokes",
        "navier_stokes",
        "parabolic",
        "hyperbolic",
        "helmholtz",
        "curlcurl",
        "diffusion",
        "diffusion_convection",
        "diffusion_convection_reaction",
        "diffusion_reaction",
        "darcyforchheimer",
        "linear_elasticity",
        "interface_poisson",
        "surface_poisson",
        "wave",
        "allen_cahn",
        "polyharmonic",
        "quasilinear_elliptic",
        "optimal_control",
        "ion_flow",
        "dld_microfluidic_chip",
        "mgtensor_possion",
    }
)


class FealpyGatewayComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(FEALPY_GATEWAY_SLOT)
        api.declare_input("task", "FealpyProblemSpec", required=False)
        api.declare_output("task", "FealpyProblemSpec", mode="sync")
        api.provide_capability(CAP_FEALPY_TASK_ISSUE)

    def issue_task(self, spec: FealpyProblemSpec) -> FealpyProblemSpec:
        self._validate_spec(spec)
        return spec

    def compile_experiment(
        self,
        spec: FealpyProblemSpec,
        environment: FealpyEnvironmentReport | None = None,
        compiler: FealpyCompilerComponent | None = None,
    ) -> FealpyRunPlan:
        issued = self.issue_task(spec)
        compiler = compiler or FealpyCompilerComponent()
        return compiler.compile(issued, environment)

    def run_baseline(
        self,
        spec: FealpyProblemSpec,
        *,
        environment_probe: FealpyEnvironmentProbeComponent | None = None,
        compiler: FealpyCompilerComponent | None = None,
        executor: FealpyExecutorComponent | None = None,
    ) -> FealpyRunArtifact:
        issued = self.issue_task(spec)
        runtime = getattr(self, "_runtime", None)
        environment_probe = environment_probe or FealpyEnvironmentProbeComponent()
        compiler = compiler or FealpyCompilerComponent()
        executor = executor or FealpyExecutorComponent()
        for component in (environment_probe, compiler, executor):
            component._runtime = runtime
        environment = environment_probe.probe(issued)
        plan = compiler.compile(issued, environment if environment.available else None)
        return executor.execute_plan(plan, environment)

    def _validate_spec(self, spec: FealpyProblemSpec) -> None:
        if spec.pde_family not in _VALID_FAMILIES:
            raise ValueError(f"Unsupported PDE family: {spec.pde_family}")
