# Lean Extension Implementation Plan

> Status: proposed
> Executable implementation plan for the first slice of `metaharness_ext.lean`.

## Technical Alignment Notes

This plan targets only the first implementation slice: a contract and manifest baseline for a Lean extension. It intentionally avoids real Lean execution, autonomous proof search, theorem retrieval, and external LLM calls.

The design source is `14-lean-extension-blueprint.md`; the sequencing source is `14-lean-roadmap.md`.

## Objective

Create the smallest truthful Lean extension baseline inside MHE.

After this slice, the project should be able to claim only:

- `metaharness_ext.lean` has a package scaffold;
- Lean contracts, slots, and capabilities are defined;
- baseline component interfaces are declared;
- package and component manifests exist;
- focused tests verify imports, contracts, constants, and manifest parity.

It should not claim that Lean code can be executed, checked, repaired, or proven yet.

## Scope

### In scope

- package scaffold under `src/metaharness_ext/lean/`;
- typed contracts for Lean task, project, blueprint, plan, artifact, validation, and evidence objects;
- slot and capability constants;
- baseline component classes with `declare_interface()` methods;
- package and component JSON manifests;
- focused tests under `tests/test_metaharness_lean_*.py`;
- README/wiki wording that clearly states proposed or baseline status.

### Out of scope

- real `lake env lean` execution;
- subprocess invocation;
- temporary Lean workspace mutation;
- theorem search;
- external LLM discussion partners;
- proof golfing;
- autonomous subagent orchestration;
- benchmark comparison runs;
- updating global extension status tables unless the implementation lands and is verified.

## Current Baseline

No Lean extension code is currently assumed to be present.

Existing MHE extension conventions to follow:

- package shape follows `src/metaharness_ext/abacus/` and `src/metaharness_ext/qcompute/`;
- component classes should declare slots, inputs, outputs, and capabilities through `declare_interface()`;
- manifests should match component declaration snapshots;
- protected validator/evidence slots should be represented in both constants and manifest metadata;
- tests should be named `tests/test_metaharness_lean_<surface>.py`.

## Design Decisions For This Slice

### Contracts

Define Pydantic models only. Keep them independent of a local Lean installation.

Recommended models:

- `LeanProjectSpec`;
- `LeanBlueprintItem`;
- `LeanTaskSpec`;
- `LeanRunPlan`;
- `LeanRunArtifact`;
- `LeanValidationReport`;
- `LeanEvidenceBundle`.

Suggested enums or literals:

- task family: `formal_proof`, `formalization_project`, `proof_audit`;
- execution mode: `mocked`, `dry_run`, `real_check`;
- validation state: `environment_skipped`, `planned`, `executed`, `compiled_with_sorry`, `compiled_complete`, `failed`.

### Runtime / Execution

Only declare component interfaces. Component methods may be minimal or deterministic placeholders if the existing extension pattern expects callable behavior, but they should not call external tools.

### Validation / Evidence

The first slice should define validation and evidence contracts, not implement full diagnostic parsing.

### Manifests

Add one package manifest and one manifest per baseline component.

Recommended component IDs:

- `lean.gateway`;
- `lean.environment`;
- `lean.blueprint_compiler`;
- `lean.workspace`;
- `lean.executor`;
- `lean.validator`;
- `lean.evidence`.

### Naming / Semantics Constraints

- Use `lean` as the Python package name and manifest namespace.
- Use `Lean<Role>Component` class names, such as `LeanGatewayComponent`.
- Keep real execution gates out of this slice.
- Avoid wording that says the extension proves theorems before executor and validator behavior is implemented.

## Target Files

### Production files

```text
src/metaharness_ext/lean/__init__.py
src/metaharness_ext/lean/capabilities.py
src/metaharness_ext/lean/slots.py
src/metaharness_ext/lean/contracts.py
src/metaharness_ext/lean/gateway.py
src/metaharness_ext/lean/environment.py
src/metaharness_ext/lean/blueprint_compiler.py
src/metaharness_ext/lean/workspace.py
src/metaharness_ext/lean/executor.py
src/metaharness_ext/lean/validator.py
src/metaharness_ext/lean/evidence.py
```

### Manifest files

```text
src/metaharness_ext/lean/manifest.json
src/metaharness_ext/lean/gateway.json
src/metaharness_ext/lean/environment.json
src/metaharness_ext/lean/blueprint_compiler.json
src/metaharness_ext/lean/workspace.json
src/metaharness_ext/lean/executor.json
src/metaharness_ext/lean/validator.json
src/metaharness_ext/lean/evidence.json
```

### Tests

```text
tests/test_metaharness_lean_imports.py
tests/test_metaharness_lean_contracts.py
tests/test_metaharness_lean_manifest.py
tests/test_metaharness_lean_slots_capabilities.py
```

### Docs

