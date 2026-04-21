# Meta-Harness Engineering

Meta-Harness Engineering (`MHE`) is a Python reference runtime for the Meta-Harness model. It combines a typed component SDK, manifest-driven discovery, candidate-first graph assembly, semantic validation, versioned routing, hot-swap state migration, safety gating, provenance, and optimizer scaffolding in one codebase.

The project is best understood as a **research and engineering runtime** rather than a production orchestrator. Its strongest current surfaces are:

- the typed SDK under `src/metaharness/sdk/`
- the graph/runtime core under `src/metaharness/core/`
- the XML import and validation flow under `src/metaharness/config/`
- the boot orchestrator `HarnessRuntime`
- the demo harness and CLI
- the hot-reload, identity-boundary, safety, and provenance subsystems

MHE treats the **internal graph model** as runtime authority. XML is an import/config format, not the in-memory source of truth.

## What Ships Today

The current tree includes:

- typed SDK models for ports, events, slots, capabilities, manifests, and runtime injection
- manifest loading, multi-source discovery, static validation, and dependency ordering
- a registry that tracks declarations, slot bindings, capability indexes, and graph versions
- internal graph models for nodes, edges, pending mutations, snapshots, and validation reports
- a `ConnectionEngine` that stages, validates, commits, routes, and rolls back graph snapshots
- structural XML validation and semantic graph validation
- a boot orchestrator (`HarnessRuntime`) that wires discovery, activation, handler registration, identity boundary injection, and migration adapter collection
- nine bundled core-component implementations plus an optimizer component
- hot-reload support with checkpoints, migration adapter registry, saga compensation, and observation-window evaluation
- a minimal protected identity boundary for credential separation
- safety modules for sandbox validation, A/B shadow checks, policy veto, and auto-rollback
- in-memory observability, provenance, and Merkle-anchored audit logging primitives
- optimizer search, trigger, convergence, template, and code-generation scaffolding
- bundled example manifests and example graphs
- a runnable demo harness and a small CLI
- an extensive pytest suite covering the main subsystems

## Current Maturity

MHE is intentionally **modular, testable, and explicit**, but many subsystems are still reference-grade:

- most storage and stateful services are in-memory
- the bundled demo components are intentionally simple and mostly echo-style
- the CLI is small and focused on demo, validation, and version reporting
- the hot-swap path is implemented, but its observation inputs are caller-supplied rather than fully wired to a live metrics backend
- the optimizer package is broad, but the core authority boundary remains strict: proposals only, no direct active-graph write path

That makes MHE well suited for:

- architecture experiments
- contract and manifest evolution
- routing and graph-validation work
- hot-reload protocol development
- safety-chain testing
- optimizer and provenance research
- extension prototyping

It is not yet a production control plane.

## Extension Packages

MHE ships with two domain-specific extension packages under `src/metaharness_ext/`:

### `metaharness_ext.nektar` — Nektar++ Solver Extension

A solver-specific extension that wraps Nektar++ workflows into the HarnessComponent / manifest / slot system.

Current execution chain:

```text
NektarGateway -> SessionCompiler -> XMLRenderer -> SolverExecutor -> Postprocess -> Validator
```

Key components:
- `NektarGatewayComponent` — emits `NektarProblemSpec` tasks
- `SessionCompilerComponent` — compiles problem specs into `NektarSessionPlan`
- `SolverExecutorComponent` — runs `ADRSolver` / `IncNavierStokesSolver` via subprocess
- `PostprocessComponent` — runs `FieldConvert` for format conversion and error extraction
- `NektarValidatorComponent` — validates results against exit codes, file existence, and error tolerances
- `ConvergenceStudyComponent` — performs structured convergence studies (e.g., `NUMMODES` sweeps)

Key contracts: `NektarProblemSpec`, `NektarSessionPlan`, `NektarRunArtifact`, `ConvergenceStudySpec`, `ConvergenceStudyReport`

