# Meta-Harness Master Roadmap (17 Apr 2026)

This document defines the development roadmap for the **Meta-Harness** self-modifying agent framework, based on the consolidated wiki at `docs/wiki/meta-harness-wiki/` and the revised merge plan at `docs/wiki/RevisedMergePlan.md`.

The Meta-Harness is a plugin-based, self-optimizing agent runtime that can safely modify its own component topology, connection graph, and behavioral policies at runtime — subject to a four-level safety chain and constitutional governance layer.

In short:

- **v0.x** establishes the Component SDK, lifecycle management, and connection engine
- **v1.x** implements the nine core components + Optimizer skeleton with basic governance
- **v2.x** adds the full four-level safety chain, hot-reload, observability, and Merkle audit
- **v3.x** activates the self-growth Optimizer, template library, and code generation
- **v4.x** productizes the ecosystem with stable APIs, extension guides, and rollout support

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Background Snapshot](#background-snapshot)
3. [Design Principles](#design-principles)
4. [Architecture Overview](#architecture-overview)
5. [Programme Structure](#programme-structure)
6. [Status Summary](#status-summary)
7. [MH-SP1 — Component SDK & Core Infrastructure](#mh-sp1--component-sdk--core-infrastructure)
8. [MH-SP2 — Connection Engine & Graph Management](#mh-sp2--connection-engine--graph-management)
9. [MH-SP3 — Core Components Implementation](#mh-sp3--core-components-implementation)
10. [MH-SP4 — Safety, Governance & Hot-Reload](#mh-sp4--safety-governance--hot-reload)
11. [MH-SP5 — Observability, Audit & Provenance](#mh-sp5--observability-audit--provenance)
12. [MH-SP6 — Optimizer & Self-Growth Engine](#mh-sp6--optimizer--self-growth-engine)
13. [MH-SP7 — Productization, Extension Ecosystem & Rollout](#mh-sp7--productization-extension-ecosystem--rollout)
14. [Cross-Project Dependencies & Critical Path](#cross-project-dependencies--critical-path)
15. [Phase-to-Version Mapping](#phase-to-version-mapping)
16. [Risk Register](#risk-register)
17. [Acceptance Criteria](#acceptance-criteria)

---

## Executive Summary

The Meta-Harness addresses a fundamental limitation of current agent architectures: **static configuration**. Once deployed, an agent's component topology, connection graph, and behavioral parameters are frozen. Adapting requires manual re-engineering.

The Meta-Harness solves this by introducing:

- **Staged component lifecycle** — discover → validate → register → activate → deactivate, with atomic commit/rollback at each stage
- **Candidate graph / active graph versioning** — proposed changes enter a `pending mutations` queue, are assembled into a candidate graph, validated through a four-level safety chain, and only then committed as a new active graph version
- **Meta-layer Optimizer** — a separate component that observes performance metrics, proposes candidate mutations, and iterates using evolutionary search (with Bayesian optimization and optional RL)
- **Constitutional governance** — immutable rules (C-01 through C-05) and domain-specific regulations (R-01 through R-03) that the Optimizer cannot override
- **Suspend-Transform-Resume hot-reload** — live component replacement inspired by Erlang's `code_change`, with checkpoint, state migration, and automatic rollback

This roadmap translates the wiki design into an actionable, phased development plan.

---

## Background Snapshot

### Current Baseline

| Capability | Status | Notes |
|---|---|---|
| Meta-Harness wiki | Complete | 10 chapters (01–10) totaling ~8,400 lines, covering SDK through extension guide |
| Meta-Harness wiki draft | Complete | 9 chapters as alternative framing, stronger on terminology and control-plane structure |
| Revised merge plan | Approved | `docs/wiki/RevisedMergePlan.md` defines merge strategy with 6 phases |
| Architecture diagrams | Complete | `fig1` (system architecture) and `fig2` (lifecycle sequence) in PlantUML |
| Reference systems | Researched | Aeloon Plugin SDK, Erlang OTP, Kubernetes Operator pattern studied for design inspiration |

### Key Design Decision

Meta-Harness is a **standalone system** with its own SDK, runtime, and governance layer. It does not depend on or extend any existing plugin framework. Existing systems (Aeloon Plugin SDK, Erlang OTP, Kubernetes) were studied for design inspiration, but Meta-Harness defines its own abstractions:

| Aspect | Meta-Harness Design |
|---|---|
| Primary unit | Component |
| Registration | Pending → candidate graph → active graph version |
| Lifecycle | discover → validate → assemble → dynamic-validate → activate → commit |
| Safety | 4-level safety chain before any config change |
| Modification | Optimizer-driven with constitutional governance |
| Hot-reload | Suspend-Transform-Resume with state migration |

---

## Design Principles

1. **Candidate graph first, active graph second**
   - No component or connection enters the active graph without passing through the candidate graph → safety chain → commit pipeline.

2. **Staged lifecycle with atomic boundaries**
   - Each lifecycle phase has clear entry/exit conditions and can be rolled back independently. Registration is an atomic `_commit()` within the SDK, not a visible lifecycle phase.

3. **Protected components**
   - Policy, Identity, and Evaluation-QC are protected: the Optimizer cannot modify them without passing through a Human Review Gate.

4. **Conservative status semantics**
   - Component phases: `DISCOVERED` → `VALIDATED_STATIC` → `ASSEMBLED` → `VALIDATED_DYNAMIC` → `ACTIVATED` → `COMMITTED` → `SUSPENDED` → `FAILED`
   - Graph versions: `candidate` → `active` → `rollback_target` → `archived`

5. **Observability as a first-class citizen**
   - Every state transition, mutation proposal, and safety-chain decision produces structured evidence objects.

6. **Token / resource budget as hard constraint**
   - Budgets are not just optimization targets — they are circuit breakers. Every component must respect ceiling and floor limits.

7. **Graph-version lifecycle management**
   - Versions are not infinitely accumulated. Retirement, archival, and staleness prevention are built-in.

8. **Evolutionary search first, RL optional**
   - The Optimizer's primary search strategy is evolutionary (population-based). Bayesian optimization for parameter tuning. RL only as optional enhancement in later phases.

---

## Architecture Overview

The Meta-Harness is organized into six layers:

```
L1: Core Kernel
    HarnessRuntime, ConfigParser, ComponentDiscovery, ComponentLoader

L2: Component SDK
    HarnessComponent, HarnessAPI, ComponentRuntime, ComponentRegistry

L3: Connection Engine
    ConnectionEngine, EventBus, CompatibilityValidator, ContractPruner, GraphVersionManager

L4: Core Components (9 + Meta-layer)
    Gateway, Runtime, Memory, ToolHub, Planner/Reasoner, Executor,
    Evaluation, Observability, Policy/Governance, Optimizer (meta)

    Note: Identity is a protected root capability managed by Policy/Gateway/Runtime,
    not a standalone core component. Sandbox and Browser are ToolHub/Executor
    extension classes. The book's older 12-component taxonomy is historical.

L5: Governance Plane
    4-level safety chain, 3-tier sandbox, PolicyVeto, AutoRollback, Merkle audit

L6: Plugin & Template Ecosystem
    ComponentPlugin, MetaPlugin, GovernancePlugin, TemplateLibrary, CodeGenPipeline
```

Component lifecycle follows 10 phases (see `fig2_meta_harness_lifecycle_flow.puml`):

```
Phase 0:  Startup
Phase 1:  Discovery (4 sources: bundled, templates, market, custom)
Phase 2:  Static Validation (manifest, deps, version compat)
Phase 3:  Dependency Resolution (Kahn's topological sort)
Phase 4:  Register & Interface Declaration
Phase 5:  Candidate Graph Assembly (5 compatibility rules)
Phase 6:  Dynamic Validation — 4-level safety chain
Phase 7:  Activate & Commit (with Suspend-Transform-Resume)
Phase 8:  Observe & Rollback
Phase 9:  Shutdown
```

### Canonical Scope

The authoritative component model follows the wiki (`03-core-components.md`):

| # | Core Component | Protected | Notes |
|---|---|---|---|
| 1 | Runtime / Orchestrator | No | Task scheduling, flow coordination |
| 2 | Gateway | No | Communication, credential management |
| 3 | Memory | No | Context read/write, trajectory persistence |
| 4 | ToolHub | No | Tool registration, discovery, execution |
| 5 | Planner / Reasoner | No | Plan decomposition, strategy selection |
| 6 | Executor | No | Action execution, result collection |
| 7 | Evaluation | **Yes** | Performance metrics, quality control |
| 8 | Observability | No | Metrics collection, health monitoring |
| 9 | Policy / Governance | **Yes** | Permission enforcement, constitutional rules |
| — | Optimizer (meta-layer) | No | Self-growth engine; does not participate in task execution |

Identity, Sandbox, and Browser are **not** core components. They are capabilities provided by the core components above.

---

## Programme Structure

| Sub-Project | Focus | Depends On |
|---|---|---|
| **MH-SP1** Component SDK & Core Infrastructure | HarnessComponent, HarnessAPI, ComponentRuntime, ComponentManifest, ComponentRegistry, ComponentDiscovery, ComponentLoader, staged lifecycle | — |
| **MH-SP2** Connection Engine & Graph Management | ConnectionEngine, EventBus, CompatibilityValidator, ContractPruner, GraphVersionManager, pending mutations, candidate graph | MH-SP1 |
| **MH-SP3** Core Components Implementation | 9 core components + Optimizer skeleton; component interfaces, ports, slots, capabilities | MH-SP1, MH-SP2 |
| **MH-SP4** Safety, Governance & Hot-Reload | 4-level safety chain, 3-tier sandbox, PolicyVeto, AutoRollback, Suspend-Transform-Resume, checkpoint, Saga, constitutional layer | MH-SP2, MH-SP3 |
| **MH-SP5** Observability, Audit & Provenance | 3-layer metrics, Trace/Replay, Merkle audit chain, evidence objects, provenance queries | MH-SP3 |
| **MH-SP6** Optimizer & Self-Growth Engine | three-phase search, GIN state encoding, 5-layer trigger mechanism, 4-layer action funnel, convergence criteria, template/code generation, trigger gating | MH-SP3, MH-SP4, MH-SP5 |
| **MH-SP7** Productization, Extension Ecosystem & Rollout | Docs, extension guide, template library, API stability, evaluation fixtures, ecosystem tooling | MH-SP1–SP6 |

---

## Status Summary

| SP | Status | Target Milestone |
|---|---|---|
| MH-SP1 Component SDK & Core Infrastructure | **Planned — not started** | M1.1 |
| MH-SP2 Connection Engine & Graph Management | **Planned — not started** | M1.2 |
| MH-SP3 Core Components Implementation | **Planned — not started** | M2.1 |
| MH-SP4 Safety, Governance & Hot-Reload | **Planned — not started** | M2.2 |
| MH-SP5 Observability, Audit & Provenance | **Planned — not started** | M2.3 |
| MH-SP6 Optimizer & Self-Growth Engine | **Planned — not started** | M3.1 |
| MH-SP7 Productization, Extension Ecosystem & Rollout | **Planned — parallel after kernel stabilizes** | M4 |

---

## MH-SP1 — Component SDK & Core Infrastructure

**Goal:** Establish the component abstraction layer, lifecycle management, discovery, loading, and registration — the foundational SDK upon all other Meta-Harness layers depend.

**Milestone target:** M1.1 — Component SDK Ready

### P1.1 Core SDK Models

| # | Task | Status | Acceptance Criteria |
|---|---|---|---|
| 1.1.1 | Define `HarnessComponent` base class | [ ] | Abstract base with `declare_interface()`, `activate()`, `deactivate()`, `export_state()`, `import_state()`, `transform_state()`, `health_check()` hooks |
| 1.1.2 | Define `ComponentManifest` (`harness.component.json`) | [ ] | Manifest includes id, name, version, `kind`, `entry`, harness_version, deps, bins, env, `contracts`, `provides`, `requires`, `slots`, `safety`, `state_schema_version` |
| 1.1.3 | Define `ComponentType` enum | [ ] | CORE, TEMPLATE, META, GOVERNANCE types supported |
| 1.1.4 | Define `ComponentPhase` enum | [ ] | DISCOVERED → VALIDATED_STATIC → ASSEMBLED → VALIDATED_DYNAMIC → ACTIVATED → COMMITTED → SUSPENDED → FAILED |
| 1.1.5 | Define `HarnessAPI` injection interface | [ ] | API provides `declare_input()`, `declare_output()`, `declare_event()`, `provide_capability()`, `require_capability()`, `bind_slot()`, `reserve_slot()`, `register_connection_handler()`, `register_hook()`, `register_service()`, `register_validator()`, `register_migration_adapter()`, `_commit()` |
| 1.1.6 | Define `ComponentRuntime` injection | [ ] | Runtime provides `storage_path`, `config`, `logger`, `metrics`, `trace_store`, `event_bus`, `llm`, `sandbox_client`, `graph_reader`, `mutation_submit`, `process_direct()`, `tool_execute()` |
| 1.1.7 | Write ADRs for foundational decisions | [ ] | ADR-001: component taxonomy, ADR-002: package boundaries + package naming, ADR-003: XML vs internal model, ADR-004: protected components |

### P1.2 Discovery & Loading

### P1.1b Slot System & Capability Vocabulary

| # | Task | Status | Acceptance Criteria |
|---|---|---|---|
| 1.1.8 | Define slot system | [ ] | Primary and secondary slots defined; one primary instance per core slot |
| 1.1.9 | Define capability vocabulary | [ ] | `domain.verb[.qualifier]` naming scheme adopted across core components |
| 1.1.10 | Define default implementations | [ ] | Baseline default implementation named for each primary slot |

### P1.2 Discovery & Loading

| # | Task | Status | Acceptance Criteria |
|---|---|---|---|
| 1.2.1 | Implement `ComponentDiscovery` with 4 sources | [ ] | scan_bundled, scan_templates, scan_market, scan_custom all functional |
| 1.2.2 | Implement conflict resolution (priority override) | [ ] | Higher-priority source overrides lower when same component found |
| 1.2.3 | Implement `ComponentLoader` — static validation | [ ] | Validates harness_version, bins/env deps, manifest schema |
| 1.2.4 | Implement dependency resolution (Kahn's algorithm) | [ ] | Topological sort with circular-dependency detection |
| 1.2.5 | Implement import and class loading | [ ] | `import_module()` with proper error handling and phase tracking |

### P1.3 Registry & Lifecycle

| # | Task | Status | Acceptance Criteria |
|---|---|---|---|
| 1.3.1 | Implement `ComponentRegistry` | [ ] | Tracks components, slots, capabilities, graph versions, pending mutations |
| 1.3.2 | Implement staged registration with commit/rollback | [ ] | Components enter pending zone first; atomic commit or rollback on failure |
| 1.3.3 | Implement conflict detection (ID / port) | [ ] | Duplicate IDs or overlapping ports trigger RegistrationConflictError |
| 1.3.4 | Implement enabled/disabled filtering | [ ] | config.enabled=False components are skipped during boot |
| 1.3.5 | Implement `HarnessRuntime.boot()` orchestration | [ ] | Orchestrates discovery → validation → dependency resolution → registration in correct order |

---

## MH-SP2 — Connection Engine & Graph Management

**Goal:** Build the data routing layer, compatibility validation, graph versioning, and the pending-mutations → candidate-graph → active-graph pipeline.

**Milestone target:** M1.2 — Connection Engine Ready

### P2.1 Connection Engine Core

| # | Task | Status | Acceptance Criteria |
|---|---|---|---|
| 2.1.1 | Define `Input` / `Output` / `Event` port models | [ ] | Ports have name, contract/type, required flag, description |
| 2.1.2 | Define `Connection` model | [ ] | Source component + output → target component + input, with payload/mode/policy properties |
| 2.1.3 | Define `PendingConnection` / `PendingConnectionSet` | [ ] | Proposed connections are staged before commit |
| 2.1.4 | Implement `ConnectionEngine` routing | [ ] | Routes data between connected component ports in `sync` / `async` / `event` / `shadow` modes |
| 2.1.5 | Implement `EventBus` dispatch | [ ] | Event-driven routing with subscriber management and trace propagation |

### P2.2 Compatibility Validation

| # | Task | Status | Acceptance Criteria |
|---|---|---|---|
| 2.2.1 | Implement `CompatibilityValidator` — 5 rules | [ ] | Contract matching, event declaration, input completeness, ID uniqueness, graph consistency / no illegal loops |
| 2.2.2 | Implement `ContractPruner` | [ ] | Prunes search space for Optimizer by eliminating incompatible connection proposals |
| 2.2.3 | Implement `PortIndex` and `RouteTable` | [ ] | Fast routing lookup and graph assembly structures exist |

### P2.3 Graph Version Management

| # | Task | Status | Acceptance Criteria |
|---|---|---|---|
| 2.3.1 | Implement `GraphVersionManager` | [ ] | Creates immutable graph snapshots, tracks candidate → active → rollback_target → archived lifecycle |
| 2.3.2 | Implement candidate graph assembly | [ ] | Collects pending components/connections, validates compatibility, creates candidate snapshot |
| 2.3.3 | Implement atomic cutover | [ ] | candidate → active graph version switch is atomic; old version becomes rollback_target |
| 2.3.4 | Implement graph version retirement | [ ] | Archived versions are cleaned up; staleness detection prevents version rot |
| 2.3.5 | Implement XML/XSD configuration parser | [ ] | Parses `harness.config.xml` with XSD validation for component and connection definitions |

---

## MH-SP3 — Core Components Implementation

**Goal:** Implement the nine core components and the Optimizer skeleton. Each component follows the SDK contract from MH-SP1 and registers its ports/connections via MH-SP2.

**Milestone target:** M2.1 — Core Components Ready

### P3.1 Core Components

| # | Task | Status | Acceptance Criteria |
|---|---|---|---|
| 3.1.1 | Implement `Runtime` component | [ ] | Task scheduling, flow coordination, dispatch |
| 3.1.2 | Implement `Gateway` component | [ ] | Communication interface, credential management, API routing |
| 3.1.3 | Implement `Memory` component | [ ] | Context read/write, trajectory persistence, hot/cold storage |
| 3.1.4 | Implement `ToolHub` component | [ ] | Tool registration, discovery, execution sandboxing |
| 3.1.5 | Implement `Planner` component | [ ] | Plan decomposition, reasoning, strategy selection |
| 3.1.6 | Implement `Executor` component | [ ] | Action execution, result collection, retry/error handling |
| 3.1.7 | Implement `Evaluation` component | [ ] | Performance metrics, quality control, fitness assessment |
| 3.1.8 | Implement `Observability` component | [ ] | Metrics collection, health monitoring, trace emission |
| 3.1.9 | Implement `Policy` component | [ ] | Permission enforcement, constraint checking, constitutional rules |

### P3.2 Optimizer Skeleton

| # | Task | Status | Acceptance Criteria |
|---|---|---|---|
| 3.2.1 | Define Optimizer as meta-layer component | [ ] | Optimizer does not participate in task execution; only triggers on MetaCycle |
| 3.2.2 | Implement Optimizer interfaces | [ ] | `observe()`, `propose()`, `evaluate()`, `commit()` lifecycle hooks |
| 3.2.3 | Implement protected component boundaries | [ ] | Policy, Identity, Evaluation-QC cannot be modified without Human Review Gate |
| 3.2.4 | Define `PendingMutation` model | [ ] | Mutation proposals carry type (param/connection/template/code/policy), target, justification |

### P3.3 Cross-Component Wiring

| # | Task | Status | Acceptance Criteria |
|---|---|---|---|
| 3.3.1 | Define default connection topology | [ ] | 9 components wired via ConnectionEngine with standard data flow |
| 3.3.2 | Implement component dependency declarations | [ ] | Each component declares its required inputs and provided outputs |
| 3.3.3 | Verify orphan component detection | [ ] | Components with unresolved connections are flagged during assembly |

---

## MH-SP4 — Safety, Governance & Hot-Reload

**Goal:** Implement the four-level safety chain, three-tier sandbox, constitutional governance, automatic rollback, and the Suspend-Transform-Resume hot-reload protocol.

**Milestone target:** M2.2 — Safety & Governance Ready

### P4.1 Four-Level Safety Chain

| # | Task | Status | Acceptance Criteria |
|---|---|---|---|
| 4.1.1 | Implement Level 1: SandboxValidator | [ ] | Executes regression tests + historical failure replay in isolated environment |
| 4.1.2 | Implement Level 2: ABShadowTester | [ ] | Duplicates production traffic to candidate config; statistical significance test (paired t / Wilcoxon) |
| 4.1.3 | Implement Level 3: PolicyVeto | [ ] | Constitutional review against immutable rules (C-01 through C-05) and domain regulations (R-01 through R-03) |
| 4.1.4 | Implement Level 4: AutoRollback | [ ] | Observation window with Z-score anomaly detection; automatic rollback on regression |
| 4.1.5 | Implement Guard / Mutate / Reduce hooks | [ ] | Governance layer exposes policy extension points for veto, adjustment, and aggregation |
| 4.1.6 | Implement sequential gate pipeline | [ ] | Candidate must pass all 4 levels sequentially; failure at any level halts promotion |

### P4.2 Three-Tier Sandbox

| # | Task | Status | Acceptance Criteria |
|---|---|---|---|
| 4.2.1 | Implement V8/WASM sandbox tier | [ ] | <1ms overhead for simple logic validation |
| 4.2.2 | Implement gVisor sandbox tier | [ ] | ~50ms overhead for Python script execution |
| 4.2.3 | Implement Firecracker sandbox tier | [ ] | ~30ms startup for high-risk operation isolation |
| 4.2.4 | Implement risk-tier selection logic | [ ] | Component risk profile determines which sandbox tier to use |

### P4.3 Hot-Reload Protocol

| # | Task | Status | Acceptance Criteria |
|---|---|---|---|
| 4.3.1 | Implement `suspend()` on components | [ ] | Stops new message acceptance; drains current operations with configurable timeout |
| 4.3.2 | Implement state snapshot capture | [ ] | `suspend()` returns `state_snapshot` for checkpoint |
| 4.3.3 | Implement `transform_state()` migration | [ ] | Applies `τ: S_old × ΔP → S_new` transformation logic |
| 4.3.4 | Implement `resume(new_state)` on components | [ ] | Injects migrated state; resumes message processing |
| 4.3.5 | Implement checkpoint management | [ ] | GraphVersionManager stores state checkpoints for rollback |
| 4.3.6 | Implement Saga rollback for failed migrations | [ ] | Multi-step migration failures trigger compensating transactions |

---

## MH-SP5 — Observability, Audit & Provenance

**Goal:** Build the three-layer observation system, trace/replay mechanism, Merkle audit chain, and provenance tracking.

**Milestone target:** M2.3 — Observability Ready

### P5.1 Three-Layer Metrics

| # | Task | Status | Acceptance Criteria |
|---|---|---|---|
| 5.1.1 | Implement system-level metrics collection | [ ] | CPU, memory, I/O, network, component count, graph version count |
| 5.1.2 | Implement component-level metrics collection | [ ] | Per-component latency, throughput, error rate, resource usage |
| 5.1.3 | Implement task-level trace collection | [ ] | Per-task execution trajectory with timestamps and outcomes |

### P5.2 Trace & Replay

| # | Task | Status | Acceptance Criteria |
|---|---|---|---|
| 5.2.1 | Implement execution trajectory persistence | [ ] | Hot/warm/cold tiered storage for traces |
| 5.2.2 | Implement trace query interface | [ ] | Query by task ID, component, time range, outcome |
| 5.2.3 | Implement replay mechanism | [ ] | Historical executions can be replayed for diagnosis |

### P5.3 Merkle Audit Chain

| # | Task | Status | Acceptance Criteria |
|---|---|---|---|
| 5.3.1 | Implement PROV-based evidence object model | [ ] | Each state transition, mutation, and safety decision produces a signed evidence object with PROV mapping |
| 5.3.2 | Implement Merkle tree construction | [ ] | Evidence objects are leaves; Merkle root provides tamper-evident integrity |
| 5.3.3 | Implement provenance query | [ ] | "Why was this component modified?" → full provenance chain |
| 5.3.4 | Implement audit log persistence | [ ] | Merkle roots stored in append-only audit log |
| 5.3.5 | Implement counter-factual diagnosis interfaces | [ ] | compare traces, search failures, and replay execution from checkpoints |

---

## MH-SP6 — Optimizer & Self-Growth Engine

**Goal:** Activate the self-modification loop with evolutionary search, GIN state encoding, convergence criteria, and template-based code generation.

**Milestone target:** M3.1 — Self-Growth Ready

### P6.1 Trigger & Search

| # | Task | Status | Acceptance Criteria |
|---|---|---|---|
| 6.1.1 | Implement layered trigger mechanism (5 levels) | [ ] | L1: param adjustment → L2: connection rewiring → L3: template swap → L4: code patch → L5: behavior policy |
| 6.1.2 | Implement trigger gating with configurable thresholds | [ ] | Optimization only triggers when performance delta exceeds threshold |
| 6.1.3 | Implement Phase A: local parameter search | [ ] | Population-based search with crossover and mutation operators |
| 6.1.4 | Implement Phase B: topology & template search | [ ] | Connection rewiring and template swaps are explored under contract pruning |
| 6.1.5 | Implement Phase C: constrained synthesis | [ ] | LLM-based proposer emits bounded config/code patches |
| 6.1.6 | Implement Bayesian optimization (parameter tuning) | [ ] | Gaussian process surrogate for continuous parameter search |
| 6.1.7 | Implement optional RL enhancement | [ ] | PPO/SAC as optional strategy for sequential decision problems |

### P6.2 State Encoding & Action Space

| # | Task | Status | Acceptance Criteria |
|---|---|---|---|
| 6.2.1 | Implement GIN-based state encoder | [ ] | Graph Isomorphism Network encodes current component topology as fixed-dimension vector |
| 6.2.2 | Implement 4-layer action space funnel | [ ] | Parameter → Connection → Template/Code → Policy; funnel narrows from safe to impactful |
| 6.2.3 | Implement contract-driven pruning | [ ] | Prune incompatible actions before search to reduce exploration space |

### P6.3 Convergence & Feedback

| # | Task | Status | Acceptance Criteria |
|---|---|---|---|
| 6.3.1 | Implement triple convergence criteria | [ ] | Hypervolume stability + statistical significance + complexity cap |
| 6.3.2 | Implement reward/fitness functions | [ ] | Multi-objective: task success rate, latency, resource usage, token budget compliance |
| 6.3.3 | Implement negative reward feedback loop | [ ] | Safety-chain failures and rollbacks feed back as penalty signals |
| 6.3.4 | Implement Dead End detection | [ ] | Same intent failed 3 consecutive times → marked as Dead End in Memory |
| 6.3.5 | Implement non-Markovian state caveat | [ ] | Optimizer acknowledges partial observability; state includes trajectory summary |

### P6.4 Template Library & Code Generation

| # | Task | Status | Acceptance Criteria |
|---|---|---|---|
| 6.4.1 | Implement template registry | [ ] | Curated templates: BM25Retriever, ContextPruner, ChainOfThoughtPlanner, RetryWithBackoff, etc. |
| 6.4.2 | Implement slot-filling engine | [ ] | Templates declare required slots; engine fills from component capabilities |
| 6.4.3 | Implement code generation pipeline | [ ] | Template selection → parameter filling → code generation → mypy check → sandbox test → register |
| 6.4.4 | Implement migration adapter system | [ ] | Template version changes trigger migration adapters for state transformation |

---

## MH-SP7 — Productization, Extension Ecosystem & Rollout

**Goal:** Make Meta-Harness a stable, documented, extensible platform that third-party developers can build upon.

**Milestone target:** M4 — Productized Meta-Harness

### P7.1 Documentation & Extension Guide

| # | Task | Status | Acceptance Criteria |
|---|---|---|---|
| 7.1.1 | Write extension guide for custom components | [ ] | Step-by-step: manifest → implement → test → register → deploy |
| 7.1.2 | Document candidate-graph-first workflow | [ ] | Developers understand why changes go through pending → candidate → safety → active |
| 7.1.3 | Document protected component constraints | [ ] | Clear warnings about which components cannot be modified without Human Review Gate |
| 7.1.4 | Document Optimizer extension points | [ ] | How to add custom search strategies, fitness functions, trigger rules |

### P7.2 Evaluation & Rollout

| # | Task | Status | Acceptance Criteria |
|---|---|---|---|
| 7.2.1 | Create evaluation fixtures for safety chain | [ ] | At least one fixture per safety level: sandbox pass/fail, A/B reject, veto, rollback |
| 7.2.2 | Create evaluation fixtures for hot-reload | [ ] | Suspend-Transform-Resume with state migration and rollback |
| 7.2.3 | Create evaluation fixtures for Optimizer | [ ] | Convergence detection, Dead End marking, reward feedback |
| 7.2.4 | Verify API stability guarantees | [ ] | Public SDK interfaces stable; internal implementation can change |
| 7.2.5 | Performance benchmarks | [ ] | Boot time, safety-chain latency, hot-reload downtime measured and documented |

---

## Cross-Project Dependencies & Critical Path

```text
MH-SP1 (Component SDK & Core Infrastructure)
   ├──> MH-SP2 (Connection Engine & Graph Management)
   │      └──> MH-SP4 (Safety, Governance & Hot-Reload)
   ├──> MH-SP3 (Core Components Implementation)
   │      ├──> MH-SP4 (Safety, Governance & Hot-Reload)
   │      │      └──> hot-reload also needs SP5-minimal
   │      └──> MH-SP5 (Observability, Audit & Provenance)
   │             └──> MH-SP6 (Optimizer & Self-Growth Engine)
   │                    ├──> MH-SP4 required (safety chain)
   │                    └──> MH-SP5 required (fitness signals)
   └──> MH-SP7 (Productization & Rollout) — starts after MH-SP1–SP6 stabilize
```

### Strict Ordering

1. `HarnessComponent` and `ComponentManifest` must exist before any components can be built.
2. `ConnectionEngine` and `GraphVersionManager` must exist before multi-component wiring.
3. Core components (9 + Optimizer) must be assembled and activated before the safety chain can validate real configurations.
4. **Minimal observability (metrics, trace IDs, audit event schema) must land in SP3** — the safety chain's Level 4 (AutoRollback) and shadow testing both depend on metrics collection.
5. The safety chain must be operational before the Optimizer can propose real mutations.
6. **Hot-reload (SP4 §4.3) depends on component state contracts from SP3** — at minimum Memory and Runtime must define stateful behavior before suspend/resume is meaningful.
7. The Optimizer's evolutionary search must work before template/code generation is useful.

### Parallel Opportunities

- MH-SP2 and MH-SP3 can run in parallel after MH-SP1 stabilizes.
- MH-SP5 can start after MH-SP3 core components provide metrics endpoints.
- Documentation (MH-SP7) can begin incrementally once each SP's interface stabilizes.
- Template library design can start in parallel with MH-SP6 implementation.

---

## Phase-to-Version Mapping

| Version | Milestone | Capabilities |
|---|---|---|
| v0.1 | M1.1 | Component SDK: HarnessComponent, HarnessAPI, ComponentRuntime, Discovery, Loader, Registry |
| v0.2 | M1.2 | Connection Engine: ConnectionEngine, EventBus, CompatibilityValidator, GraphVersionManager |
| **v0.5** | **M1.5** | **MVP: boot → candidate graph → commit/rollback → one stable end-to-end topology** |
| v1.0 | M2.1 | Core Components: 9 components + Optimizer skeleton, default topology, minimal observability built-in |
| v1.1 | M2.2 | Safety & Governance: 4-level safety chain, at least 1 sandbox tier, Suspend-Transform-Resume |
| v1.2 | M2.3 | Advanced Observability: Trace/Replay, Merkle audit, provenance queries |
| v2.0 | M3.1 | Self-Growth: Evolutionary search, GIN encoder, action funnel, convergence, template/code gen |
| v3.0 | M4 | Productized: stable APIs, extension guide, evaluation fixtures, ecosystem tooling |

### What v0.5 MVP Excludes

The minimal shippable v0.5 deliberately excludes:

- **RL enhancement** — evolutionary search is sufficient for initial self-growth
- **Firecracker sandbox** — WASM + gVisor cover most use cases; Firecracker is a later stretch goal
- **Full Merkle provenance** — simple audit log suffices initially; Merkle chain is v1.2
- **Template code generation** — manual component authoring first; codegen is v2.0
- **Statistical shadow testing** — basic regression comparison first; paired t-tests are a stretch goal
- **GIN state encoding** — feature-vector state representation first; GIN is v2.0

---

## Risk Register

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| Component SDK scope creeps without clear boundaries | High | Medium | Define SDK interface contracts first; stabilize before building downstream |
| Graph versioning creates storage/memory overhead | Medium | Medium | Implement version retirement and archival; cap active versions |
| Four-level safety chain adds unacceptable latency | High | Medium | Tier-based gating: low-risk changes skip heavy levels |
| Optimizer proposes unsafe mutations that bypass safety chain | High | Low | Safety chain is independent of Optimizer; cannot be bypassed |
| Suspend-Transform-Resume state migration loses data | High | Medium | Mandatory checkpoint before migration; Saga rollback on failure |
| Evolutionary search converges too slowly | Medium | Medium | Hybrid with Bayesian optimization; configurable population size |
| Template slot-filling generates incorrect code | Medium | High | Sandbox test as mandatory gate; mypy check before registration |
| Merkle audit chain grows unbounded | Low | Medium | Periodic pruning with configurable retention window |
| Hot-reload causes message loss during suspend | Medium | Medium | Message buffer with configurable drain timeout |
| Graph-version retirement removes needed rollback targets | High | Low | Minimum retention count; manual pin for critical versions |

---

## Acceptance Criteria

### v0.1 Gate (SDK Ready)
- [ ] `HarnessComponent` base class supports full staged lifecycle
- [ ] `ComponentDiscovery` scans all 4 sources
- [ ] `ComponentLoader` validates manifests and resolves dependencies
- [ ] `ComponentRegistry` supports pending zone with atomic commit/rollback
- [ ] At least one test component can be discovered, loaded, assembled, and activated

### v0.2 Gate (Connection Ready)
- [ ] `ConnectionEngine` routes data between connected component ports
- [ ] `CompatibilityValidator` enforces all 5 compatibility rules
- [ ] `GraphVersionManager` creates immutable snapshots and tracks version lifecycle
- [ ] Candidate graph can be assembled, validated, and committed as active graph

### v1.0 Gate (Core Components Ready)
- [ ] All 9 core components registered and wired in default topology
- [ ] Optimizer skeleton can observe metrics and propose mutations (no execution)
- [ ] No orphan components in default configuration
- [ ] Component dependency graph has no cycles
- [ ] Minimal observability built-in: metrics endpoint, trace IDs, audit event schema

### v0.5 Gate (MVP — Minimal Viable Harness)
- [ ] Boot succeeds with at least 2 components discovered, loaded, assembled, and activated
- [ ] Candidate graph can be assembled from pending components/connections
- [ ] CompatibilityValidator accepts valid topologies and rejects invalid ones
- [ ] Candidate graph can be committed as active graph version
- [ ] Active graph can be rolled back to previous version
- [ ] One end-to-end topology runs a task from input to output

### v1.1 Gate (Safety Ready)
- [ ] 4-level safety chain rejects invalid candidate configurations
- [ ] At least 1 sandbox tier operational (WASM)
- [ ] Suspend-Transform-Resume completes with zero message loss in test (stretch: 2 sandbox tiers)
- [ ] Saga rollback correctly compensates failed multi-step migrations

### v1.2 Gate (Observability Ready)
- [ ] 3-layer metrics collected and queryable
- [ ] Execution trajectories persist to tiered storage
- [ ] Merkle audit chain produces tamper-evident evidence for every mutation
- [ ] Provenance query can trace "why was this component modified"

### v2.0 Gate (Self-Growth Ready)
- [ ] Optimizer can trigger, search, propose, and evaluate candidate mutations
- [ ] At least 3 optimization cycles complete with measurable fitness improvement
- [ ] Convergence detection correctly stops search
- [ ] Template slot-filling generates at least 3 working components (stretch: 5)
- [ ] Dead End detection prevents repeated failed optimization attempts
- [ ] GIN state encoding produces distinguishable vectors for different topologies (stretch: similarity preservation)

### v3.0 Gate (Productized)
- [ ] Extension guide covers custom component, custom search strategy, custom template
- [ ] At least one end-to-end scenario: Optimizer proposes → Safety chain validates → Hot-reload applies → Observability confirms
- [ ] Public API surface is stable and documented
- [ ] Evaluation fixtures cover all major failure modes (safety reject, rollback, migration failure)
