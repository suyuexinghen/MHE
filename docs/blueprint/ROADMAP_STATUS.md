# MHE Roadmap Status Matrix

This document tracks how the current `MHE/` implementation maps to the master roadmap in `docs/roadmap/Meta_Harness_master_roadmap.md`.

## Legend

| Status | Meaning |
|---|---|
| Done | Implemented and evidenced in the current `MHE` tree |
| Partial | Some meaningful implementation exists, but the roadmap item is not fully satisfied |
| Missing | Not implemented in the current `MHE` tree |

## Overall Summary

| Subproject | Status | Notes |
|---|---|---|
| MH-SP1 — Component SDK & Core Infrastructure | Done | Discovery, dependency resolution, registration staging, and boot orchestration are implemented |
| MH-SP2 — Connection Engine & Graph Management | Done | Routing, validation, XML import, event bus, port/route tables, pruner, and version lifecycle are implemented |
| MH-SP3 — Core Components Implementation | Done | All nine core components exist, optimizer has observe/propose/evaluate/commit, default topology wires them |
| MH-SP4 — Safety, Governance & Hot-Reload | Done | Four-tier safety chain, sandbox tier abstraction with risk-tier selection, and hot-reload saga orchestration are implemented |
| MH-SP5 — Observability, Audit & Provenance | Done | Metrics, traces, trajectories, PROV evidence, Merkle-anchored audit log, provenance queries, and counter-factual diagnosis are implemented |
| MH-SP6 — Optimizer & Self-Growth Engine | Done | Triggers, fitness, convergence, encoder, action-space funnel, search phases, Bayesian optimizer, RL adapter, templates, codegen, and migration adapter system are all implemented |
| MH-SP7 — Productization, Extension Ecosystem & Rollout | Done | Extension guide, optimizer-extension guide, API stability doc, protected-component guide, evaluation fixtures, and benchmark runner are all in place |

## MH-SP1 — Component SDK & Core Infrastructure

| Item | Status | Notes |
|---|---|---|
| 1.1.1 `HarnessComponent` base class | Done | `declare_interface`, `activate`, `deactivate`, `export_state`, `import_state`, `transform_state`, `health_check` |
| 1.1.2 `ComponentManifest` | Done | Includes `id`, `name`, `version`, `kind`, `entry`, `harness_version`, `deps`, `bins`, `env`, `contracts`, `provides`, `requires`, `safety`, `state_schema_version`, `enabled` |
| 1.1.3 `ComponentType` enum | Done | `CORE`, `TEMPLATE`, `META`, `GOVERNANCE` (plus legacy `CUSTOM`); `ComponentKind` retained as alias |
| 1.1.4 `ComponentPhase` enum | Done | Wiki-aligned 8-phase enum with transition enforcement via `LifecycleTracker` |
| 1.1.5 `HarnessAPI` injection interface | Done | All declaration helpers plus `register_connection_handler`, `register_migration_adapter`, and atomic `_commit()` |
| 1.1.6 `ComponentRuntime` injection | Done | Adds `storage_path`, `metrics`, `process_direct`, `tool_execute` alongside the existing fields |
| 1.1.7 Foundational ADRs | Done | ADR-001..ADR-004 cover package name, runtime authority, core semantics, and protected components |
| 1.1.8 Slot system | Done | Primary/secondary slot binding with enum-typed API |
| 1.1.9 Capability vocabulary | Done | Provide/require capabilities at both contract and module level; dependency resolver honours them |
| 1.1.10 Default implementations | Done | Baseline manifests plus `default_impl` manifest field |
| 1.2.1 Discovery across 4 sources | Done | `ComponentDiscovery` scans bundled/templates/market/custom |
| 1.2.2 Conflict resolution | Done | Source-priority override via `DiscoveryResult.winners` / `overridden` |
| 1.2.3 Loader static validation | Done | `validate_manifest_static` checks `harness_version`, `bins`, and `env` |
| 1.2.4 Dependency resolution | Done | Kahn topological sort with missing-dep and cycle detection (`resolve_boot_order`) |
| 1.2.5 Import and class loading | Done | Import loading with explicit errors |
| 1.3.1 `ComponentRegistry` | Done | Tracks components, slots, capabilities, graph versions, pending mutations, and a pending zone |
| 1.3.2 Staged registration with commit/rollback | Done | `stage`, `commit_pending`, `abort_pending` provide atomic batch registration |
| 1.3.3 Conflict detection | Done | `RegistrationConflictError` raised on duplicate component ids |
| 1.3.4 Enabled/disabled filtering | Done | `filter_enabled` honours manifest + config-driven overrides |
| 1.3.5 `HarnessRuntime.boot()` orchestration | Done | Orchestrates discovery → validation → dependency resolution → registration |