Supported solver families: `ADR` (advection-diffusion-reaction) and `IncNS` (incompressible Navier-Stokes)

For details, see:
- `MHE/docs/wiki/meta-harness-engineer/nektar-engine-wiki/`
- `MHE/src/metaharness_ext/nektar/`

### `metaharness_ext.ai4pde` — AI4PDE Agent Extension

A scientific-agent extension for PDE-solving workflows combining team runtime, meta-harness governance, and multi-method solver capabilities.

Architecture layers:

```text
Meta Layer (AI4PDE Meta-Harness)
  -> Coordination Layer (AI4PDE Team Runtime)
    -> Runtime Layer (PDE Capability Fabric)
```

Key components:
- `PDEGatewayComponent` — issues `PDETaskRequest` with physics/geometry/data specs
- `ProblemFormulatorComponent` — formalizes PDE problems
- `MethodRouterComponent` — routes to appropriate solver families
- `SolverExecutorComponent` — executes PINN strong-form and classical hybrid solvers
- `PhysicsValidatorComponent` — validates residual, boundary conditions, and conservation
- `EvidenceManagerComponent` — bundles scientific evidence for audit

Key contracts: `PDETaskRequest`, `PDEPlan`, `PDERunArtifact`, `ValidationBundle`, `ScientificEvidenceBundle`

Supported solver families: `pinn_strong`, `dem_energy`, `operator_learning`, `pino`, `classical_hybrid`

For details, see:
- `MHE/docs/wiki/meta-harness-engineer/ai4pde-agent-wiki/`
- `MHE/src/metaharness_ext/ai4pde/`

---

## Architecture At A Glance

### 1. Components are declared, not inferred

Each component is defined by:

- a JSON manifest (`ComponentManifest`)
- a Python implementation (`HarnessComponent`)
- declarations collected through `HarnessAPI`

Manifests declare:

- `entry` import path
- contracts: inputs, outputs, events, capabilities, slots
- safety metadata
- state schema version
- dependency requirements
- runtime version, binary, and environment constraints

### 2. Discovery and boot are explicit

`HarnessRuntime` performs the main boot flow:

1. resolve manifests from discovery roots
2. apply enable/disable overrides
3. run static manifest validation
4. dependency-sort boot order
5. instantiate components and collect declarations
6. register declarations into the registry
7. inject runtime services such as identity boundary and migration adapter registry
8. activate components
9. attach declared connection handlers

Graph commit is separate from boot.

### 3. Graphs are staged before promotion

A graph enters runtime through a `PendingConnectionSet`, then moves through:

1. candidate snapshot creation
2. semantic validation
3. candidate recording
4. commit on success
5. rollback to previous committed state if needed

### 4. Routing is versioned

`ConnectionEngine` compiles committed edges into route bindings and dispatches payloads by source port. Routing modes currently include:

- `sync`
- `async`
- `event`
- `shadow`

### 5. Hot swap is state-aware

Hot swap is not just component replacement. The runtime includes:

- checkpoint capture
- migration adapter lookup
- `transform_state()` fallback
- resume into the incoming component
- optional observation-window rejection
- saga compensation on failure

### 6. Identity is a boundary, not a primary slot

The current implementation does **not** model identity as a standalone core component. Instead, it injects an `InMemoryIdentityBoundary` that:

- issues attestations
- keeps protected credentials off normal payload paths
- exposes only public identity material to ordinary component flow

### 7. Safety and provenance are layered

The repository includes separate modules for:

- sandbox validation
- A/B shadow evaluation
- policy veto
- post-commit auto-rollback
- traces and metrics
- append-only audit logging with Merkle anchoring
- PROV-style evidence structures

## Repository Layout

