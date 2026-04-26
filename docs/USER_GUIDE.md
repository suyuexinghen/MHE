# MHE User Guide

This guide explains how to use the current Meta-Harness Engineering (`MHE`) implementation as it exists in this repository.

It focuses on the practical surfaces that work today:

- running the demo harness
- validating graph XML files
- understanding manifests and graph topology
- using the boot/runtime flow programmatically
- interpreting lifecycle, routing, identity, and hot-reload behavior
- troubleshooting common setup and validation issues

For internal architecture details, read `MHE/docs/wiki/meta-harness-engineer/meta-harness-wiki/11-current-technical-manual.md` after this guide.

For a cross-extension workflow that runs `AI4PDE` and `Nektar` against the same PDE problem definition and compares their outputs honestly, read `MHE/docs/wiki/meta-harness-engineer/ai4pde-agent-wiki/06-ai4pde-nektar-comparison.md`.

## 1. What MHE Is

MHE is a contract-first runtime for assembling and operating a graph of components.

At a high level, MHE works like this:

1. component manifests describe implementations and contracts
2. Python component classes declare ports, slots, handlers, and optional migration adapters
3. discovery and boot register those declarations into a runtime registry
4. a graph XML file is parsed into internal node/edge models
5. the graph is semantically validated against the registry
6. the graph is committed into the connection engine
7. payloads are routed across ports through compiled route bindings

The most important rule is:

> **the internal graph model is authoritative at runtime**

XML is not the live runtime state. XML is parsed into internal graph snapshots, and those snapshots are what the engine validates, commits, and rolls back.

## 2. What You Can Do With The Current Implementation

The current repository supports these main workflows:

- run a minimal or expanded bundled demo
- validate XML graph files structurally and semantically
- boot a runtime from manifests and commit a graph programmatically
- experiment with routing and lifecycle tracking
- declare migration adapters and use the hot-swap path
- extend the runtime with new manifests and new component implementations

The bundled components are intentionally simple, but the runtime flow around them is real.

## 3. Project Layout You Should Know

```text
MHE/
├── README.md
├── docs/
│   ├── README.md
│   ├── USER_GUIDE.md
│   ├── TEST_GUIDE.md
│   ├── blueprint/
│   ├── wiki/
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

If you are new to the project, the fastest useful reading order is:

1. `MHE/README.md`
2. `MHE/docs/USER_GUIDE.md`
3. `MHE/src/metaharness/cli.py`
4. `MHE/src/metaharness/demo.py`
5. `MHE/src/metaharness/core/boot.py`
6. `MHE/src/metaharness/core/connection_engine.py`

## 4. Environment And Installation

## 4.1 Python version

`pyproject.toml` currently declares:

- `requires-python = ">=3.11"`

The repository tooling is configured around:

- Ruff target `py313`
- `ruff==0.15.6`

If you are developing the codebase, Python 3.13 is the best match.

## 4.2 Run directly from source

From the repository root:

```bash
PYTHONPATH=MHE/src python -m metaharness.cli version
```

This is the most reliable way to run the package without depending on an installed console script.

## 4.3 Editable install

```bash
pip install -e ./MHE
```

That makes these console scripts available:

```bash
metaharness version
metaharness demo
metaharness-demo
```

## 5. First Run

## 5.1 Minimal demo

Run:

```bash
PYTHONPATH=MHE/src python -m metaharness.demo
```

Typical output shape:

```text
topology=minimal
graph_version=1
trace_id=trace-demo-1
task=demo task
runtime_status=runtime-ok
executor_status=executed
score=1.0
```

What this means:

- the runtime loaded the minimal example graph
- the graph passed validation and was committed as version `1`
- the gateway produced a task payload
- the runtime component handled that task
- the executor produced a result
- the evaluation component produced a score

## 5.2 Expanded demo

Run:

```bash
PYTHONPATH=MHE/src python -m metaharness.cli demo --topology expanded --async-mode
```

This prints JSON instead of a compact summary. It is useful when you want to inspect intermediate payloads.

Look for:

- `gateway_payload`
- `runtime_payload`
- `plan_payload`
- `executor_payload`
- `evaluation_payload`
- `memory_record`
- `policy_record`
- `audit_event`
- `lifecycle`

## 5.3 Version command

```bash
PYTHONPATH=MHE/src python -m metaharness.cli version
```

This prints the package version from the installed package metadata or source fallback.

## 6. CLI Reference

MHE currently exposes three CLI commands.

## 6.1 `demo`

Run a bundled topology.

```bash
PYTHONPATH=MHE/src python -m metaharness.cli demo --topology minimal
PYTHONPATH=MHE/src python -m metaharness.cli demo --topology expanded --async-mode
```

Options:

- `--topology {minimal,expanded}`
- `--task <text>`
- `--trace-id <id>`
- `--async-mode`

Notes:

- `minimal` is the smallest useful path
- `expanded` adds `planner` and `memory`
- `--async-mode` exercises the async dispatch path in the connection engine

## 6.2 `validate`

Validate a graph XML file.

Structural validation only:

```bash
PYTHONPATH=MHE/src python -m metaharness.cli validate \
  MHE/examples/graphs/minimal-happy-path.xml
