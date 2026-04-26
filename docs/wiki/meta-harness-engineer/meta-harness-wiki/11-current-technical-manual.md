# MHE Technical Manual

This manual describes the current Meta-Harness Engineering (`MHE`) implementation as an engineering system.

It is intentionally implementation-aligned. Where the broader Meta-Harness wiki describes a larger target architecture, this manual documents what the code in `MHE/src/metaharness/` actually does today.

## 1. Scope And Reading Strategy

This manual is for readers who want to understand:

- how boot, registration, graph commit, and routing work
- how safety gates are structured in code
- how hot swap, migration adapters, and rollback work
- how the optimizer is constrained
- how provenance, counter-factual analysis, and Merkle audit logging are implemented
- what the runtime does **not** currently do

If you are new to MHE, read in this order:

1. `MHE/README.md`
2. `MHE/docs/USER_GUIDE.md`
3. `MHE/docs/wiki/meta-harness-engineer/meta-harness-wiki/11-current-technical-manual.md`
4. `MHE/src/metaharness/core/boot.py`
5. `MHE/src/metaharness/core/connection_engine.py`
6. `MHE/src/metaharness/core/validators.py`

## 2. System Overview

At a high level, the current runtime is built from a set of explicit subsystems:

- **SDK**: manifests, contracts, lifecycle, runtime injection, declaration API
- **Discovery/Loader**: manifest resolution, static validation, dependency ordering, instantiation
- **Registry**: declared component surfaces, slot and capability indexes, graph pointers
- **Graph Core**: nodes, edges, snapshots, candidate sets, validation reports, lifecycle, versions
- **Connection Engine**: candidate staging, commit, rollback, route-table compilation, emit/emit_async
- **Boot Orchestrator**: `HarnessRuntime`
- **Safety**: sandbox validation, A/B shadow testing, policy veto, auto-rollback, sandbox-tier selection
- **Hot Reload**: checkpoint, migration adapters, swap orchestration, observation window, saga compensation
- **Identity Boundary**: protected attestation and credential separation
- **Observability/Provenance**: metrics, traces, trajectory storage, PROV-like evidence, Merkle audit log
- **Optimizer**: triggers, fitness, convergence, search phases, Bayesian/RL add-ons, proposal submission
- **Extension Packages**: domain-specific component sets (`metaharness_ext.nektar`, `metaharness_ext.ai4pde`)

The runtime is modular and explicit, but still mostly in-memory.

## 3. Boot, Declaration, And Runtime Injection

## 3.1 Boot orchestrator

The composition root is `HarnessRuntime` in `MHE/src/metaharness/core/boot.py`.

Its main boot flow is:

1. resolve manifests from the configured discovery roots
2. filter manifests with enable/disable overrides
3. run static manifest validation
4. resolve dependency order
5. instantiate each component and collect declarations through `HarnessAPI`
6. register declarations into the registry
7. collect declared migration adapters into a shared runtime registry
8. activate components with a `ComponentRuntime`
9. register declared connection handlers with the `ConnectionEngine`
10. record lifecycle transitions

Boot does **not** commit a graph. Graph commit is a separate explicit operation.

## 3.2 Discovery model

`ComponentDiscovery` supports four source categories:

- bundled
- template
- market
- custom

Higher-priority sources override lower-priority ones by manifest identity. In current code, this is a straightforward source-priority override model rather than a merge model.

## 3.3 Static manifest validation

Static validation currently checks:

- whether `harness_version` is compatible with the running runtime version
- whether required binaries exist on `PATH`
- whether required environment variables are set

This is separate from semantic graph validation.

## 3.4 Runtime injection

`ComponentRuntime` is the runtime dependency carrier. Fields are optional so the SDK can be used in small tests, but boot injects shared services where appropriate.

Important injected services today:

- `event_bus`
- `identity_boundary`
- `migration_adapters`

The runtime may also carry metrics, trace store, mutation submitter, sandbox client, and other services, but these are not always fully wired in the current default boot path.

## 4. Graph Model And Runtime Authority

## 4.1 Internal graph authority

The central architecture rule is:

> XML is an external representation; the internal graph snapshot is the runtime truth.

`parse_graph_xml()` turns XML into nodes and edges, and the engine operates on `GraphSnapshot` / `PendingConnectionSet`, not on XML strings.

This matters because:

