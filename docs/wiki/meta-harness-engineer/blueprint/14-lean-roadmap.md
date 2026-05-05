# Lean Extension Roadmap

> Status: proposed
> Scope: formal execution roadmap for `metaharness_ext.lean`.

## Technical Alignment Notes

This roadmap starts from no landed Lean extension package in the MHE tree. It therefore treats all Lean extension work as proposed until code, tests, manifests, and docs are added.

The roadmap follows MHE greenfield extension practice:

- package under `src/metaharness_ext/lean/`;
- tests named `tests/test_metaharness_lean_*.py`;
- JSON manifests beside component modules;
- design wiki under `docs/wiki/meta-harness-engineer/lean-engine-wiki/`;
- baseline tests use mocked subprocess/runtime behavior unless real Lean execution is explicitly enabled.

## Current State Snapshot

### Landed code truth

No `metaharness_ext.lean` package is currently assumed to exist.

### Landed tests truth

No Lean extension tests are currently assumed to exist.

### Docs truth

This roadmap and the companion blueprint / implementation plan define proposed design and sequencing only. They do not claim implementation support.

### Main remaining gaps

- package scaffold;
- typed contracts;
- slots and capabilities;
- component declarations;
- JSON manifests;
- mocked runtime components;
- validation and evidence semantics;
- focused tests;
- optional real Lean smoke path.

## Recommended Execution Order

```text
Phase 0 -> Phase 1 -> Phase 2 -> Phase 3 -> Phase 4
```

This order proves the MHE contract and manifest surface before adding real Lean execution. That prevents a common overclaim: treating a successful local `lake env lean` experiment as if the extension’s MHE lifecycle, evidence, and governance seams are already implemented.

## Completed Items

No implementation items are completed yet.

The current completed design artifacts are expected to be:

- `14-lean-extension-blueprint.md`;
- `14-lean-roadmap.md`;
- `14-lean-implementation-plan.md`;
- `lean-engine-wiki/README.md`.

## Remaining Slices

### Slice 1: Contract and manifest baseline

Create package scaffold, contracts, slots, capabilities, manifests, and manifest parity tests. No real Lean execution.

### Slice 2: Mocked environment and execution chain

Add mocked environment probe, blueprint compiler, workspace, executor, validator, and evidence components with focused tests.

### Slice 3: Dry-run command/workspace planning

Render command manifests and workspace plans for Lean/Lake checks without executing them.

### Slice 4: Opt-in real Lean smoke

Add gated `MHE_RUN_REAL_LEAN=1` smoke support against a known local Lean project fixture or externally provided fixture path.

### Slice 5: Proof-audit and statement-tracking hardening

Add structured detection for `sorry`, statement drift, changed declarations, and incomplete proof evidence.

### Slice 6: Blueprint-guided multi-item formalization

Add dependency-aware blueprint handling for formalization projects, including item status and per-item evidence references.

### Slice 7: Optional theorem-search and discussion adapters

Add adapter surfaces for theorem search or external strategy discussion only after baseline evidence and policy boundaries are stable.

## Phase Map

### Phase 0: Design and scaffold

- **Status**: proposed
- **Goal**: establish package, docs, and manifest-compatible skeleton.
- **Key tasks**:
  - create `src/metaharness_ext/lean/`;
  - define contracts, capabilities, and slots;
  - add component class skeletons;
  - add package and component manifests;
  - add import, contract, and manifest tests.
- **Acceptance criteria**:
  - package imports successfully;
  - manifests match declared interfaces;
  - contracts serialize and validate;
  - docs state proposed status and do not claim runtime support.
- **Evidence**:
  - `python -m pytest tests/test_metaharness_lean_manifest.py -q`;
  - `python -m pytest tests/test_metaharness_lean_contracts.py -q`;
  - `ruff check src/metaharness_ext/lean tests/test_metaharness_lean_*.py`.

### Phase 1: Mocked runtime baseline

- **Status**: proposed
- **Goal**: prove the component chain works through mocked Lean outcomes.
- **Key tasks**:
  - implement environment probe with fake project discovery inputs;
  - compile `LeanTaskSpec` into `LeanRunPlan`;
  - produce mocked `LeanRunArtifact` objects;
  - classify validation reports for success, error, `sorry`, timeout, and skip;
  - emit evidence bundles preserving task, plan, run, artifact, and validation IDs.