```

Structural + semantic validation:

```bash
PYTHONPATH=MHE/src python -m metaharness.cli validate \
  MHE/examples/graphs/minimal-expanded.xml \
  --manifests MHE/examples/manifests/baseline
```

Exit codes:

- `0` validation succeeded
- `2` structural validation failed
- `3` semantic validation failed

## 6.3 `version`

```bash
PYTHONPATH=MHE/src python -m metaharness.cli version
```

## 7. Understanding The Bundled Topologies

## 7.1 Minimal topology

Source file:

- `MHE/examples/graphs/minimal-happy-path.xml`

Current route chain:

```text
Gateway -> Runtime -> Executor -> Evaluation
```

Concrete edges in the shipped XML:

- `gateway.primary.task -> runtime.primary.task`
- `runtime.primary.result -> executor.primary.task`
- `executor.primary.result -> evaluation.primary.task_result`

Use this topology when you want:

- the smallest end-to-end graph
- a fast routing sanity check
- a compact example for learning manifests and XML

## 7.2 Expanded topology

Source file:

- `MHE/examples/graphs/minimal-expanded.xml`

Current route chain:

```text
Gateway -> Runtime -> Planner -> Executor -> Evaluation
                                      └-> Memory
```

Concrete extra edges:

- `runtime.primary.result -> planner.primary.task`
- `planner.primary.plan -> executor.primary.task`
- `executor.primary.result -> memory.primary.task_result`

Use this topology when you want:

- multi-stage routing
- async side-output behavior
- a better example of lifecycle and intermediate payloads

## 7.3 Control-plane helpers in the demo

The demo harness also instantiates:

- `policy.primary`
- `observability.primary`

These are used to record decisions and audit events around the demo run, even though they are not explicit nodes in the example XML files.

## 8. Manifests And Components

## 8.1 What a manifest does

A manifest describes:

- the component name and stable identity
- the Python entrypoint (`module:Class`)
- ports and slot bindings
- safety metadata
- state schema version
- dependency requirements
- runtime version / binary / env constraints

Bundled examples live in:

- `MHE/examples/manifests/baseline/`

## 8.2 Example manifest mental model

The baseline `gateway` manifest declares:

- no input ports
- one `task` output of type `TaskRequest`
- a required `gateway.primary` slot

The baseline `runtime` manifest declares:

- one required `task` input of type `TaskRequest`
- one `result` output of type `TaskRequest`
- a required `runtime.primary` slot

The baseline `planner` and `memory` manifests show how additional intermediate and side-output components are modeled.

## 8.3 What the Python class does

The manifest points to a Python implementation. During declaration time, the class calls `HarnessAPI` to declare its runtime surface.

That is how MHE learns about:

- inputs
- outputs
- events
- capabilities
- slot bindings
- connection handlers
- migration adapters

## 9. Booting A Runtime Programmatically

The demo harness is convenient, but `HarnessRuntime` is the real boot orchestrator.

Example:

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

What `boot()` currently does:

1. discovers manifests
2. applies enable/disable overrides
3. runs static manifest validation
4. computes dependency order
5. instantiates components and collects declarations
6. registers declarations into the registry
7. injects a shared identity boundary if one is not supplied
8. injects a shared migration adapter registry if one is not supplied
9. activates components
10. registers declared connection handlers

What `commit_graph()` currently does:

1. converts a `PendingConnectionSet` into a candidate `GraphSnapshot`
2. validates it semantically
3. records the candidate in the version store
4. commits it if valid
5. loads the committed route table into the connection engine
6. advances lifecycle states for committed nodes

## 10. Runtime Services Injected During Boot

The runtime dependency object is `ComponentRuntime`.

It can carry optional services such as:

- config
- logger
- metrics
- trace store
- event bus
- graph reader
- mutation submitter
- sandbox client
- identity boundary
- migration adapter registry

The most important boot-time defaults today are:

### 10.1 Identity boundary

A shared `InMemoryIdentityBoundary` is injected by default.

This gives components a simple protected boundary for:

- issuing subject attestations
- separating sensitive credentials from ordinary payloads
- letting downstream governance code see attestation references without seeing secrets

### 10.2 Migration adapter registry

A shared `MigrationAdapterRegistry` is injected by default.

This matters because:

- components can declare migration adapters through `HarnessAPI`
- boot automatically collects those adapters into the runtime-owned registry
- hot swaps of already-booted components can reuse that registry automatically

## 11. Validation Model

MHE validates graphs in two different layers.

## 11.1 Structural validation

Structural validation checks whether the XML is well-formed according to the expected harness shape.

Examples of checks:

- root tag and high-level structure
- required component and connection attributes
- allowed route modes
- allowed connection policy values

This happens in `MHE/src/metaharness/config/xsd_validator.py`.

## 11.2 Semantic validation

Semantic validation checks whether the graph is valid against the runtime registry.

Current checks include:

- duplicate connection IDs
- unknown components
- unknown source ports
- unknown target ports
- payload mismatches
- missing required inputs
- protected slot overrides
- cycles
- orphaned components

This happens in `MHE/src/metaharness/core/validators.py`.

## 11.3 Why both layers matter

A graph can be structurally valid but semantically wrong.

Examples:

- a `from` port points to a component that does not exist
- payload names do not match declarations
- a required input is never wired
- the graph creates a disallowed cycle

That is why `validate` supports both structural-only and semantic modes.

## 12. Lifecycle And Routing

## 12.1 Lifecycle phases

The runtime tracks components across these phases:

- `discovered`
- `validated_static`
- `assembled`
- `validated_dynamic`
- `activated`
- `committed`
- `failed`
- `suspended`

The demo harness returns a lifecycle snapshot so you can inspect the committed state of each registered component.

## 12.2 Routing modes

The connection engine currently supports these route modes:

- `sync`
- `async`
- `event`
- `shadow`

Operational meaning:

- `sync` runs in order and returns results normally
- `async` can dispatch coroutine handlers through the async path
- `event` is broadcast-like routing across multiple bindings
- `shadow` swallows failures and excludes shadow results from the normal return payload

## 13. Identity Boundary Behavior

The current identity subsystem is intentionally small.

It does **not** introduce a standalone identity primary slot.

Instead, it provides a boundary service that:

- issues an `IdentityAttestation`
- exposes a safe public payload view
- stores any attached credentials privately
- lets trusted code look credentials up by `attestation_id`

What this means for ordinary users:

- normal payloads can carry `subject` and `attestation`
- sensitive credential material should not appear in standard routed payloads
- booted components that need this behavior should read it from `runtime.identity_boundary`

## 14. Hot Reload And Migration In Practice

The runtime now includes a real hot-swap path.

Main pieces:

- `CheckpointManager`
- `MigrationAdapterRegistry`
- `HotSwapOrchestrator`
- `ObservationWindowEvaluator`
- `SagaRollback`

The hot-swap path currently works like this:

1. suspend the outgoing component
2. capture a checkpoint
3. deactivate the outgoing component
4. try a registered migration adapter
5. fall back to `incoming.transform_state()` when no adapter matches
6. resume the incoming component with migrated state
7. optionally run an observation-window evaluator
8. compensate on failure

Important current behavior:

- if the components were booted through `HarnessRuntime`, `HotSwapOrchestrator` automatically prefers `runtime.migration_adapters`
- callers do not have to pass the registry explicitly for already-booted components

## 14.1 Observation window

The observation subsystem is intentionally simple today.

It expects callers to provide:

- observed metrics
- observed events
- optional extra context

Probes then accept or reject the swap.

Built-in helpers include:

- a maximum-metric threshold probe
- a forbidden-event probe

## 15. Using Domain-Specific Extensions

MHE includes two extension packages that demonstrate real solver and
agent workflows.

### 15.1 Nektar++ Extension (`metaharness_ext.nektar`)

The Nektar extension provides a full Nektar++ execution chain. After
booting the runtime with Nektar manifests, the typical workflow is:

```python
from metaharness_ext.nektar import (
    NektarGatewayComponent,
    SessionCompilerComponent,
    SolverExecutorComponent,
    PostprocessComponent,
    NektarValidatorComponent,
)
from metaharness_ext.nektar.contracts import NektarProblemSpec

