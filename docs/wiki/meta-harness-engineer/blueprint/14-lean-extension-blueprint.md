# Lean Extension Blueprint

> Status: proposed
> Scope: formal implementation blueprint for `MHE/src/metaharness_ext/lean`.

## Technical Alignment Notes

This blueprint designs an MHE-native Lean extension. It learns from Numina-Lean-Agent design patterns, but it does not attempt to align with, wrap, or reproduce Numina-Lean-Agent.

The relevant design lessons are:

- use Lean feedback as a first-class runtime signal instead of treating proof checking as a final-only step;
- represent long formalization work through a dependency-aware blueprint rather than a single monolithic prompt;
- separate informal strategy generation, Lean statement formalization, proof execution, validation, and proof-quality review;
- isolate hard subgoals so long contexts do not contaminate every proof attempt;
- keep `sorry` and statement drift visible in validation artifacts rather than hiding incompleteness behind informal success claims.

The first implementation should remain MHE-native and reference-grade. It should use mocked subprocesses for ordinary tests and gate real Lean/Lake execution behind explicit opt-in environment checks.

## Goal

The Lean extension provides typed MHE surfaces for Lean proof-engineering workflows: checking Lean projects, compiling proof tasks into bounded run plans, executing proof attempts through a controlled workspace, validating proof artifacts, and preserving evidence for review.

The target boundary is the Lean project and proof workflow layer, not a trained theorem prover or a hosted proof-search service.

The design stance is: MHE owns contracts, lifecycle, validation, provenance, and governance; the Lean extension owns Lean-specific task semantics, project probing, blueprint compilation, proof-workspace preparation, execution adapters, and validation interpretation.

## Platform vs Domain Boundary

MHE core remains responsible for:

- component declaration and manifest discovery;
- candidate graph validation and activation;
- slots, capabilities, protected boundaries, and policy seams;
- execution lifecycle records, provenance, audit, and evidence references;
- assembly and instantiation governance;
- benchmark and research-loop comparison surfaces.

The Lean extension owns:

- Lean project discovery through `lean-toolchain`, `lakefile.lean`, or `lakefile.toml`;
- formal proof task and blueprint contracts;
- Lean command assembly for dry-run and opt-in real checks;
- parsing Lean diagnostics into MHE validation reports;
- detecting `sorry`, statement drift, missing imports, and incomplete proof evidence;
- preserving proof artifacts, logs, hashes, and optional external verification references.

## Design Position

The extension should target a component-chain interface rather than a monolithic autonomous proving agent. This fits MHE better because each stage can be declared, tested, swapped, and governed independently.

The initial chain is:

```text
Lean gateway
  -> Lean environment probe
    -> Lean blueprint compiler
      -> Lean proof workspace
        -> Lean executor
          -> Lean validator
            -> Lean evidence / policy adapter
```

Higher-risk layers are explicitly deferred:

- autonomous theorem proving claims;
- real external LLM orchestration inside the extension baseline;
- online theorem retrieval as a default path;
- automatic mutation of human mathematical statements without explicit policy approval;
- claiming Mathlib-quality proof style from compiler success alone.

## Current Reality / Constraints

MHE extension conventions require package-local contracts, capabilities, slots, component modules, JSON manifests, and manifest parity tests.

Lean real execution requires a local Lean project. A target `.lean` file outside a Lake project is not enough for robust checking. The environment probe must therefore classify project state before the executor runs.

The baseline should support three execution modes:

| Mode | Meaning | Evidence boundary |
|---|---|---|
| `mocked` | subprocess behavior is simulated for tests | proves MHE wiring only |
| `dry_run` | command/workspace plan is rendered but not executed | proves command assembly only |
| `real_check` | gated `lake env lean` or equivalent check executes | proves local Lean check for that environment |

`real_check` must remain opt-in and environment-gated. It should not run in default CI unless explicitly marked and enabled.

## Supported Family Design

### Family: `formal_proof`

A single theorem, lemma, or `sorry` target inside a Lean file.

Typical baseline:

- target declaration name;
- target file path;
- optional statement-preservation policy;
- optional informal proof outline;
- attempt budget;
- validation requirement: no Lean errors, optionally no `sorry`.

### Family: `formalization_project`

A blueprint-guided set of definitions, lemmas, and theorems with explicit dependencies.

Typical baseline:

- project root;
- blueprint items ordered by dependency;
- per-item Lean declaration target;
- dependency graph;
- per-item status: `todo`, `partial`, `done`, `blocked`;
- evidence linking each completed item to validation output.

### Family: `proof_audit`

A validation-only or review-oriented task for existing Lean code.

Typical baseline:

- check files or directories;
- classify errors, warnings, `sorry`, statement drift, and proof-artifact gaps;
- emit a validation report without attempting to solve proofs.

### Not Yet Supported Families

- online theorem retrieval as a managed service;
- interactive human-in-the-loop editor sessions;
- theorem-prover benchmark leaderboards;
- external prover ensembles;
- automated proof golfing beyond local style/evidence checks.

## Component Chain

### Gateway

Accepts user or upstream MHE tasks and normalizes them into `LeanTaskSpec` objects. It should reject ambiguous targets that cannot be associated with a project or task family.

### Environment Probe

Discovers Lean/Lake project facts:

- project root;
- Lean toolchain string;
- Lake file type;
- candidate target files;
- whether real execution prerequisites are present;
- opt-in environment variables for real execution.