## MH-SP2 — Connection Engine & Graph Management

| Item | Status | Notes |
|---|---|---|
| 2.1.1 `Input` / `Output` / `Event` models | Done | SDK contracts |
| 2.1.2 `Connection` model | Done | `ConnectionEdge` |
| 2.1.3 `PendingConnection` / `PendingConnectionSet` | Done | Distinct `PendingConnection` type plus `add_pending_connection` helper |
| 2.1.4 `ConnectionEngine` routing | Done | `sync` / `async` / `event` / `shadow` with `emit` and `emit_async` |
| 2.1.5 `EventBus` dispatch | Done | `EventBus` with subscriber management, trace propagation, and history |
| 2.2.1 Compatibility validator (5 rules) | Done | Type matching, event declaration, input completeness, id uniqueness, graph consistency |
| 2.2.2 `ContractPruner` | Done | Pruner filters by payload/direction and respects protected/denied pairs |
| 2.2.3 `PortIndex` and `RouteTable` | Done | Public classes compiled from the registry/graph snapshot |
| 2.3.1 `GraphVersionManager` | Done | Wrapper over `GraphVersionStore` with candidate/active/rollback/archived lifecycle |
| 2.3.2 Candidate graph assembly | Done | Candidate snapshots are staged from pending models |
| 2.3.3 Atomic cutover | Done | `GraphVersionManager.cutover` performs atomic version switch |
| 2.3.4 Graph version retirement | Done | Retention window archives old snapshots; rollback rehydrates from archive |
| 2.3.5 XML/XSD parser | Done | XML import with structural XSD-style validation and async helper |

## MH-SP3 — Core Components Implementation

| Item | Status | Notes |
|---|---|---|
| 3.1.1 `Runtime` | Done | Minimal runtime component wired into demo + default topology |
| 3.1.2 `Gateway` | Done | Task-entry component wired into demo + default topology |
| 3.1.3 `Memory` | Done | In-memory record store with manifest and topology wiring |
| 3.1.4 `ToolHub` | Done | Tool registration/discovery/execution with audit log |
| 3.1.5 `Planner` | Done | Minimal planner wired into expanded topology |
| 3.1.6 `Executor` | Done | Minimal executor wired into expanded topology |
| 3.1.7 `Evaluation` | Done | Performance-vector emitter wired into expanded topology |
| 3.1.8 `Observability` | Done | Audit event capture with event-subscriber semantics |
| 3.1.9 `Policy` | Done | Decision recording plus `review_proposal` governance hook |
| 3.2.1 Optimizer as meta-layer component | Done | Optimizer never participates in task execution; only proposes |
| 3.2.2 Optimizer interfaces | Done | `observe`, `propose`, `propose_batch`, `evaluate`, `commit` hooks |
| 3.2.3 Protected component boundaries | Done | Validator rejects protected-slot overrides; optimizer holds no write path |
| 3.2.4 `PendingMutation` model | Done | Carries `type` (param/connection/template/code/policy), `target`, `justification` |
| 3.3.1 Default connection topology | Done | `examples/graphs/default-topology.xml` wires all nine core components |
| 3.3.2 Component dependency declarations | Done | Manifests carry `deps`, `provides`, `requires`; resolver uses them |
| 3.3.3 Orphan component detection | Done | `detect_orphans` + validator emit `orphan_component` for unreferenced nodes with inputs |

## MH-SP4 — Safety, Governance & Hot-Reload