# 1. Issue a problem spec
gateway = NektarGatewayComponent()
spec = gateway.issue_task("Helmholtz 2D demo", task_id="demo-1")

# 2. Compile into a session plan
compiler = SessionCompilerComponent()
plan = compiler.compile(spec)

# 3. Render XML and execute
executor = SolverExecutorComponent()
artifact = executor.execute(plan)

# 4. Postprocess
postprocessor = PostprocessComponent()
post_result = postprocessor.process(artifact)

# 5. Validate
validator = NektarValidatorComponent()
report = validator.validate(artifact, post_result)
```

Convergence studies are supported through `ConvergenceStudyComponent`:

```python
from metaharness_ext.nektar import ConvergenceStudyComponent
from metaharness_ext.nektar.contracts import ConvergenceStudySpec, NektarMutationAxis

study = ConvergenceStudyComponent()
spec = ConvergenceStudySpec(
    study_id="demo-convergence",
    task_id="demo-1",
    base_problem=problem_spec,
    axis=NektarMutationAxis(kind="num_modes", values=[4, 6, 8, 10]),
    metric_key="l2_error_u",
    convergence_rule="relative_drop",
)
report = study.run_study(spec, executor=executor, postprocessor=postprocessor, validator=validator)
```

For full Nektar extension documentation, see:
`MHE/docs/wiki/meta-harness-engineer/nektar-engine-wiki/`

For the current AI4PDE-versus-Nektar same-problem run-and-compare workflow, see:
`MHE/docs/wiki/meta-harness-engineer/ai4pde-agent-wiki/06-ai4pde-nektar-comparison.md`

### 15.2 AI4PDE Extension (`metaharness_ext.ai4pde`)

The AI4PDE extension provides a multi-layer scientific-agent runtime.
After booting, the typical workflow is:

```python
from metaharness_ext.ai4pde import PDEGatewayComponent, PDETemplate
from metaharness_ext.ai4pde.contracts import PDETaskRequest