```text
MHE/
├── README.md
├── pyproject.toml
├── docs/
│   ├── USER_GUIDE.md
│   ├── TECHNICAL_MANUAL.md
│   ├── ROADMAP_STATUS.md
│   ├── API_STABILITY.md
│   ├── EXTENSION_GUIDE.md
│   ├── OPTIMIZER_EXTENSIONS.md
│   ├── PROTECTED_COMPONENTS.md
│   └── adr/
├── examples/
│   ├── graphs/
│   └── manifests/baseline/
├── src/metaharness/
│   ├── cli.py
│   ├── demo.py
│   ├── components/
│   ├── config/
│   ├── core/
│   ├── hotreload/
│   ├── identity/
│   ├── observability/
│   ├── optimizer/
│   ├── provenance/
│   ├── safety/
│   └── sdk/
└── tests/
```

## Requirements

Package metadata currently declares:

- Python `>=3.11`
- `pydantic>=2.12,<3`

Repository development rules currently assume:

- `ruff==0.15.6`
- Ruff target version `py313`
- pytest-based test execution

If you are working on the codebase itself, using Python 3.13 is the safest match for the current repo configuration.

## Install And Run

### Run directly from source

From the repository root:

```bash
PYTHONPATH=MHE/src python -m metaharness.cli version
```

### Editable install

```bash
pip install -e ./MHE
```

This provides the console scripts:

```bash
metaharness version
metaharness demo
metaharness-demo
```

## Quick Start

### 1. Run the minimal demo

```bash
PYTHONPATH=MHE/src python -m metaharness.demo
```

Expected shape of output:

```text
topology=minimal
graph_version=1
trace_id=trace-demo-1
task=demo task
runtime_status=runtime-ok
executor_status=executed
score=1.0
```

### 2. Run the expanded demo

```bash
PYTHONPATH=MHE/src python -m metaharness.cli demo --topology expanded --async-mode
```

The CLI emits structured JSON containing values such as:

- `gateway_payload`
- `runtime_payload`
- `plan_payload`
- `executor_payload`
- `evaluation_payload`
- `memory_record`
- `policy_record`
- `audit_event`
- `lifecycle`

### 3. Validate a graph

Structural validation only:

```bash
PYTHONPATH=MHE/src python -m metaharness.cli validate \
  MHE/examples/graphs/minimal-happy-path.xml
```

Structural and semantic validation:

```bash
PYTHONPATH=MHE/src python -m metaharness.cli validate \
  MHE/examples/graphs/minimal-expanded.xml \
  --manifests MHE/examples/manifests/baseline
```

Exit codes:

- `0` success
- `2` structural validation failure
- `3` semantic validation failure

## Demo Topologies

### Minimal

The minimal graph currently routes:

```text
Gateway -> Runtime -> Executor -> Evaluation
```

Shipped artifact:

- `examples/graphs/minimal-happy-path.xml`

### Expanded

The expanded graph currently routes:

```text
Gateway -> Runtime -> Planner -> Executor -> Evaluation
                                      └-> Memory
```

Shipped artifact:

- `examples/graphs/minimal-expanded.xml`

In the demo harness, `Policy` and `Observability` are present as control-plane helpers rather than main graph nodes in the example XML.

## Programmatic Boot Example

The demo harness is the easiest way to see the runtime in action, but the actual boot orchestrator is `HarnessRuntime`.

```python
from pathlib import Path

from metaharness.config.xml_parser import parse_graph_xml
from metaharness.core.boot import HarnessRuntime
from metaharness.core.models import PendingConnectionSet
from metaharness.sdk.discovery import ComponentDiscovery

manifest_dir = Path("MHE/examples/manifests/baseline")
graph_path = Path("MHE/examples/graphs/minimal-happy-path.xml")

runtime = HarnessRuntime(ComponentDiscovery(bundled=manifest_dir))
report = runtime.boot()

snapshot = parse_graph_xml(graph_path)
version = runtime.commit_graph(
    PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges),
    candidate_id="example",
)

print(report.booted_ids)
print(version)
```

During boot, the runtime currently injects:

- an event bus
- a shared in-memory identity boundary
- a shared migration adapter registry