| Item | Status | Notes |
|---|---|---|
| 4.1.1 Level 1 SandboxValidator | Done | `SandboxValidator` runs the full validator chain against a candidate snapshot |
| 4.1.2 Level 2 ABShadowTester | Done | `ABShadowTester` supports pluggable baseline / candidate runners and comparator |
| 4.1.3 Level 3 PolicyVeto | Done | `PolicyVetoGate` delegates to `PolicyComponent.review_proposal` with a fresh validation report |
| 4.1.4 Level 4 AutoRollback | Done | `AutoRollback` records health probes and triggers `ConnectionEngine.rollback` on failure |
| 4.1.5 Guard / Mutate / Reduce hooks | Done | `HookRegistry` provides all three hook families with ordered application |
| 4.1.6 Sequential gate pipeline | Done | `SafetyPipeline` runs gates in order, short-circuits on first reject, captures evidence |
| 4.2.1 V8/WASM sandbox tier | Done | `v8_wasm_adapter()` exposes the tier with an in-process fallback adapter |
| 4.2.2 gVisor sandbox tier | Done | `gvisor_adapter()` exposes the tier with an in-process fallback adapter |
| 4.2.3 Firecracker sandbox tier | Done | `firecracker_adapter()` exposes the tier with an in-process fallback adapter |
| 4.2.4 Risk-tier selection | Done | `RiskTierSelector` picks the cheapest adapter meeting the risk-driven floor tier |
| 4.3.1 `suspend()` on components | Done | `HarnessComponent.suspend` available on all components with a safe default |
| 4.3.2 State snapshot capture | Done | `CheckpointManager.capture` returns a bounded-history snapshot store |
| 4.3.3 `transform_state()` migration | Done | Default merge-delta plus orchestrator-driven invocation during hot swap |
| 4.3.4 `resume(new_state)` | Done | `HarnessComponent.resume` rehydrates the component from optional state |
| 4.3.5 Checkpoint management | Done | Retention-bounded `CheckpointManager` with `capture_sync` / `restore` helpers |
| 4.3.6 Saga rollback | Done | `SagaRollback` runs forward actions and compensations in LIFO order |

## MH-SP5 — Observability, Audit & Provenance

| Item | Status | Notes |
|---|---|---|
| 5.1.1 System-level metrics | Done | `MetricsRegistry` collects Counter/Gauge/Histogram under the `system` scope |
| 5.1.2 Component-level metrics | Done | Same registry with `component` scope; labels are keyed per-component |
| 5.1.3 Task-level trace collection | Done | `TraceCollector` starts / finishes spans with trace-id propagation; bounded capacity |
| 5.2.1 Execution trajectory persistence | Done | `TrajectoryStore` records per-task step history with optional JSONL flush |
| 5.2.2 Trace query interface | Done | `TraceQuery` filters by span name, attribute, duration, or a custom predicate |
| 5.2.3 Replay mechanism | Done | `TraceReplay.replay` re-emits spans in timestamp order (optionally throttled) |
| 5.3.1 PROV evidence object model | Done | `ProvGraph` with Entity / Activity / Agent nodes and the core PROV-O relations |
| 5.3.2 Merkle tree construction | Done | `MerkleTree` produces root hashes and inclusion proofs for any leaf index |
| 5.3.3 Provenance query | Done | `ProvenanceQuery` walks derivations, attributions, and associations |
| 5.3.4 Audit log persistence | Done | `AuditLog` is an append-only JSONL log anchored into the Merkle tree |
| 5.3.5 Counter-factual diagnosis interfaces | Done | `CounterFactualDiagnosis` prunes PROV graphs and scores hypotheses against an evaluator |

## MH-SP6 — Optimizer & Self-Growth Engine

| Item | Status | Notes |
|---|---|---|
| 6.1.1 Layered trigger mechanism | Done | `LayeredTriggerSystem` supports METRIC / EVENT / SCHEDULE / MANUAL / COMPOSITE layers |
| 6.1.2 Trigger gating with thresholds | Done | `TriggerThreshold` enforces min/max/delta/interval gating per trigger |
| 6.1.3 Phase A local parameter search | Done | `LocalParameterSearch` supports grid and random strategies over a schema |
| 6.1.4 Phase B topology & template search | Done | `TopologyTemplateSearch` enumerates add/remove/swap moves using `ContractPruner` |
| 6.1.5 Phase C constrained synthesis | Done | `ConstrainedSynthesis` filters plans by user-supplied invariants |
| 6.1.6 Bayesian optimization | Done | `BayesianOptimizer` implements UCB-style surrogate-free arm selection |
| 6.1.7 Optional RL enhancement | Done | `RLEnhancement` provides a softmax policy with REINFORCE-style updates |
| 6.2.1 GIN-based state encoder | Done | `GINEncoder` produces deterministic per-node and graph-level embeddings |
| 6.2.2 4-layer action space funnel | Done | `ActionSpaceFunnel` runs generate/structural/contract/budget filters + scorer |
| 6.2.3 Contract-driven pruning | Done | `ContractPruner` emits legal connection targets |
| 6.3.1 Triple convergence criteria | Done | `TripleConvergence` evaluates plateau / budget / safety-floor criteria |
| 6.3.2 Reward/fitness functions | Done | `RewardComponents`, `FitnessEvaluator`, and `composite_fitness` |
| 6.3.3 Negative reward feedback | Done | `NegativeRewardLoop` accumulates decaying penalties per subject |
| 6.3.4 Dead End detection | Done | `DeadEndDetector` tracks per-path score windows |
| 6.3.5 Non-Markovian state caveat | Done | `NonMarkovianGuard` exposes a bounded lookback window |
| 6.4.1 Template registry | Done | `TemplateRegistry` with register / list / find_by_kind |
| 6.4.2 Slot-filling engine | Done | `SlotFillingEngine.bind` and `instantiate` produce concrete manifests |
| 6.4.3 Code generation pipeline | Done | `CodegenPipeline.render` emits manifest / module stub / graph fragment |
| 6.4.4 Migration adapter system | Done | `MigrationAdapterSystem` resolves adapter chains via BFS and executes them |