# 1. Issue a PDE task
gateway = PDEGatewayComponent()
task = gateway.issue_task("Solve Laplace on unit square")

# 2. Select a template from the catalog
from metaharness_ext.ai4pde.templates.catalog import catalog
template = catalog.get("forward-solid-mechanics")

# 3. The method router selects a solver family
# 4. The solver executor runs the selected method
# 5. The physics validator produces a ValidationBundle
# 6. The evidence manager bundles everything into ScientificEvidenceBundle
```

For full AI4PDE extension documentation, see:
`MHE/docs/wiki/meta-harness-engineer/ai4pde-agent-wiki/`

For the current AI4PDE-versus-Nektar same-problem run-and-compare workflow, see:
`MHE/docs/wiki/meta-harness-engineer/ai4pde-agent-wiki/06-ai4pde-nektar-comparison.md`

## 16. Common Workflows

## 15.1 Validate a graph you are editing

```bash
PYTHONPATH=MHE/src python -m metaharness.cli validate \
  my-graph.xml \
  --manifests MHE/examples/manifests/baseline
```

## 15.2 Inspect demo payloads as JSON

```bash
PYTHONPATH=MHE/src python -m metaharness.cli demo \
  --topology expanded \
  --async-mode \
  --task "plan me"
```

## 15.3 Boot and commit a graph in Python

Use `HarnessRuntime`, `ComponentDiscovery`, `parse_graph_xml`, and `PendingConnectionSet` as shown earlier.

## 15.4 Study routing behavior from tests

```bash
PYTHONPATH=MHE/src pytest MHE/tests/test_engine_routing.py
```

## 15.5 Study hot reload behavior from tests

```bash
PYTHONPATH=MHE/src pytest MHE/tests/test_hot_reload.py
```

## 16. Development Commands

Run the full test suite:

```bash
PYTHONPATH=MHE/src pytest MHE/tests
```

Run a focused subset:

```bash
PYTHONPATH=MHE/src pytest MHE/tests/test_boot.py
PYTHONPATH=MHE/src pytest MHE/tests/test_hot_reload.py
PYTHONPATH=MHE/src pytest MHE/tests/test_validation.py
```

Run lint:

```bash
ruff check MHE
```

Run format check:

```bash
ruff format --check MHE
```

## 17. Troubleshooting

## 17.1 `ModuleNotFoundError: metaharness`

When running from source, use:

```bash
PYTHONPATH=MHE/src python -m metaharness.cli version
```

## 17.2 Console scripts use the wrong interpreter

Use the module form instead of the installed wrapper:

```bash
PYTHONPATH=MHE/src python -m metaharness.cli ...
PYTHONPATH=MHE/src python -m metaharness.demo
```

## 17.3 Structural validation fails

Check:

- XML syntax
- required root and child structure
- route mode values
- connection policy values
- required attributes like `id`, `from`, `to`, and `payload`

## 17.4 Semantic validation fails

Check:

- the manifest directory passed to `--manifests`
- component IDs in XML
- source and target port names
- payload names
- required input coverage
- protected slot conflicts
- unintended cycles

## 17.5 A graph validates structurally but still cannot commit

That usually means semantic validation failed. The engine only commits valid candidates.

## 17.6 A hot swap ignores a declared migration adapter

Check:

- that the component declared the adapter through `HarnessAPI.register_migration_adapter(...)`
- that boot actually ran for that component
- that the component runtime has `migration_adapters`
- that the source and target schema versions match the requested swap

## 17.7 Identity-aware behavior is missing

Check:

- whether the component was booted through `HarnessRuntime`
- whether `runtime.identity_boundary` is populated
- whether your payload code is using the boundary to issue attestations and expose sanitized payloads

## 18. What The Current Runtime Does Not Yet Try To Be

MHE today is **not**:

- a production cluster control plane
- a durable, externally replicated graph store
- a full identity and credential-management product
- a fully automated optimizer administration surface
- a fully integrated live-metrics-driven hot-reload management system

It is a strong engineering and research runtime for developing those ideas explicitly.

## 19. Frequently Asked Design Questions

## 19.1 What happens to invalid candidates?

They are recorded as rejected or non-promoted candidates in the versioning flow, but they do not advance the active graph pointer.

## 19.2 Is XML round-tripped back from runtime state?

Not today. XML is currently an import/config surface. The authoritative runtime state is the internal graph snapshot.

## 19.3 Why does `shadow` routing exist if failures are swallowed?

It is useful for non-critical parallel observation work, shadow execution, side-channel evaluation, or optional side effects that must not break the main execution path.

## 19.4 How does A/B shadow comparison work today?

The current implementation runs a baseline runner and candidate runner over supplied trial inputs and compares outputs with a comparator. By default, the comparator checks output equality.

## 19.5 What triggers an optimizer proposal to become a real commit?

The optimizer only submits proposals. Actual commit happens through `MutationSubmitter` after staging, validation, and reviewer approval.

## 19.6 What if no migration adapter exists for a hot swap?

The runtime falls back to `transform_state()` on the incoming component. If that fails, the swap fails and compensation runs.

## 19.7 Does `--trace-id` change runtime behavior?

In the current demo and CLI paths, it is mainly a correlation identifier for audit/trace-style records, not a control knob for routing or sampling.

## 19.8 If I edit XML during a demo run, will the runtime pick it up?

No. The demo parses and commits the graph at startup for that run, then continues using the in-memory committed graph.

## 20. Where To Go Next

After this guide, read:

- `MHE/docs/wiki/meta-harness-engineer/meta-harness-wiki/11-current-technical-manual.md` for internals
- `MHE/docs/wiki/meta-harness-engineer/meta-harness-wiki/10-extension-guide.md` for extension work
- `MHE/docs/wiki/meta-harness-engineer/meta-harness-wiki/02-component-sdk.md` before depending on internal APIs
- `MHE/tests/` for executable examples of intended behavior

## 20. Summary

The easiest way to succeed with MHE is to keep four ideas in mind:

1. manifests and declarations define the component surface
2. graphs are staged and validated before promotion
3. the committed internal graph is the runtime truth
4. hot swap, identity, and safety boundaries are explicit runtime services, not hidden framework magic
