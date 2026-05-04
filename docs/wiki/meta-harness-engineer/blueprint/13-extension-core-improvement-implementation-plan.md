# Extension Core-Improvement Implementation Plan

> Status: proposed
> Scope: staged implementation plan for upgrading existing MHE extensions to use core assembly, instantiation, selection, and metrics capabilities.
> Acceptance: each slice must be testable without requiring real solver binaries by default.

## Implementation Objective

Implement a cross-extension improvement program that lets MHE extensions produce truthful assembly and instantiation evidence while preserving existing extension behavior. The plan prioritizes shared patterns, small adapters, and report-visible evidence over large rewrites.

The implementation should proceed extension-by-extension, but the shape of each slice should stay consistent:

- audit manifests and capability dependencies;
- map native execution modes into core `ExecutionMode`;
- emit or preserve `InstantiationRecord` data;
- collect external evidence refs when real execution occurs;
- attach assembly metrics JSON/Markdown sidecars to benchmark or research outputs;
- record selection lifecycle states only when there is reviewable evidence.

## In-Scope Extension Families

The first rollout covers current documented extension families:

- `metaharness_ext.ai4pde`
- `metaharness_ext.nektar`
- `metaharness_ext.jedi`
- `metaharness_ext.deepmd`
- `metaharness_ext.qcompute`
- `metaharness_ext.abacus`
- `metaharness_ext.octave`
- `metaharness_ext.fealpy`
- `metaharness_ext.pycfd`
- `metaharness_ext.boutpp`
- `metaharness_ext.moose`

If an extension has only blueprint or partial implementation status, its slice should stop at manifest/evidence design and mocked tests until real source-tree behavior supports stronger claims.

## Shared Files and Surfaces

Production changes should prefer existing extension files:

```text
src/metaharness_ext/<extension>/contracts.py
src/metaharness_ext/<extension>/executor.py
src/metaharness_ext/<extension>/validator.py
src/metaharness_ext/<extension>/evidence.py
src/metaharness_ext/<extension>/governance.py
src/metaharness_ext/<extension>/benchmark_runner.py
examples/manifests/<extension>/*.json
```

Core additions should be avoided unless a repeated invariant is missing from the already-upgraded core. The expected core surfaces already exist:

```text
src/metaharness/core/assembly.py
src/metaharness/core/execution_modes.py
src/metaharness/core/selection.py
src/metaharness/observability/metrics.py
src/metaharness/cli.py
```

## Shared Test Surfaces

Each extension slice should add or update focused tests near the existing extension tests:

```text
tests/test_metaharness_<extension>_manifest.py
tests/test_metaharness_<extension>_executor.py
tests/test_metaharness_<extension>_validator*.py
tests/test_metaharness_<extension>_governance*.py
tests/test_metaharness_<extension>_benchmark*.py
```

At minimum, tests should cover:

- native mode to core mode mapping;
- instantiated versus externally verified counting;
- missing evidence staying unknown or partial;
- real-tool execution paths being mocked or opt-in;
- metrics sidecar generation when benchmark/research runners exist.

## Slice: Manifest Dependency Audit

Goal: make extension assembly paths visible to `DependencyGraphSnapshot` and `AssemblyHealthSummary`.

Implementation steps:

- Identify gateway, compiler, environment, executor, postprocess, validator, policy, evidence, study, and governance components.
- Add component dependencies where one component consumes another component's output.
- Add capability dependencies where a component requires a semantic ability rather than a named implementation.
- Mark external execution, validation, policy, and receipt adapters as critical dependencies where appropriate.
- Keep boot compatibility unchanged.

Acceptance:

- focused manifest tests still pass;
- boot order remains deterministic;
- assembly metrics reports include dependency graph snapshots;
- missing legacy dependencies are documented as backlog rather than silently inferred.

## Slice: Execution Mode Mapping

Goal: preserve extension-native modes while making cross-extension execution honesty comparable.

Implementation steps:

- Add a small mapping helper in each extension's evidence or governance layer.
- Map native mode strings or enums into `ExecutionMode`.
- Preserve native mode in `native_execution_mode`.
- Default unmapped legacy modes to `ExecutionMode.UNKNOWN`.
- Add tests for every native mode and unknown fallback.

Acceptance:

- existing extension APIs still accept current native modes;
- dry-run/config/schema paths do not become instantiated;
- simulation/mock paths do not become externally verified;
- real execution paths require concrete run artifacts before becoming instantiated.

## Slice: InstantiationRecord Handoff

Goal: reconcile extension claims, actions, run artifacts, validation refs, and external evidence through a core boundary object.

Implementation steps:

- Create `InstantiationRecord` in executor, validator, evidence, or governance adapter handoff code.
- Populate `execution_mode`, `native_execution_mode`, `run_artifact_ref`, `validation_ref`, `evidence_refs`, `external_evidence_refs`, `candidate_id`, and `graph_version` when available.
- Keep records partial when some refs are unavailable.
- Attach records to benchmark/research summaries or pass them into `AssemblyMetricsService` through CLI/report paths.

Acceptance:

- records serialize as JSON;
- records with external refs but non-external mode are not counted as externally verified;
- records with external mode but no external refs are not counted as externally verified;
- unknown records remain visible in metrics.

## Slice: External Receipt Standardization

Goal: make real solver/backend/hardware runs inspectable instead of prose-only.

Implementation steps:

