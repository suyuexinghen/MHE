# Meta-Harness Engineering

Meta-Harness Engineering (`MHE`) is a Python reference runtime for the Meta-Harness model. It provides a typed component SDK, manifest-driven discovery, candidate-first graph assembly, semantic validation, versioned routing, hot-swap state migration, safety gating, provenance, and optimizer scaffolding.

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
- safety modules for sandbox validation, policy gates, shadow checks, and rollback hooks
- provenance primitives for evidence, audit logging, Merkle anchoring, and artifact snapshots
- optimizer scaffolding for proposal generation, search, convergence tracking, and mutation templates
- domain extension packages under `src/metaharness_ext/`
- examples, manifests, and a pytest suite for the runtime and extensions

## Maturity

MHE is intentionally modular, explicit, and testable. Several subsystems are still reference-grade:

- most runtime stores are local or in-memory by default
- bundled core components are demonstration components rather than production service integrations
- the CLI focuses on demo, validation, and version reporting
- hot-swap observation depends on supplied metrics/events rather than a fully integrated live metrics backend
- optimizer outputs are proposals; they do not directly mutate the active graph

MHE is suitable for architecture experiments, contract evolution, graph-validation work, hot-reload protocol development, safety-chain testing, provenance research, optimizer research, and extension prototyping.

## Extension Packages

Domain extensions live under `src/metaharness_ext/`. Their maturity varies by package; use each extension's wiki, tests, and user guides as the source of truth.

| Package | Purpose | Current Notes |
|---|---|---|
| `metaharness_ext.ai4pde` | PDE-oriented scientific-agent workflows | Provides typed PDE task, planning, solving, validation, and evidence surfaces. |
| `metaharness_ext.nektar` | Nektar++ solver workflows | Wraps session compilation, solver execution, postprocess, validation, and convergence studies. |
| `metaharness_ext.deepmd` | DeePMD-kit / DP-GEN workflows | Provides environment probing, config compilation, execution, validation, evidence, policy, and study support. |
| `metaharness_ext.jedi` | JEDI workflow control surfaces | Supports schema/validate/real-run style execution boundaries for JEDI-family workflows. |
| `metaharness_ext.abacus` | ABACUS materials-simulation workflows | In active development; design and typed boundaries are present, with remaining implementation work tracked in blueprint docs. |
| `metaharness_ext.qcompute` | Quantum-computing workflows | Provides Qiskit Aer, PennyLane, gated Quafu, noise mitigation, studies, VQE, evidence, and governance paths. |

Primary extension docs:

- `docs/qcompute-user-manual.md` — user-facing QCompute usage and testing guide
- `docs/wiki/meta-harness-engineer/qcompute-engine-wiki/` — QCompute design and tested support matrix
- `docs/wiki/meta-harness-engineer/ai4pde-agent-wiki/` — AI4PDE design wiki
- `docs/wiki/meta-harness-engineer/nektar-engine-wiki/` — Nektar design wiki
- `docs/wiki/meta-harness-engineer/deepmd-engine-wiki/` — DeepMD design wiki
- `docs/wiki/meta-harness-engineer/jedi-engine-wiki/` — JEDI design wiki
- `docs/wiki/meta-harness-engineer/abacus-engine-wiki/` — ABACUS design wiki

## Repository Layout

```text
MHE/
├── README.md
├── pyproject.toml
├── docs/
│   ├── README.md
│   ├── USER_GUIDE.md
│   ├── TEST_GUIDE.md
│   ├── qcompute-user-manual.md
│   └── wiki/
├── examples/
│   ├── graphs/
│   ├── manifests/
│   └── qcompute/
├── src/
│   ├── metaharness/
│   └── metaharness_ext/
│       ├── abacus/
│       ├── ai4pde/
│       ├── deepmd/
│       ├── jedi/
│       ├── nektar/
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

Python 3.13 is the safest match for the current development configuration.

Some extensions require optional external tools or libraries. For example, QCompute simulator paths require `qiskit` / `qiskit-aer`, and Quafu hardware use requires explicit environment gating plus a token. See the relevant extension guide before running optional external integrations.

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
- extension-specific graph examples such as `ai4pde-minimal.xml`, `deepmd-minimal.xml`, `jedi-minimal.xml`, and `abacus-minimal.xml`

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
- `docs/wiki/meta-harness-engineer/blueprint/` — implementation plans, roadmaps, handoffs, and status material

## Known Limitations

- Most runtime stores are local or in-memory by default.
- Core demo components are intentionally simple.
- Optional extension paths may require external scientific software, quantum SDKs, or hardware credentials.
- Hardware-backed tests are gated and should not be treated as default CI coverage.
- Hot-reload observation is implemented, but live production metrics integration is outside the current reference runtime.
- Optimizer and governance modules are real code, but remain reference-grade in operational maturity.

## Recommended Reading Order

If you are new to MHE, read in this order:

1. `README.md`
2. `docs/USER_GUIDE.md`
3. `docs/TEST_GUIDE.md`
4. `docs/TECHNICAL_MANUAL.md`
5. `src/metaharness/cli.py`
6. `src/metaharness/demo.py`
7. `src/metaharness/core/boot.py`
8. `src/metaharness/core/connection_engine.py`
9. `src/metaharness/core/validators.py`
10. `tests/`

## Summary

MHE is a contract-first, graph-based reference runtime that makes routing, validation, lifecycle, migration, safety, and provenance boundaries explicit. It is designed for Meta-Harness research and extension engineering, with clear separation between declarations and activation, candidate and active graph state, data-plane routing and control-plane governance, public payloads and protected identity material, and hot-swap orchestration and rollback.