It should produce skip findings rather than failing destructively when Lean is unavailable.

### Blueprint Compiler

Compiles proof-blueprint input into a `LeanRunPlan`.

It should model:

- proof items;
- dependency edges;
- target declarations;
- allowed mutation policy;
- attempt budgets;
- validation gates;
- workspace and artifact roots.

### Proof Workspace

Prepares a bounded workspace for proof attempts. For later slices, this may include temporary extracted files, baseline snapshots, and statement tracking. The baseline may model this as data only.

### Executor

Runs mocked, dry-run, or opt-in real Lean commands. It should preserve command manifests and raw outputs as artifacts.

The default test executor should use patched subprocesses or fake outputs. Real execution should require explicit opt-in such as `MHE_RUN_REAL_LEAN=1`.

### Validator

Interprets artifacts into `LeanValidationReport`:

- command return code;
- Lean errors;
- warnings;
- `sorry` occurrences;
- changed or removed statements;
- missing files;
- timeout or environment skip state;
- whether the task is compiler-valid and whether it is scientifically or formally complete.

### Evidence / Policy Adapter

Builds `LeanEvidenceBundle` and maps validation results into MHE governance terms. Compiler success is formal-check evidence for a concrete environment; it is not a claim of proof elegance, mathematical novelty, or benchmark superiority.

## Contracts Surface

The extension should define these Pydantic models:

- `LeanProjectSpec` for project roots and toolchain expectations;
- `LeanBlueprintItem` for dependency-aware proof targets;
- `LeanTaskSpec` for task family, target, policy, and mode;
- `LeanRunPlan` for executable or dry-run plans;
- `LeanRunArtifact` for command, stdout/stderr, output paths, hashes, and mode;
- `LeanValidationReport` for compiler, `sorry`, statement, and evidence status;
- `LeanEvidenceBundle` for provenance, validation refs, artifact refs, and policy status.

Important naming constraints:

- family names should be stable string literals;
- execution modes should preserve Lean-native fields while mapping to MHE execution boundaries;
- validation reports should distinguish `compiled`, `complete_without_sorry`, and `accepted_by_policy`.

## Runtime Semantics

The canonical lifecycle is:

```text
intake task
  -> probe project
    -> compile plan
      -> prepare workspace
        -> execute or dry-run
          -> validate artifacts
            -> emit evidence and policy result
```

Environment-first ordering is mandatory. The executor should not guess a Lean project root or run from a standalone file if no Lake project is found.

Short-circuit decisions:

- missing target file;
- no Lean project root;
- real execution requested without opt-in;
- unsafe mutation policy;
- invalid blueprint dependencies.

Non-short-circuit decisions:

- `sorry` warnings when the task explicitly allows partial proofs;
- non-fatal style warnings;
- mocked or dry-run execution when the support statement is clearly bounded.

## Governance & Validation

Validation states should include:

| State | Meaning |
|---|---|
| `environment_skipped` | prerequisites absent or opt-in not enabled |
| `planned` | command/workspace plan rendered only |
| `executed` | command was run in mocked or real mode |
| `compiled_with_sorry` | Lean accepted the file but incomplete proof markers remain |
| `compiled_complete` | Lean accepted the target with no disallowed `sorry` |
| `failed` | command failed, diagnostics contain errors, or policy rejected |

Evidence should preserve real identifiers:

- plan ID;
- run ID;
- task ID;
- artifact IDs;
- validation report ID;
- source file hashes when available.

No derived evidence ID should replace the underlying run or validation identity.

## Packaging & Registration

Recommended package files:

```text
src/metaharness_ext/lean/
├── __init__.py
├── capabilities.py
├── slots.py
├── contracts.py
├── gateway.py
├── environment.py
├── blueprint_compiler.py
├── workspace.py
├── executor.py
├── validator.py
├── evidence.py
├── manifest.json
├── gateway.json
├── environment.json
├── blueprint_compiler.json
├── workspace.json
├── executor.json
├── validator.json
└── evidence.json
```

Tests should assert parity between component `declare_interface()` snapshots and JSON manifests.

Recommended protected slots:

- Lean validator;
- Lean evidence/policy adapter;
- any future real-execution launcher.

## Tests & Evidence Expectations

Baseline tests should cover:

- import and package exports;
- contract serialization and validation;
- slot and capability constants;
- manifest parity for all baseline components;
- mocked environment discovery;
- mocked executor success, failure, timeout, and skipped states;
- validator classification for errors, warnings, and `sorry`;
- evidence bundle identity preservation.

Opt-in real tests should be marked separately and require both a local Lean project fixture and explicit environment opt-in.

## Explicit Out of Scope

The baseline does not implement:

- full autonomous proof search;
- external LLM calls;
- online Lean theorem search;
- proof golfing agents;
- distributed subagent orchestration;
- automatic modification of mathematical statements;
- claims that compiler-accepted generated proofs are idiomatic Mathlib contributions.

## Open Questions / Risks

- Whether real Lean fixtures should live inside MHE tests or under an external fixture path.
- Whether `sorry` should be allowed per family or per target item.
- How much statement tracking belongs in baseline versus a later safety slice.
- Whether future theorem retrieval should be an MHE component, an MCP adapter, or an external evidence reference.
- How to review proof readability without conflating style with formal correctness.