- Add receipt fields to extension artifact or evidence models where absent.
- Include binary/backend version, command manifest, stdout/stderr/log snapshot, output hash, environment probe, and benchmark summary refs.
- Avoid storing large raw outputs in summary models when a file path or artifact hash is enough.
- Keep real execution opt-in when local solver dependencies are unavailable in CI.

Acceptance:

- mocked tests verify receipt extraction and missing-receipt classification;
- real smoke tests skip cleanly without local dependencies;
- docs avoid claiming external verification without receipt refs.

## Slice: Metrics Sidecar Integration

Goal: let benchmark and research outputs preserve core evidence metrics alongside extension-specific metrics.

Implementation steps:

- Add optional metrics sidecar generation to benchmark or research runner outputs.
- Use `AssemblyMetricsService` rather than extension-local metric schemas for core evidence boundaries.
- Write JSON and Markdown sidecars under `.runs/`.
- Include non-claims in Markdown reports.

Acceptance:

- sidecar paths are retained in run summaries;
- JSON report includes source graph/manifests when available;
- Markdown report includes non-claims;
- unknown evidence is not counted as externally verified.

## Slice: Selection Lifecycle Adoption

Goal: make promotion, suspension, deprecation, and graveyard decisions auditable.

Implementation steps:

- Record `SelectionLifecycle` states only after focused test, benchmark, review, or negative-result evidence exists.
- Use `promoted` for recommended component profiles.
- Use `suspended` for temporarily blocked but potentially valuable profiles.
- Use `deprecated` for replaced profiles that remain available.
- Use `graveyard` for misleading or high-risk routes with explicit mismatch evidence.

Acceptance:

- lifecycle records include reason and evidence refs;
- benchmark/report summaries can show selection state counts;
- no component is automatically retired from unknown evidence alone.

## Slice: Opt-In Enforcement Pilot

Goal: test stricter assembly health policy only after record/report slices are stable.

Implementation steps:

- Keep default `warn_only` for all extension boot and benchmark flows.
- Choose one mature extension lane with stable receipts for `defer_high_risk` pilot.
- Configure `reject_critical` only for explicit critical mismatch evidence.
- Preserve reviewer-visible reasons and evidence refs.

Acceptance:

- default behavior remains backward compatible;
- high-risk evidence produces defer only in configured lanes;
- reject requires critical mismatch evidence;
- unknown evidence never triggers automatic reject.

## Extension-Specific First Slices

| Extension | First implementation slice | Tests to prioritize |
|---|---|---|
| AI4PDE | emit InstantiationRecord from evidence manager and research-loop handoff | research evidence serialization and unknown/external counting |
| Nektar | map render/run/postprocess modes and attach solver log refs | session render dry-run and mocked real binary receipt tests |
| JEDI | map `schema`, `validate_only`, and `real_run` to core modes | native mode mapping and structured diagnostics receipt tests |
| DeepMD / DP-GEN | classify workspace/config stages as staged and training evidence separately | staged workflow records and checkpoint/log refs |
| QCompute | separate simulator/mock backend from provider receipt paths | simulator not external verified; provider receipt required |
| ABACUS | attach launcher, binary, SCF log, and output hash refs | input generation dry-run and real-run receipt classification |
| Octave | emit real `octave-cli` execution record for native smoke lanes | script generation versus CLI execution tests |
| FEALPy | attach backend labels and benchmark summary refs | numpy/reference versus library-backed mode records |
| PyCFD | audit compiler/runner/validator manifests and environment skip evidence | dependency graph and skip artifact tests |
| BOUT++ | create BOUT++ run artifact instantiation records and metrics sidecars | binary probe, log refs, and warn-only metrics report tests |
| MOOSE | separate input deck generation from executable run evidence | input dry-run, launcher skip, and output receipt tests |

## Documentation Updates

Each extension should update its wiki or blueprint with a short section named “Assembly / Instantiation Evidence Boundary”. The section should state:

- native execution modes and core mode mapping;
- what counts as external evidence refs;
- which claims remain non-goals;
- which metrics sidecars are expected;
- which selection lifecycle states are currently supported or planned.

## Verification Commands

Run focused checks for each touched extension first:

```bash
PYTHONPATH=src python -m pytest tests/test_metaharness_<extension>_*.py -q
ruff check src/metaharness_ext/<extension> tests/test_metaharness_<extension>_*.py
ruff format --check src/metaharness_ext/<extension> tests/test_metaharness_<extension>_*.py
```

Run cross-core checks after shared patterns are touched:

```bash
PYTHONPATH=src python -m pytest tests/test_observability.py tests/test_assembly.py tests/test_boot.py -q
ruff check src/metaharness src/metaharness_ext tests
ruff format --check src/metaharness src/metaharness_ext tests
```

If existing unrelated formatting drift exists, report it separately and do not fix it as part of a narrow extension evidence slice.

## Out-of-Scope

This plan does not include:

- rewriting all extension contracts at once;
- moving solver-specific metrics into core semantics;
- adding real solver binaries to default CI;
- claiming domain correctness from assembly metrics;
- enabling default hard policy rejection across extensions;
- replacing extension-specific benchmark reports.

## Completion Criteria

The improvement program is complete when every in-scope extension has:

- manifest dependencies aligned with actual pipeline structure;
- native execution mode mapping into core `ExecutionMode`;
- at least one tested `InstantiationRecord` path;
- external evidence refs for any externally verified claim;
- metrics sidecar support in benchmark or research outputs where applicable;
- documented selection lifecycle policy or backlog;
- updated wiki/blueprint claim boundaries;
- focused tests and independent review for docs truthfulness.