## MH-SP7 — Productization, Extension Ecosystem & Rollout

| Item | Status | Notes |
|---|---|---|
| 7.1.1 Extension guide for custom components | Done | `docs/EXTENSION_GUIDE.md` walks through components, handlers, templates, packaging |
| 7.1.2 Candidate-graph-first workflow docs | Done | Covered in README and `docs/USER_GUIDE.md` |
| 7.1.3 Protected component constraints docs | Done | `docs/PROTECTED_COMPONENTS.md` plus ADR-004 |
| 7.1.4 Optimizer extension points docs | Done | `docs/OPTIMIZER_EXTENSIONS.md` lists every extension point |
| 7.2.1 Safety-chain evaluation fixtures | Done | `metaharness.fixtures.safety_scenarios` ships five canonical scenarios |
| 7.2.2 Hot-reload evaluation fixtures | Done | `metaharness.fixtures.hot_reload_scenarios` covers success, failure, empty-state cases |
| 7.2.3 Optimizer evaluation fixtures | Done | `metaharness.fixtures.optimizer_scenarios` plus dedicated optimizer test suites |
| 7.2.4 API stability guarantees | Done | `docs/API_STABILITY.md` documents the tiered stability model |
| 7.2.5 Performance benchmarks | Done | `metaharness.benchmarks` runs connection-engine / Bayesian / audit-log microsweeps |

## Version / Gate Assessment

| Gate | Status | Notes |
|---|---|---|
| v0.1 — SDK Ready | Done | Discovery, dependency resolution, registry staging, and boot orchestration are in place |
| v0.2 — Connection Ready | Done | Routing, validation, event bus, pruner, and graph version lifecycle are in place |
| v0.5 — MVP | Done | Candidate graph, validation, commit, rollback, and end-to-end demos are exercised by tests |
| v1.0 — Core Components Ready | Done | All nine core components plus optimizer skeleton wired via the default topology |
| v1.1 — Safety Ready | Done | Four-tier safety chain, sandbox tier abstraction, and hot-reload orchestration implemented |
| v1.2 — Observability Ready | Done | Metrics, trace, trajectory, PROV evidence, Merkle-anchored audit log, and counter-factual diagnosis implemented |
| v2.0 — Self-Growth Ready | Done | Triggers, fitness, convergence, encoder, action-space funnel, search phases, Bayesian / RL, and template+codegen+migration implemented |
| v3.0 — Productized | Done | Extension guide, optimizer extensions, protected-component guide, API stability guide, evaluation fixtures, and benchmark runner implemented |

## Evidence Pointers

- SDK and registry
  - `MHE/src/metaharness/sdk/api.py`
  - `MHE/src/metaharness/sdk/base.py`
  - `MHE/src/metaharness/sdk/manifest.py`
  - `MHE/src/metaharness/sdk/runtime.py`
  - `MHE/src/metaharness/sdk/loader.py`
  - `MHE/src/metaharness/sdk/discovery.py`
  - `MHE/src/metaharness/sdk/dependency.py`
  - `MHE/src/metaharness/sdk/registry.py`
