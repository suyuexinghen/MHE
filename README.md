# Meta-Harness Engineering

Meta-Harness Engineering (`MHE`) is a Python reference runtime for the Meta-Harness model. It provides a typed component SDK, manifest-driven discovery, candidate-first graph assembly, semantic validation, versioned routing, hot-swap state migration, safety gating, provenance, optimizer scaffolding, assembly/instantiation governance, benchmark comparison surfaces, and a benchmark-backed research-loop CLI.

MHE is best understood as a **research and engineering runtime**, not a production orchestrator. The runtime treats the **internal graph model** as the source of authority. XML files are import/configuration inputs, not the in-memory runtime truth.

## Current Scope

The current tree includes:

- a typed SDK for ports, events, slots, capabilities, manifests, and runtime injection
- manifest loading, multi-source discovery, static validation, and dependency ordering
- registry and graph models for component declarations, slot bindings, candidate graphs, snapshots, and validation reports
- a `ConnectionEngine` for staging, validating, committing, routing, and rolling back graph snapshots
- structural XML validation plus semantic graph validation
- a boot orchestrator, `HarnessRuntime`, for discovery, activation, handler registration, identity-boundary injection, and migration-adapter collection
- hot-reload support with checkpoints, migration adapters, saga compensation, and observation-window evaluation
- safety modules for sandbox validation, policy gates, shadow checks, rollback hooks, and assembly-health policy checks
- provenance primitives for evidence, audit logging, Merkle anchoring, artifact snapshots, and external evidence references
- optimizer scaffolding for proposal generation, search, convergence tracking, and mutation templates
- assembly/instantiation governance for lineage records, copy-count tracking, dependency DAG snapshots, execution-mode classification, instantiation records, and selection lifecycle state
- assembly metrics reports that summarize assembly health, lineage, reuse, instantiation evidence, and selection state without making scientific-validity claims
- benchmark and research CLI surfaces for extension/direct/agent comparison, approval-gate checks, and benchmark-backed research-loop handoff
- domain extension packages under `src/metaharness_ext/`
- examples, manifests, local `.claude/skills/`, and a pytest suite for the runtime and extensions

## Maturity

MHE is intentionally modular, explicit, and testable. Several subsystems are still reference-grade:

- most runtime stores are local or in-memory by default
- bundled core components are demonstration components rather than production service integrations
- CLI surfaces cover demo, validation, metrics reporting, benchmark comparison, approval checks, research-loop handoff, and version reporting
- hot-swap observation depends on supplied metrics/events rather than a fully integrated live metrics backend
- optimizer outputs are proposals; they do not directly mutate the active graph
- metrics and benchmark reports improve governance and auditability but do not prove scientific validity by themselves

MHE is suitable for architecture experiments, contract evolution, graph-validation work, hot-reload protocol development, safety-chain testing, provenance research, optimizer research, benchmark workflow research, and extension prototyping.

## Extension Packages

Domain extensions live under `src/metaharness_ext/`. Their maturity varies by package; use each extension's wiki, tests, and user guides as the source of truth.

| Package | Purpose | Current Notes |
|---|---|---|
| `metaharness_ext.ai4pde` | PDE-oriented scientific-agent workflows | Provides typed PDE task, planning, solving, validation, and evidence surfaces. |
| `metaharness_ext.nektar` | Nektar++ solver workflows | Wraps session compilation, solver execution, postprocess, validation, and convergence studies. Real solver paths remain opt-in and externally evidenced. |
| `metaharness_ext.deepmd` | DeePMD-kit / DP-GEN workflows | Provides environment probing, config compilation, execution, validation, evidence, policy, and study support. |
| `metaharness_ext.jedi` | JEDI workflow control surfaces | Supports `validate_only` / staged / real-run style boundaries mapped to core `ExecutionMode`; real-run claims require external receipts/logs and explicit evidence refs. |
| `metaharness_ext.abacus` | ABACUS materials-simulation workflows | Design and typed boundaries are present; scientific approval remains blocked until real fixtures, reviewed tolerances, and repeated real evidence exist. |
| `metaharness_ext.qcompute` | Quantum-computing workflows | Provides Qiskit Aer, PennyLane, gated Quafu, noise mitigation, studies, VQE, evidence, and governance paths; simulation and dry-run paths are not real hardware execution, and Quafu remains token/env gated. |
| `metaharness_ext.octave` | GNU Octave numerical workflows | Provides native-script compilation, dry-run/real-tool boundaries, validation/evidence reports, and benchmark cases for Octave-style numerical tasks. |
| `metaharness_ext.fealpy` | FEALPy finite-element workflows | Provides typed PDE/FEM problem surfaces, dry-run evidence, optional real-tool execution gates, and benchmark comparison support. |
| `metaharness_ext.pycfd` | PyCFD-style computational-fluid workflows | Provides PDE/FVM workflow contracts, evidence bundles, dry-run and optional real-source execution gates, and comparison benchmarks. |
| `metaharness_ext.boutpp` | BOUT++ plasma/PDE workflows | Provides typed case specs, `BOUT.inp` rendering, command assembly, dry-run usage validation, and gated real smoke methodology. |
| `metaharness_ext.moose` | MOOSE FEM simulation integration | Provides FEM simulation contract boundaries, blueprint/roadmap docs, and implementation scaffolding for gated real-tool workflows. |

