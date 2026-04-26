# Meta-Harness Extension Guide

This guide walks through the minimum steps required to add a new
component, template, or connection handler to an existing Meta-Harness
deployment. It complements `USER_GUIDE.md`, which focuses on running
and operating the engine.

## 1. Add a Custom Component

Every custom component follows the same skeleton:

1. Subclass `metaharness.sdk.base.HarnessComponent`.
2. Implement the three required hooks (`declare_interface`, `activate`,
   `deactivate`) and, if useful, `export_state` / `import_state` /
   `transform_state` / `suspend` / `resume`.
3. Publish a manifest JSON describing the component's contracts.

### 1.1 Component module

```python
# my_plugin/my_runtime.py
from __future__ import annotations

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime


class MyRuntimeComponent(HarnessComponent):
    """A small example runtime that counts task requests."""

    def __init__(self) -> None:
        self.count = 0
        self._runtime: ComponentRuntime | None = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot("runtime.primary")
        api.declare_input("task", "TaskRequest")
        api.declare_output("result", "TaskRequest", mode="sync")

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None
```

### 1.2 Manifest

```json
{
  "id": "my-runtime",
  "name": "my-runtime",
  "version": "0.1.0",
  "kind": "core",
  "entry": "my_plugin.my_runtime:MyRuntimeComponent",
  "harness_version": ">=0.1.0",
  "contracts": {
    "inputs": [{"name": "task", "type": "TaskRequest", "required": true}],
    "outputs": [{"name": "result", "type": "TaskRequest", "mode": "sync"}],
    "events": [],
    "provides": [],
    "requires": [],
    "slots": [{"slot": "runtime.primary", "binding": "primary", "required": true}]
  }
}
```

Place the manifest under one of the four discovery roots
(`bundled`, `templates`, `market`, or `custom`). The runtime picks the
highest-priority copy when the same `id` appears in multiple roots.

### 1.3 Wire into a graph

Edit the graph XML (`examples/graphs/*.xml`) and reference the new
component:

```xml
<Component id="my-runtime.primary" type="Runtime" impl="my_plugin.my_runtime" version="0.1.0" />
```

Then add the connections that reference its input and output ports. The
`ConnectionEngine` validates the graph during staging, so typos or
type mismatches raise immediately.

## 2. Register a Connection Handler

Connection handlers are functions that turn an inbound payload into an
outbound dispatch. They are registered during `declare_interface`:

```python
def declare_interface(self, api: HarnessAPI) -> None:
    api.bind_slot("runtime.primary")
    api.declare_input("task", "TaskRequest")
    api.register_connection_handler("task", self._on_task)

async def _on_task(self, payload: object) -> object:
    self.count += 1
    return payload
```

Connection handlers are eligible for hot-swap: the
`HotSwapOrchestrator` takes care of draining in-flight handlers before
replacing the component.

## 3. Add a Template

Templates are parameterised component definitions. Register them with
`TemplateRegistry` and drive instantiation through `SlotFillingEngine`:

```python
from metaharness.optimizer.templates.registry import (
    ComponentTemplate,
    TemplateRegistry,
)
from metaharness.optimizer.templates.slots import SlotFillingEngine

registry = TemplateRegistry()
registry.register(
    ComponentTemplate(
        template_id="pooled-runtime",
        manifest=manifest,
        slots={"pool_size": "concurrent workers"},
        defaults={"pool_size": 4},
    )
)

engine = SlotFillingEngine()
manifest, bindings = engine.instantiate(
    registry.get("pooled-runtime"),
    {"pool_size": 16},
)
```

The synthesised manifest can then be handed to the runtime's discovery
pipeline or streamed through `CodegenPipeline` to produce on-disk
artifacts.

## 4. Extend the Optimizer

See `docs/OPTIMIZER_EXTENSIONS.md` for the full list of extension
points. In practice you will most often:

- provide a custom `proposer` / `evaluator` to `OptimizerComponent`;
- register triggers with `LayeredTriggerSystem`;
- register fitness evaluators against `FitnessEvaluator`.

## 5. Safety-Chain Integration

Every custom extension should obey the protected-component contract
defined in `docs/PROTECTED_COMPONENTS.md`. In practice:

- Do not attempt to mutate `Policy` or `Observability` slots.
- Do not bypass `MutationSubmitter` when committing graph changes.
- Register any dangerous operations against the sandbox tier selector
  so they run under the mandated isolation level.