- Graph and validation core
  - `MHE/src/metaharness/core/boot.py`
  - `MHE/src/metaharness/core/models.py`
  - `MHE/src/metaharness/core/event_bus.py`
  - `MHE/src/metaharness/core/port_index.py`
  - `MHE/src/metaharness/core/contract_pruner.py`
  - `MHE/src/metaharness/core/graph_versions.py`
  - `MHE/src/metaharness/core/connection_engine.py`
  - `MHE/src/metaharness/core/validators.py`
  - `MHE/src/metaharness/config/xml_parser.py`
  - `MHE/src/metaharness/config/xsd_validator.py`
- Lifecycle, mutation, and optimizer scaffolding
  - `MHE/src/metaharness/core/lifecycle_tracker.py`
  - `MHE/src/metaharness/core/mutation.py`
  - `MHE/src/metaharness/components/optimizer.py`
  - `MHE/src/metaharness/components/policy.py`
  - `MHE/src/metaharness/components/toolhub.py`
- Safety and hot-reload
  - `MHE/src/metaharness/safety/gates.py`
  - `MHE/src/metaharness/safety/sandbox_validator.py`
  - `MHE/src/metaharness/safety/ab_shadow.py`
  - `MHE/src/metaharness/safety/policy_veto.py`
  - `MHE/src/metaharness/safety/auto_rollback.py`
  - `MHE/src/metaharness/safety/hooks.py`
  - `MHE/src/metaharness/safety/pipeline.py`
  - `MHE/src/metaharness/safety/sandbox_tiers.py`
  - `MHE/src/metaharness/hotreload/checkpoint.py`
  - `MHE/src/metaharness/hotreload/saga.py`
  - `MHE/src/metaharness/hotreload/swap.py`
- Observability and provenance
  - `MHE/src/metaharness/observability/metrics.py`
  - `MHE/src/metaharness/observability/trace.py`
  - `MHE/src/metaharness/observability/trajectory.py`
  - `MHE/src/metaharness/provenance/evidence.py`
  - `MHE/src/metaharness/provenance/merkle.py`
  - `MHE/src/metaharness/provenance/audit_log.py`
  - `MHE/src/metaharness/provenance/query.py`
  - `MHE/src/metaharness/provenance/counter_factual.py`
- Optimizer and self-growth
  - `MHE/src/metaharness/optimizer/triggers.py`
  - `MHE/src/metaharness/optimizer/fitness.py`
  - `MHE/src/metaharness/optimizer/convergence.py`
  - `MHE/src/metaharness/optimizer/encoder.py`
  - `MHE/src/metaharness/optimizer/action_space.py`
  - `MHE/src/metaharness/optimizer/search/phase_a.py`
  - `MHE/src/metaharness/optimizer/search/phase_b.py`
  - `MHE/src/metaharness/optimizer/search/phase_c.py`
  - `MHE/src/metaharness/optimizer/search/bayesian.py`
  - `MHE/src/metaharness/optimizer/search/rl.py`
  - `MHE/src/metaharness/optimizer/templates/registry.py`
  - `MHE/src/metaharness/optimizer/templates/slots.py`
  - `MHE/src/metaharness/optimizer/templates/codegen.py`
  - `MHE/src/metaharness/optimizer/templates/migration.py`
- Fixtures and benchmarks
  - `MHE/src/metaharness/fixtures/safety_scenarios.py`
  - `MHE/src/metaharness/fixtures/hot_reload_scenarios.py`
  - `MHE/src/metaharness/fixtures/optimizer_scenarios.py`
  - `MHE/src/metaharness/benchmarks/runner.py`
- Productization docs
  - `MHE/docs/EXTENSION_GUIDE.md`
  - `MHE/docs/OPTIMIZER_EXTENSIONS.md`
  - `MHE/docs/PROTECTED_COMPONENTS.md`
  - `MHE/docs/API_STABILITY.md`
- Demo, CLI, and docs
  - `MHE/src/metaharness/demo.py`
  - `MHE/src/metaharness/cli.py`
  - `MHE/examples/graphs/default-topology.xml`
  - `MHE/README.md`
  - `MHE/docs/USER_GUIDE.md`
  - `MHE/docs/adr/ADR-004-protected-components.md`

## Status Statement

MH-SP1–MH-SP7 are complete: the SDK, connection engine, graph version lifecycle, all nine core components, the four-tier safety chain, sandbox tier abstraction, hot-reload saga orchestration, full observability + Merkle-anchored audit trail with counter-factual diagnosis, the self-growth engine, and the productization / extension ecosystem are implemented, tested, and lint-clean. The current MHE tree satisfies the roadmap through the v3.0 productization gate.