```text
docs/wiki/meta-harness-engineer/blueprint/14-lean-extension-blueprint.md
docs/wiki/meta-harness-engineer/blueprint/14-lean-roadmap.md
docs/wiki/meta-harness-engineer/blueprint/14-lean-implementation-plan.md
docs/wiki/meta-harness-engineer/lean-engine-wiki/README.md
```

## Planned Changes

### 1. Contracts

Implement schema-only models with deterministic defaults and explicit family/mode/status literals.

Tests should cover:

- minimal valid task spec;
- formalization project with two blueprint items and a dependency;
- validation report with `compiled_with_sorry`;
- evidence bundle preserving task, plan, run, artifact, and validation IDs.

### 2. Slots and Capabilities

Add constants similar to existing extensions.

Suggested slots:

- `LEAN_GATEWAY_SLOT = "lean_gateway.primary"`;
- `LEAN_ENVIRONMENT_SLOT = "lean_environment.primary"`;
- `LEAN_BLUEPRINT_COMPILER_SLOT = "lean_blueprint_compiler.primary"`;
- `LEAN_WORKSPACE_SLOT = "lean_workspace.primary"`;
- `LEAN_EXECUTOR_SLOT = "lean_executor.primary"`;
- `LEAN_VALIDATOR_SLOT = "lean_validator.primary"`;
- `LEAN_EVIDENCE_SLOT = "lean_evidence.primary"`.

Suggested protected slots:

- `LEAN_VALIDATOR_SLOT`;
- `LEAN_EVIDENCE_SLOT`.

Suggested capabilities:

- `CAP_LEAN_TASK_INTAKE`;
- `CAP_LEAN_ENV_PROBE`;
- `CAP_LEAN_BLUEPRINT_COMPILE`;
- `CAP_LEAN_WORKSPACE_PREPARE`;
- `CAP_LEAN_EXECUTE`;
- `CAP_LEAN_VALIDATE`;
- `CAP_LEAN_EVIDENCE`.

### 3. Component Declarations

Each component should declare exactly the contracts it consumes and produces.

Minimum chain:

| Component | Input | Output | Capability |
|---|---|---|---|
| Gateway | external task payload or `LeanTaskSpec` | `LeanTaskSpec` | task intake |
| Environment | `LeanTaskSpec` | environment finding or enriched project spec | environment probe |
| Blueprint compiler | `LeanTaskSpec` | `LeanRunPlan` | blueprint compile |
| Workspace | `LeanRunPlan` | workspace plan/artifact seed | workspace prepare |
| Executor | `LeanRunPlan` | `LeanRunArtifact` | execute |
| Validator | `LeanRunArtifact` | `LeanValidationReport` | validate |
| Evidence | validation + artifacts | `LeanEvidenceBundle` | evidence |

### 4. Manifests

Create JSON manifests with entries pointing to the component classes. Keep manifest metadata conservative:

- sandbox tier should match no external process use in this slice;
- validator and evidence should mark protected slots;
- contracts should name the same inputs/outputs as `declare_interface()`.

### 5. Tests

Test manifest parity using the same style as existing extension manifest tests.

Recommended assertions:

- every manifest file exists;
- every component declares the expected slot and capability;
- manifest snapshot matches declaration snapshot;
- protected slots are present for validator and evidence;
- package `__init__.py` re-exports core models and components.

### 6. Docs / Handoff Sync

Do not update repository-level extension support tables until the code baseline lands and tests pass. If an index is updated later, it should say the Lean extension has a scaffolded contract/manifest baseline, not runtime execution support.

## Verification Plan

Run from `/home/linden/code/git/Aeloon/Aeloon-science-agent/MHE`:

```bash
PYTHONPATH=src python -m pytest tests/test_metaharness_lean_imports.py -q
PYTHONPATH=src python -m pytest tests/test_metaharness_lean_contracts.py -q
PYTHONPATH=src python -m pytest tests/test_metaharness_lean_manifest.py -q
PYTHONPATH=src python -m pytest tests/test_metaharness_lean_slots_capabilities.py -q
ruff check src/metaharness_ext/lean tests/test_metaharness_lean_*.py
```

No real Lean command should be needed for this slice.

## Fallback Strategy

### Preferred Path

Implement the full contract and manifest baseline in one slice.

### Safe Fallback

If the component chain is too broad, land only:

- `contracts.py`;
- `capabilities.py`;
- `slots.py`;
- `__init__.py`;
- package manifest;
- import and contract tests.

Then mark component manifests and parity tests as the next slice.

### Rollback Point

This slice should be easy to revert because it only adds a new package, tests, and docs. If partial support lands, docs must say scaffold-only or contracts-only.

### Truthfulness Rule

If only docs land, the extension remains proposed. If only contracts land, the extension is not runnable. If manifests land without executor behavior, the extension is manifest-visible but not execution-capable.

## Completion Criteria

The slice is complete only when:

- production files exist and import cleanly;
- tests pass for imports, contracts, slots/capabilities, and manifest parity;
- `ruff check` passes for the new package and tests;
- docs do not claim real Lean execution;
- an independent reviewer/verifier confirms the docs and tests match the implemented truth.