- validation operates on typed graph structures
- commit and rollback operate on stored snapshots
- mutation and hot-reload logic can work on graph state without treating XML as the live source of truth

## 4.2 Main graph types

The main runtime graph types are:

- `ComponentNode`
- `ConnectionEdge`
- `PendingMutation`
- `PendingConnectionSet`
- `ValidationIssue`
- `ValidationReport`
- `GraphSnapshot`
- `GraphState`

Together they represent staged graph intent, committed graph state, and the validation surface between them.

## 4.3 Candidate-first mutation model

The graph commit model is candidate-first:

1. candidate graph snapshot is built
2. semantic validation runs
3. candidate is recorded in the version store
4. active graph is promoted only if validation succeeds

### What happens to invalid candidates?

Invalid candidates are **recorded but not promoted**.

There are two relevant paths:

- `ConnectionEngine.commit(...)` stores a candidate record even when `report.valid` is false, but does not advance the active graph
- `ConnectionEngine.discard_candidate(...)` stores a rejected candidate explicitly and clears the registry’s `candidate_graph`

So invalid candidates are **inspectable as candidate records**, not silently lost. In the current implementation, this is inspection-oriented state, not a full replay product surface.

## 4.4 Version lifecycle

`GraphVersionStore` maintains:

- current candidate
- active graph version
- rollback target version
- archived snapshots

The rollback target is the **previous committed active graph**, not an arbitrary historical version. Older versions can be archived and later rehydrated when needed.

## 5. Semantic Validation

The semantic validator checks a candidate graph against the live registry.

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

This validator is registry-aware. It depends on declarations having been booted and registered first.

## 6. Connection Engine And Routing

## 6.1 Responsibilities

`ConnectionEngine` has two jobs:

- manage candidate/active graph state transitions
- route payloads over the committed graph’s compiled route table

## 6.2 Route bindings

Committed edges are compiled into `RouteBinding` objects containing:

- connection ID
- target port
- payload type
- route mode
- connection policy

## 6.3 Current routing modes

The engine currently supports:

- `sync`
- `async`
- `event`
- `shadow`

### Practical meaning of `shadow`

`shadow` routes still execute handlers, but:

- failures are swallowed
- shadow results are omitted from the normal returned results

The practical use case is **non-critical parallel observation or side-effect work**, such as candidate shadow execution, monitoring, or non-blocking experimental processing. Logging-like or side-channel evaluation is a good mental model.

## 7. XML, Round-Trip, And Runtime Truth

## 7.1 Is XML one-way today?

Effectively, yes.

The current runtime parses XML into internal graph state, but there is no full graph-to-XML round-trip/export pipeline that keeps XML synchronized with optimizer-driven graph changes.

### What this means in practice

- XML is currently an import/config artifact
- committed graph state lives in internal snapshots
- optimizer- or mutation-driven changes operate on internal graph structures
- if you need persisted external representation after mutation, that would require an explicit export layer

So the current model is best understood as **XML-in, internal graph runtime, no automatic XML-out**.

## 7.2 Does changing XML on disk affect a running demo?

No.

The demo harness reads and parses the XML during graph commit at startup for that run. There is no file watcher, reparse loop, or automatic reload path tied to disk changes during execution.

## 8. Safety Chain

The repository contains a four-level safety structure:

1. sandbox validation
2. A/B shadow testing
3. policy veto
4. post-commit auto-rollback

## 8.1 Sandbox validation

The sandbox validator is the first safety gate. It evaluates proposals structurally and semantically in a sandbox-oriented validation step.

## 8.2 A/B shadow testing

`ABShadowTester` compares a baseline runner and a candidate runner over one or more trials.

Current behavior is simple and explicit:

- if `context["trials"]` exists, those are the trial inputs
- otherwise the whole context is treated as one trial
- both runners are executed for each trial
- a comparator decides whether they match

### What is actually compared?

By default, it is **output equality**.

The default comparator returns success only when `baseline == candidate`. If they differ, the tester records a divergence.

So current A/B shadow behavior is closer to **behavioral output comparison** than to structural diffing.

## 8.3 Policy veto

The policy gate is the governance review step. It can allow or reject a proposal, and protected-component rules feed into this layer.

## 8.4 Auto-rollback

`AutoRollback` is a post-commit health check layer.

Important design detail:

- `evaluate()` itself allows proposals through
- actual rollback decisions happen in `check()`

### What counts as a failed health probe?

Current implementation is **probe-defined**.

A probe is a callable that returns:

- `healthy: bool`
- `reason: str`

If any registered probe returns `healthy == False`, auto-rollback attempts a rollback.

### What does it roll back to?

It rolls back to the runtime’s stored `rollback_graph_version`, which is the **prior committed active graph**.

If rollback cannot be performed, the event is still recorded and rejection is returned, but `to_version` can be `None`.

## 8.5 Sandbox tiers

The sandbox-tier module currently defines three isolation tiers:

- `v8_wasm`
- `gvisor`
- `firecracker`

These are ordered by increasing isolation strength.

### How does tier selection work?

Selection is handled by `RiskTierSelector`.

Current risk levels:

- `low`
- `medium`
- `high`
- `critical`

Default mapping:

- `low -> v8_wasm`
- `medium -> gvisor`
- `high -> firecracker`
- `critical -> firecracker`

The selector finds adapters whose tier rank meets or exceeds the minimum floor and picks the least-cost eligible tier.

### Important limitation

The default fallback adapters in the current tree are in-process adapters. The tier structure exists, but it is not yet a hardened security boundary by itself.

## 9. Identity Boundary

The corrected architecture does not model identity as a standalone primary component.

Instead, it uses an injected boundary object: `InMemoryIdentityBoundary`.

This boundary can:

- issue a subject identity and attestation
- expose a sanitized payload view
- retain any sensitive credential material privately
- return stored credentials only through explicit attestation lookup

This is a minimal but important control-plane separation.

## 10. Hot Reload, State Migration, And Rollback

## 10.1 Main pieces

The hot-reload subsystem includes:

- `CheckpointManager`
- `MigrationAdapterRegistry`
- `HotSwapOrchestrator`
- `ObservationWindowEvaluator`
- `SagaRollback`

## 10.2 Current swap flow

Current swap flow is roughly:

1. suspend outgoing component
2. capture checkpoint
3. deactivate outgoing component
4. migrate state
5. resume incoming component
6. optionally evaluate observation window
7. compensate on failure

## 10.3 What is the drain protocol?

In the current implementation, there is **no orchestrator-level queue-drain protocol**.

The swap code does not inspect or drain pending event queues itself. Any draining behavior would have to live inside the component’s own `suspend()` implementation.

So the current answer is:

- not “drain until empty” at the framework level
- not “drain with timeout” at the framework level
- only whatever the component itself does when `suspend()` is called

## 10.4 Migration adapter selection

`MigrationAdapterRegistry` supports:

- exact type/version matches
- version wildcards (`None`)
- family-level fallback
- wildcard type fallback

## 10.5 What if no migration adapter exists?

It is **not immediately a hard error**.

Current behavior is:

1. try to resolve a registered adapter
2. if none exists, fall back to `incoming.transform_state(old_state, delta)`
3. if that fallback fails, the swap fails and saga compensation runs

So no adapter is acceptable **only if the component-level fallback can handle the migration**.

## 10.6 Runtime-owned migration registry

Recent integration work now makes this flow smoother:

- boot injects a shared migration registry into component runtimes
- declarations collected during boot automatically register migration adapters
- `HotSwapOrchestrator` defaults to `runtime.migration_adapters` when swapping already-booted components

That means caller code does not need to pass a registry explicitly for typical runtime-owned swaps.

## 10.7 Observation window

`ObservationWindowEvaluator` is intentionally small.

It accepts caller-supplied:

- metrics
- events
- optional context

Probes produce pass/fail decisions with reasons and evidence.

Built-in helpers include:

- a maximum-metric threshold probe
- a forbidden-event probe

## 11. Optimizer, Proposal Authority, And Search

## 11.1 Authority boundary

The optimizer is explicitly **proposal-only**.

It may:

- observe
- propose
- evaluate
- submit

It may **not** directly:

- write the active graph
- call the connection engine commit path directly
- bypass governance review

## 11.2 Who actually triggers commit?

Actual graph promotion happens through `MutationSubmitter.submit()`:

1. stage proposal into a candidate graph
2. ask governance reviewer for decision
3. commit only if the decision is `allow`

So the commit trigger is not “optimizer alone”; it is **submission + validation + reviewer approval**.