If a component declares migration adapters through `HarnessAPI`, they are automatically collected into the runtime-owned hot-swap registry during boot.

## Core Concepts

### Manifest-driven components

A component is described by a manifest plus a Python implementation. The implementation declares ports and runtime hooks through `HarnessAPI`.

### Candidate-first graph model

The runtime never directly mutates the active graph. It stages a candidate, validates it, and only promotes it on success.

### Lifecycle tracking

MHE tracks components across the current lifecycle phases:

- `discovered`
- `validated_static`
- `assembled`
- `validated_dynamic`
- `activated`
- `committed`
- `failed`
- `suspended`

### Protected components

Protected behavior is expressed through safety metadata and enforced during validation and governance checks. The current validator rejects protected-slot override conflicts.

### Identity boundary

Credential-like data is intentionally kept out of ordinary payloads. Components receive sanitized identity views plus attestation references.

### Hot swap and migration

The hot-swap subsystem uses:

- `CheckpointManager`
- `MigrationAdapterRegistry`
- `HotSwapOrchestrator`
- `ObservationWindowEvaluator`
- `SagaRollback`

For already-booted components, `HotSwapOrchestrator` now prefers `runtime.migration_adapters` automatically, so callers do not need to pass the registry explicitly when swapping runtime-owned components.

## Validation Model

### Structural validation

`config/xsd_validator.py` checks XML structure and allowed values.

Examples of checks:

- expected root shape
- required attributes
- route mode values
- connection policy values

### Semantic validation

`core/validators.py` validates a candidate graph against the registry.

Current checks include:

- duplicate connection IDs
- unknown components
- unknown source and target ports
- payload mismatches
- missing required inputs
- protected slot overrides
- cycles
- orphaned components

## Development Workflow

### Run the test suite

```bash
PYTHONPATH=MHE/src pytest MHE/tests
```

### Run a focused test module

```bash
PYTHONPATH=MHE/src pytest MHE/tests/test_boot.py
PYTHONPATH=MHE/src pytest MHE/tests/test_hot_reload.py
```

### Run lint checks

```bash
ruff check MHE
```

### Run format checks

```bash
ruff format --check MHE
```

## Documentation Map

- `docs/USER_GUIDE.md` — operating guide, examples, workflows, and troubleshooting
- `docs/TECHNICAL_MANUAL.md` — internal architecture and implementation manual
- `docs/EXTENSION_GUIDE.md` — extension-oriented guidance
- `docs/OPTIMIZER_EXTENSIONS.md` — optimizer extension points
- `docs/PROTECTED_COMPONENTS.md` — protected component rules
- `docs/API_STABILITY.md` — stability expectations
- `docs/ROADMAP_STATUS.md` — tracked status against the roadmap
- `docs/adr/` — architecture decisions

## Known Limitations

The current implementation is intentionally conservative and explicit:

- most runtime stores are in-memory
- the bundled components are simple demonstration components rather than production service integrations
- the CLI focuses on demo/validate/version, not runtime administration
- the identity boundary is minimal and local-only
- hot-reload observation depends on supplied metrics/events rather than a fully integrated metrics backend
- safety and optimizer modules are real code, but still reference-grade in overall operational maturity

## Recommended Reading Order

If you are new to MHE, read in this order:

1. `README.md`
2. `docs/USER_GUIDE.md`
3. `docs/TECHNICAL_MANUAL.md`
4. `src/metaharness/cli.py`
5. `src/metaharness/demo.py`
6. `src/metaharness/core/boot.py`
7. `src/metaharness/core/connection_engine.py`
8. `src/metaharness/core/validators.py`
9. `tests/`

## Summary

MHE is a contract-first, graph-based runtime that makes routing, validation, lifecycle, state migration, and safety boundaries explicit. It is a strong foundation for Meta-Harness experimentation and engineering work, with clear separation between:

- declaration and activation
- candidate and active graph state
- data-plane routing and control-plane governance
- public payloads and protected identity material
- hot-swap orchestration and rollback