Primary extension docs:

- `docs/qcompute-user-manual.md` — user-facing QCompute usage and testing guide
- `docs/wiki/meta-harness-engineer/qcompute-engine-wiki/` — QCompute design and tested support matrix
- `docs/wiki/meta-harness-engineer/ai4pde-agent-wiki/` — AI4PDE design wiki
- `docs/wiki/meta-harness-engineer/nektar-engine-wiki/` — Nektar design wiki
- `docs/wiki/meta-harness-engineer/deepmd-engine-wiki/` — DeepMD design wiki
- `docs/wiki/meta-harness-engineer/jedi-engine-wiki/` — JEDI design wiki
- `docs/wiki/meta-harness-engineer/abacus-engine-wiki/` — ABACUS design wiki
- `docs/wiki/meta-harness-engineer/octave-engine-wiki/` — Octave design wiki
- `docs/wiki/meta-harness-engineer/fealpy-engine-wiki/` — FEALPy design wiki
- `docs/wiki/meta-harness-engineer/pycfd-engine-wiki/` — PyCFD design wiki
- `docs/wiki/meta-harness-engineer/blueprint/10-boutpp-extension-blueprint.md` — BOUT++ extension blueprint
- `docs/wiki/meta-harness-engineer/blueprint/11-moose-extension-blueprint.md` — MOOSE extension blueprint

## Repository Layout

```text
MHE/
├── README.md
├── pyproject.toml
├── .claude/
│   ├── skills/
│   └── worktrees/                 # local/ephemeral worktrees; not canonical docs
├── docs/
│   ├── README.md
│   ├── USER_GUIDE.md
│   ├── TEST_GUIDE.md
│   ├── qcompute-user-manual.md
│   └── wiki/
├── examples/
│   ├── graphs/
│   ├── manifests/
│   ├── qcompute/
│   └── research/
├── src/
│   ├── metaharness/
│   └── metaharness_ext/
│       ├── abacus/
│       ├── ai4pde/
│       ├── boutpp/
│       ├── deepmd/
│       ├── fealpy/
│       ├── jedi/
│       ├── moose/
│       ├── nektar/
│       ├── octave/
│       ├── pycfd/
│       └── qcompute/
└── tests/
```

## Requirements

Package metadata declares:

- Python `>=3.11`
- `pydantic>=2.12,<3`

Development tooling uses:

- `pytest>=9,<10`
- `ruff==0.15.6`
- Ruff target version `py313`

Python 3.13 is the safest match for the current development configuration, while the package remains declared for Python `>=3.11`.

Some extensions require optional external tools or libraries. For example, QCompute simulator paths require `qiskit` / `qiskit-aer`, and Quafu hardware use requires explicit environment gating plus a token. Nektar++, Octave, FEALPy, PyCFD, BOUT++, MOOSE, ABACUS, JEDI, and DeePMD/DP-GEN real-tool paths likewise require the relevant local software, explicit opt-in, and external evidence before making real-execution claims.

## Install

From this `MHE/` directory:

```bash
pip install -e .
```

For development tools:

```bash
pip install -e '.[dev]'
```

Editable installation provides these console scripts:

```bash
metaharness version
metaharness demo
metaharness-demo
ai4pde-demo
```

You can also run from source without installation:

```bash
PYTHONPATH=src python -m metaharness.cli version
```

## Quick Start

Run the minimal demo:

```bash
PYTHONPATH=src python -m metaharness.demo
```

Expected output shape:

```text
topology=minimal
graph_version=1
trace_id=trace-demo-1
task=demo task
runtime_status=runtime-ok
executor_status=executed
score=1.0
```

Run the expanded demo:

```bash
PYTHONPATH=src python -m metaharness.cli demo --topology expanded --async-mode
```

Validate an XML graph structurally:

```bash
PYTHONPATH=src python -m metaharness.cli validate examples/graphs/minimal-happy-path.xml
```

Validate with manifests and semantic checks:

```bash
PYTHONPATH=src python -m metaharness.cli validate \
  examples/graphs/minimal-expanded.xml \
  --manifests examples/manifests/baseline
```

Generate an assembly metrics report:

```bash
PYTHONPATH=src python -m metaharness.cli metrics assembly \
  --graph examples/graphs/minimal-happy-path.xml \
  --manifests examples/manifests/baseline \
  --markdown-report .runs/assembly-metrics.md
```

Assembly metrics summarize lineage, copy count, dependency depth, instantiation status, and selection lifecycle evidence. They do **not** prove scientific validity, numerical correctness, or real-world execution.

Run a dry-run benchmark comparison workflow:

```bash
PYTHONPATH=src python -m metaharness.cli benchmark-run \
  --suite fealpy-pde \
  --lanes extension,direct \
  --cases poisson2d \
  --runs-root .runs

PYTHONPATH=src python -m metaharness.cli benchmark-compare \
  --suite fealpy-pde \
  --runs-root .runs

PYTHONPATH=src python -m metaharness.cli benchmark-approval-check \
  --suite fealpy-pde \
  --cases poisson2d
```

Benchmark comparison and approval checks support workflow/reporting claims only. Dry-run evidence, CI success, or agent-generated summaries must not be described as scientific approval or real-tool verification.

Run the benchmark-backed research-loop MVP:

```bash
PYTHONPATH=src python -m metaharness.cli research-run \
  --question examples/research/fealpy_poisson_question.json \
  --benchmark-runs-root .runs \
  --suite fealpy-pde \
  --cases poisson2d \
  --lanes extension \
  --runs-root .runs/research \
  --output-format json
```

`research-run` builds a deterministic research-loop trace from benchmark summaries. It does not claim autonomous scientific discovery, generalized benchmark approval, or external validation unless those references are present in the input evidence.

Validation exit codes:

- `0` success
- `2` structural validation failure
- `3` semantic validation failure

## Demo Graphs

The minimal graph routes:

```text
Gateway -> Runtime -> Executor -> Evaluation
```

The expanded graph routes:

```text
Gateway -> Runtime -> Planner -> Executor -> Evaluation
                                      └-> Memory
```

Example graph files include:

- `examples/graphs/minimal-happy-path.xml`
- `examples/graphs/minimal-expanded.xml`
- `examples/graphs/default-topology.xml`
- extension-specific graph examples such as `ai4pde-minimal.xml`, `deepmd-minimal.xml`, `jedi-minimal.xml`, `abacus-minimal.xml`, `qcompute-minimal.xml`, `octave-minimal.xml`, `fealpy-minimal.xml`, `pycfd-minimal.xml`, `boutpp-minimal.xml`, and `moose-minimal.xml`

## Programmatic Boot Example

The demo harness is the easiest way to see MHE in action, but the main boot orchestrator is `HarnessRuntime`.