### Is human review required?

Not always.

The current code allows automated governance by reviewer callable. Human review is one possible reviewer strategy, but the default behavior is simply “allow valid staged graphs.”

## 11.3 Search phases A/B/C

The optimizer package contains three independent search engines:

- **Phase A**: local parameter search
- **Phase B**: topology/template neighborhood search
- **Phase C**: constrained multi-step synthesis

These are **composable**, not mutually exclusive.

Current code does not impose one mandatory global cycle like “A then B then C.” A caller can use one, combine several, or orchestrate them externally.

## 11.4 Bayesian vs RL

### Bayesian optimizer

Use Bayesian search when:

- the action space is small and discrete
- you want a simple exploration/exploitation tradeoff
- you want a lightweight chooser without extra policy-learning complexity

### RL enhancement

Use RL enhancement when:

- you want a fast-adapting preference model
- you want a softmax-style policy layered on top of discrete candidate selection
- you want to update action preference weights from observed rewards

### What is the RL action space?

It is a **discrete set of hashable action identifiers**, not a continuous control surface.

In practice this maps naturally onto candidate mutation choices, such as action IDs or optimizer candidate actions.

## 12. Observability, Provenance, And Counter-Factual Diagnosis

## 12.1 Observability surface

The current codebase includes:

- in-memory metrics
- trace/span collection
- trajectory grouping
- simple component-level observability helpers

`trace_id` is primarily a **correlation field** today.

In the demo path, it is passed into `ObservabilityComponent.record_event(...)` and echoed in results. It does not currently drive sampling or routing behavior.

## 12.2 Provenance surface

The provenance subsystem includes:

- PROV-like entity/activity/agent structures
- relation recording
- append-only audit logging
- Merkle anchoring

## 12.3 Counter-factual diagnosis

Current counter-factual diagnosis is implemented as a **pruned-graph re-evaluation** technique.

Mechanism:

1. start with a provenance graph
2. remove one target node plus its connected relations
3. run a caller-supplied evaluator on the pruned graph
4. compare the score against the baseline score

So the current mechanism is not “replay the whole runtime with different inputs.” It is closer to:

- “what changes if this evidence or provenance node did not exist?”

It is a graph-level counter-factual utility, not a full runtime replay engine.

## 12.4 Merkle audit verification

There is verification code, but no standalone CLI tool for it.

Current verification support exists as library methods:

- `MerkleTree.proof_for(...)`
- `MerkleTree.verify(...)`
- `AuditLog.verify(record)`

So today the Merkle chain is useful for:

- tamper detection
- proof verification inside code or tests

But not yet through a dedicated end-user verification CLI.

## 13. Trace IDs And Demo Behavior

## 13.1 What `--trace-id` does today

In current demos and CLI runs, `trace_id` is mainly used for:

- audit-event correlation
- observable output grouping
- trace/trajectory-style identifiers where those subsystems are used

It does **not** currently change:

- sampling rates
- route selection
- graph behavior
- commit behavior

## 13.2 XML changes during a running demo

The runtime does not watch the XML file after startup.

The demo harness:

- selects a graph path
- parses that XML during `_commit_graph()`
- commits the resulting internal snapshot
- then runs against the in-memory committed graph

So editing the XML file on disk while the demo is running does not alter the already-committed runtime graph.

## 14. Testing And Evidence Sources

The test suite under `MHE/tests/` is an important companion to this manual.

High-value test modules include:

- `MHE/tests/test_boot.py`
- `MHE/tests/test_validation.py`
- `MHE/tests/test_hot_reload.py`
- `MHE/tests/test_safety_pipeline.py`
- `MHE/tests/test_identity_boundary.py`
- `MHE/tests/test_provenance.py`
- `MHE/tests/test_optimizer_search.py`
- `MHE/tests/test_optimizer_templates.py`

If you want to understand intended behavior, read tests alongside the implementation.

## 15. Limits Of The Current Implementation

The codebase is already rich enough to support real engineering experiments, but several boundaries are important:

- most stateful services are in-memory
- there is no automatic graph-to-XML persistence path
- the sandbox-tier abstraction is stronger than the default shipped adapters
- the demo components are intentionally lightweight
- the hot-swap framework does not yet provide a centralized drain protocol
- provenance counter-factual analysis is graph-pruning based, not a full execution replay system
- Merkle verification is library-level rather than productized as a CLI tool