## 6. Packaging

Publish your plugin as a standard Python package. The discovery loader
imports your module by its fully-qualified name, so the package must
be on `sys.path` at runtime. There is no plugin-entrypoint plumbing
required; discovery is driven entirely by manifest JSON files.

## 7. Domain-Specific Extension Examples

The repository includes two fully worked domain-specific extensions that
illustrate how the patterns above are applied in practice.

### 7.1 `metaharness_ext.nektar` — Nektar++ Solver Extension

The Nektar extension demonstrates a linear solver pipeline where each
stage is a separate component with typed contracts.

**Component chain:**

```text
NektarGateway -> SessionCompiler -> SolverExecutor -> Postprocess -> Validator
```

**Key design choices:**

- `NektarProblemSpec` and `NektarSessionPlan` are Pydantic contracts that
carry solver-family-specific validation (e.g., ADR problems require
`NektarAdrEqType`, IncNS problems require `NektarIncnsEqType`).
- `SessionCompilerComponent` transforms the problem spec into an executable
plan, including solver binary selection (`ADRSolver` vs `IncNavierStokesSolver`).
- `xml_renderer` renders the plan into Nektar++ session XML without
allowing arbitrary XML editing — the renderer is the only place that
knows the XML schema.
- `SolverExecutorComponent` runs the solver via subprocess, discovers
output files (`.fld`, `.chk`), and extracts error norms and step metrics
from the log.
- `PostprocessComponent` runs `FieldConvert` for format conversion,
error evaluation (`-e`), and modular post-processing (`-m`).
- `NektarValidatorComponent` produces a pass/fail judgment based on exit
code, field file existence, L2 error norms, and IncNS convergence metrics.
- `ConvergenceStudyComponent` (added recently) consumes the analyzers
layer to perform structured convergence studies such as `NUMMODES` sweeps.

**Capabilities used:**

- `nektar.compile.case`
- `nektar.solver.adr`
- `nektar.solver.incns`
- `nektar.postprocess.fieldconvert`
- `nektar.validation.check`
- `nektar.study.convergence`

**Protected slots:** `validator.primary` is the only protected slot in
the baseline nektar topology.

For full documentation, see:
- `MHE/docs/wiki/meta-harness-engineer/nektar-engine-wiki/`
- `MHE/src/metaharness_ext/nektar/`

### 7.2 `metaharness_ext.ai4pde` — AI4PDE Agent Extension

The AI4PDE extension demonstrates a multi-layer scientific-agent runtime
built on top of the Meta-Harness SDK.

**Architecture layers:**

```text
Meta Layer (AI4PDE Meta-Harness)
  -> Coordination Layer (AI4PDE Team Runtime)
    -> Runtime Layer (PDE Capability Fabric)
```

**Key design choices:**

- `PDEGatewayComponent` issues `PDETaskRequest` objects that carry
physics specs, geometry specs, data specs, and deliverables.
- `ProblemFormulatorComponent` formalizes raw task requests into
structured PDE problems.
- `MethodRouterComponent` selects solver families (`pinn_strong`,
`classical_hybrid`, etc.) based on problem characteristics.
- Multiple solver executors handle different method families:
`pinn_strong.py` for physics-informed neural networks, `classical_hybrid.py`
for classical solvers.
- `PhysicsValidatorComponent` validates residuals, boundary conditions,
and conservation properties.
- `EvidenceManagerComponent` bundles scientific evidence into
`ScientificEvidenceBundle` for audit and replay.
- `PDETemplate` in `templates/catalog.py` provides a template library
for common PDE problem families (forward solid mechanics, forward fluid
mechanics, etc.) with status tracking (`DRAFT` -> `CANDIDATE` -> `STABLE`
-> `RETIRED`).

**Capabilities used:**

- `ai4pde.solver.pinn_strong`
- `ai4pde.solver.reference_baseline`
- `ai4pde.validation.residual`
- `ai4pde.validation.boundary`
- `ai4pde.evidence.bundle`

**Protected slots:** `evidence_manager.primary`, `observability_hub.primary`,
`policy_guard.primary`, and `reference_solver.primary` are all protected
in the AI4PDE baseline topology.

For full documentation, see:
- `MHE/docs/wiki/meta-harness-engineer/ai4pde-agent-wiki/`
- `MHE/src/metaharness_ext/ai4pde/`