```python
from pathlib import Path

from metaharness.config.xml_parser import parse_graph_xml
from metaharness.core.boot import HarnessRuntime
from metaharness.core.models import PendingConnectionSet
from metaharness.sdk.discovery import ComponentDiscovery

manifest_dir = Path("examples/manifests/baseline")
graph_path = Path("examples/graphs/minimal-happy-path.xml")

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

If a component declares migration adapters through `HarnessAPI`, they are collected into the runtime-owned hot-swap registry during boot.

## Core Concepts

### Manifest-driven components

A component is described by a manifest plus a Python implementation. The implementation declares ports and runtime hooks through `HarnessAPI`.

### Candidate-first graph model

The runtime stages a graph candidate, validates it, records the candidate, and only promotes it to the active graph on success.

### Assembly and instantiation governance

Assembly services record lineage, copy/reuse counts, dependency DAG snapshots, assembly-health summaries, execution-mode mappings, instantiation records, and selection lifecycle states. These records support reviewable governance and comparison reports; they do not by themselves prove scientific validity.

### Versioned routing

`ConnectionEngine` compiles committed edges into route bindings and dispatches payloads by source port. Routing modes currently include `sync`, `async`, `event`, and `shadow`.

### Identity boundary

Credential-like data is intentionally kept out of ordinary payloads. Components receive sanitized identity views plus attestation references.

### Hot swap and migration

Hot swap combines checkpoint capture, migration-adapter lookup, `transform_state()` fallback, resume hooks, optional observation-window rejection, and saga compensation on failure.

### Safety and provenance

Safety, audit, rollback, trace, and evidence modules are separate layers. They can be composed by runtime flows and extensions without making any single layer the whole control plane.

## Development Workflow

Run the default test suite:

```bash
pytest
```

The default pytest configuration excludes tests marked `nektar` and `quafu` because they require local external binaries or real hardware credentials.

Run focused tests:

```bash
pytest tests/test_boot.py
pytest tests/test_hot_reload.py
python -m pytest tests/test_metaharness_qcompute_*.py --tb=short -q
```

Run lint and format:

```bash
ruff check --fix .
ruff format .
```

## Documentation Map

- `docs/README.md` — documentation index
- `docs/USER_GUIDE.md` — user-oriented runtime guide
- `docs/TEST_GUIDE.md` — test tiers and validation guidance
- `docs/qcompute-user-manual.md` — QCompute usage, examples, hardware gate, and testing guide
- `docs/wiki/README.md` — full wiki entry point
- `docs/wiki/meta-harness-engineer/meta-harness-wiki/` — canonical MHE engineering wiki
- `docs/wiki/meta-harness-engineer/meta-harness-wiki/11-upgraded-core-framework-and-extension-improvement.md` — upgraded core framework and extension-improvement guide
- `docs/wiki/meta-harness-engineer/research-loop-mvp-wiki/` — benchmark-backed Research Loop MVP wiki
- `docs/wiki/meta-harness-engineer/benchmark/` — benchmark comparison methods, reports, conclusions, and approval-gating docs
- `docs/wiki/meta-harness-engineer/blueprint/12-benchmark-comparison-cicd-blueprint.md` — benchmark comparison CI/CD blueprint
- `docs/wiki/meta-harness-engineer/blueprint/12-benchmark-comparison-cicd-implementation-plan.md` — benchmark comparison CI/CD implementation plan
- `docs/wiki/meta-harness-engineer/blueprint/12-benchmark-comparison-cicd-roadmap.md` — benchmark comparison CI/CD roadmap
- `docs/wiki/meta-harness-engineer/blueprint/13-extension-core-improvement-blueprint.md` — extension core-improvement blueprint
- `docs/wiki/meta-harness-engineer/blueprint/13-extension-core-improvement-implementation-plan.md` — extension core-improvement implementation plan
- `docs/wiki/meta-harness-engineer/blueprint/13-extension-core-improvement-roadmap.md` — extension core-improvement roadmap
- `docs/wiki/meta-harness-engineer/blueprint/` — implementation plans, roadmaps, handoffs, and status material

## Known Limitations

- Most runtime stores are local or in-memory by default.
- Core demo components are intentionally simple.
- Optional extension paths may require external scientific software, quantum SDKs, or hardware credentials.
- Hardware-backed tests are gated and should not be treated as default CI coverage.
- Hot-reload observation is implemented, but live production metrics integration is outside the current reference runtime.
- Optimizer and governance modules are real code, but remain reference-grade in operational maturity.
- Simulation and dry-run outputs are not real execution evidence.
- External verification requires explicit external evidence references, not just local metrics or reports.

## Recommended Reading Order

If you are new to MHE, read in this order:

1. `README.md`
2. `docs/USER_GUIDE.md`
3. `docs/TEST_GUIDE.md`
4. `docs/TECHNICAL_MANUAL.md`
5. `docs/wiki/meta-harness-engineer/meta-harness-wiki/11-upgraded-core-framework-and-extension-improvement.md`
6. `docs/wiki/meta-harness-engineer/benchmark/README.md`
7. `docs/wiki/meta-harness-engineer/research-loop-mvp-wiki/README.md`
8. `src/metaharness/cli.py`
9. `src/metaharness/demo.py`
10. `src/metaharness/core/boot.py`
11. `src/metaharness/core/connection_engine.py`
12. `src/metaharness/core/validators.py`
13. `tests/`

## Summary

MHE is a contract-first, graph-based reference runtime that makes routing, validation, lifecycle, migration, safety, provenance, assembly, instantiation, selection, benchmark comparison, and research-loop handoff boundaries explicit. It is designed for Meta-Harness research and extension engineering, with clear separation between declarations and activation, candidate and active graph state, data-plane routing and control-plane governance, public payloads and protected identity material, dry-run/simulation and real execution, internal metrics and external verification, and hot-swap orchestration and rollback.