- **Acceptance criteria**:
  - all mocked execution paths are deterministic;
  - validation distinguishes compiler success from no-`sorry` completeness;
  - evidence identity provenance is preserved.
- **Evidence**:
  - `python -m pytest tests/test_metaharness_lean_environment.py -q`;
  - `python -m pytest tests/test_metaharness_lean_executor.py -q`;
  - `python -m pytest tests/test_metaharness_lean_validator.py -q`.

### Phase 2: Dry-run Lean command planning

- **Status**: proposed
- **Goal**: render truthful Lean/Lake command plans without executing external tools.
- **Key tasks**:
  - discover project root candidates;
  - detect `lean-toolchain`, `lakefile.lean`, and `lakefile.toml`;
  - render command manifests for `lake env lean <target>`;
  - write dry-run artifacts under `.runs/`;
  - mark dry-run evidence as planned, not executed.
- **Acceptance criteria**:
  - standalone `.lean` files outside a Lake project produce an environment finding;
  - dry-run artifacts do not imply real Lean execution;
  - output roots stay under `.runs/`.
- **Evidence**:
  - focused dry-run tests;
  - no real Lean dependency in default CI.

### Phase 3: Opt-in real Lean smoke

- **Status**: future proposed
- **Goal**: verify the extension can execute a real local Lean check when the environment is explicitly enabled.
- **Key tasks**:
  - add `MHE_RUN_REAL_LEAN=1` gate;
  - add fixture path support, such as `MHE_REAL_LEAN_PROJECT_ROOT`;
  - run `lake env lean` with timeout and captured outputs;
  - hash command manifest and output logs;
  - classify missing prerequisites as skip, not failure.
- **Acceptance criteria**:
  - real tests are opt-in and marked;
  - skipped environments produce reviewable skip evidence;
  - successful real checks include command, version/project facts, logs, and validation refs.
- **Evidence**:
  - `python -m pytest -m lean_real tests/test_metaharness_lean_real_smoke.py -q` when enabled.

### Phase 4: Blueprint and proof-audit hardening

- **Status**: future proposed
- **Goal**: support dependency-aware formalization projects and rigorous proof audit outputs.
- **Key tasks**:
  - parse or accept structured blueprint items;
  - enforce dependency order;
  - track per-item status;
  - detect statement drift and changed declarations;
  - preserve per-item validation and artifact refs.
- **Acceptance criteria**:
  - dependency errors are caught before execution;
  - per-item evidence is not collapsed into a single derived ID;
  - audit mode can run without proof mutation.
- **Evidence**:
  - blueprint compiler tests;
  - proof-audit validator tests;
  - docs support matrix updated to reflect implemented boundaries.

## Risks / Dependencies

| Risk | Impact | Mitigation |
|---|---|---|
| Local Lean is unavailable | real smoke cannot run | keep default tests mocked and classify real smoke as opt-in skip |
| Dry-run overclaim | docs may imply execution | validation and docs must mark dry-run as planned only |
| Statement mutation | generated proof work may alter theorem meaning | add statement tracking before autonomous proof repair slices |
| Proof style overclaim | compiler success may be described as Mathlib-quality | evidence/policy must distinguish formal validity from style acceptance |
| External tool sprawl | theorem search and LLM discussion could broaden scope | defer adapters until baseline lifecycle is verified |

## Support Matrix Target

| Capability | Phase 0 | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|---|---|---|---|---|---|
| Contracts and manifests | proposed | tested | tested | tested | tested |
| Mocked Lean execution | none | tested | tested | tested | tested |
| Dry-run command planning | none | none | tested | tested | tested |
| Real Lean check | none | none | none | opt-in | opt-in |
| Blueprint DAG | docs only | docs only | partial | partial | tested |
| Statement drift audit | none | partial | partial | partial | tested |
| External theorem search | none | none | none | none | future |

## Stop Gates

Do not proceed to real Lean execution until:

- manifests match component declarations;
- mocked executor and validator paths are tested;
- dry-run outputs are correctly labeled as non-executed;
- docs do not claim autonomous proving support.

Do not proceed to theorem-search or external LLM adapters until:

- proof task contracts are stable;
- evidence and policy reports preserve real run and validation IDs;
- statement drift rules are implemented or explicitly out of scope.
