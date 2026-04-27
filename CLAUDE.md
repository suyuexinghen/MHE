# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Run commands from this `MHE/` directory unless noted otherwise.

```bash
pip install -e '.[dev]'
```

```bash
PYTHONPATH=src python -m metaharness.cli version
PYTHONPATH=src python -m metaharness.demo
PYTHONPATH=src python -m metaharness.cli demo --topology expanded --async-mode
PYTHONPATH=src python -m metaharness.cli validate examples/graphs/minimal-happy-path.xml
PYTHONPATH=src python -m metaharness.cli validate examples/graphs/minimal-expanded.xml --manifests examples/manifests/baseline
```

```bash
ruff check .
ruff check --fix .
ruff format .
ruff format --check .
```

```bash
python -m pytest
python -m pytest tests/test_registry.py -q
python -m pytest tests/test_registry.py::test_registry_records_slot_and_capability_indexes -q
python -m pytest tests/test_metaharness_abacus_*.py -q
python -m pytest tests/test_metaharness_qcompute*.py --tb=short -q
```

Pytest defaults from `pyproject.toml` exclude tests marked `nektar` and `quafu`. Those tiers require local solver/hardware prerequisites and should stay opt-in.

## Architecture

MHE is a Python reference runtime for the Meta-Harness model. Treat the internal graph model as authoritative; XML files are import/configuration inputs rather than runtime truth.

The core package is `src/metaharness/`:

- `sdk/` defines the component surface: `HarnessComponent`, `HarnessAPI`, manifests, contracts, runtime injection, discovery, dependency resolution, and the staged `ComponentRegistry`.
- `core/connection_engine.py` stages candidate graphs, runs semantic validation, commits valid snapshots, loads route tables, emits payloads, and rolls back graph versions.
- `core/boot.py` contains `HarnessRuntime`, which composes discovery, manifest validation, dependency ordering, component activation, handler registration, safety gates, lifecycle tracking, session recovery, provenance, and mutation submission.
- `core/execution.py` provides the first-class async execution lifecycle service that records task submitted/running/completed/failed/cancelled session events around executor protocols.
- `config/` parses graph XML and performs XSD structural validation before optional semantic validation through manifests.
- `observability/`, `provenance/`, `safety/`, `hotreload/`, and `optimizer/` hold cross-cutting runtime services for sessions, artifact snapshots, audit/provenance graphs, policy gates, migration, and candidate generation.

Domain extensions live under `src/metaharness_ext/`. They generally follow a gateway-oriented pipeline: typed `contracts`, capability/slot declarations, `environment` probes, config/input compilers, executors, validators, evidence/policy/governance adapters, and optional study components. Current extension families include AI4PDE, Nektar, DeepMD/DP-GEN, JEDI, ABACUS, and QCompute.

`examples/graphs/` and `examples/manifests/` are the primary fixtures for graph validation and boot flows. `tests/` mirrors both core subsystems and extension families; extension tests usually use mocked binaries or patched subprocesses unless explicitly marked for external tools.

## Local Rules

- Keep generated runtime and test artifacts under `.runs/`, not the repository root.
- Preserve extension behavior when changing MHE core interfaces; run focused tests for affected extensions.
- Prefer existing wiki pages under `docs/wiki/` for architecture context instead of adding new top-level docs.