## 16. FAQ Mapping

This manual is designed to answer these recurring questions directly:

- what happens to invalid candidates
- whether XML is one-way or round-trippable
- why `shadow` mode exists
- how A/B shadow testing actually compares outputs
- what auto-rollback means in code
- what sandbox tiers exist and how they are selected
- who actually commits optimizer proposals
- whether search phases A/B/C are exclusive
- when to use Bayesian vs RL search
- what counter-factual diagnosis means today
- how Merkle verification works today
- whether hot swap drains messages centrally
- what happens when no migration adapter exists
- what `trace_id` affects
- whether XML changes on disk affect a running demo

## 17. Extension Packages

The repository includes two domain-specific extension packages that
demonstrate how the core runtime is used for real solver and agent
workflows.

### 17.1 `metaharness_ext.nektar`

A Nektar++ solver extension with a linear execution chain:

```text
NektarGateway -> SessionCompiler -> SolverExecutor -> Postprocess -> Validator
```

**Key technical points:**

- Contracts (`NektarProblemSpec`, `NektarSessionPlan`, etc.) enforce
  solver-family-specific validation at the Pydantic level.
- `SessionCompilerComponent` translates problem specs into executable
  plans with correct solver binary mapping (`ADR` → `ADRSolver`,
  `IncNS` → `IncNavierStokesSolver`).
- `xml_renderer` is the single place that knows the Nektar++ session
  XML schema; no ad-hoc XML editing is allowed elsewhere.
- `SolverExecutorComponent` extracts structured metrics from solver
  logs (steps, CPU time, wall time, L2/Linf errors, IncNS convergence).
- `analyzers.py` provides a shared analysis layer (`parse_solver_log`,
  `parse_filter_outputs`, `summarize_reference_error`) consumed by both
  the validator and the `ConvergenceStudyComponent`.
- `ConvergenceStudyComponent` performs structured parameter sweeps
  (currently `num_modes`) and produces `ConvergenceStudyReport` with
  observed convergence order, drop ratios, and recommendations.

**Slots:** `nektar_gateway.primary`, `session_compiler.primary`,
`solver_executor.primary`, `postprocess.primary`, `validator.primary`,
`convergence_study.primary`

**Protected slots:** `validator.primary`

### 17.2 `metaharness_ext.ai4pde`

An AI4PDE scientific-agent extension with a three-layer architecture:

```text
Meta Layer (AI4PDE Meta-Harness)
  -> Coordination Layer (AI4PDE Team Runtime)
    -> Runtime Layer (PDE Capability Fabric)
```

**Key technical points:**

- `PDEGatewayComponent` issues `PDETaskRequest` objects carrying physics,
  geometry, data, and deliverable specs.
- `MethodRouterComponent` selects solver families based on problem
  characteristics (`pinn_strong`, `classical_hybrid`, `operator_learning`,
  etc.).
- Solver executors live under `executors/` and handle specific method
  families without interfering with each other.
- `PhysicsValidatorComponent` produces `ValidationBundle` with residual
  metrics, boundary-condition metrics, and a `NextAction` recommendation.
- `EvidenceManagerComponent` produces `ScientificEvidenceBundle` with
  artifact hashes, provenance references, and baseline metadata.
- `templates/catalog.py` provides a template library (`PDETemplate`)
  with status tracking (`DRAFT` → `CANDIDATE` → `STABLE` → `RETIRED`).

**Slots:** `pde_gateway.primary`, `problem_formulator.primary`,
`method_router.primary`, `solver_executor.primary`,
`physics_validator.primary`, `evidence_manager.primary`,
`reference_solver.primary`, `experiment_memory.primary`,
`knowledge_adapter.primary`, `asset_memory.primary`,
`observability_hub.primary`, `policy_guard.primary`

**Protected slots:** `evidence_manager.primary`,
`observability_hub.primary`, `policy_guard.primary`,
`reference_solver.primary`

## 18. Summary

MHE is a clear, explicit runtime with strong separation between:

- declarations and activation
- candidate and active graph state
- data-plane routing and control-plane governance
- public payload flow and protected identity material
- hot-swap orchestration and rollback
- audit/provenance evidence and runtime behavior
- core runtime and domain-specific extensions

That explicitness is the main strength of the current implementation.
