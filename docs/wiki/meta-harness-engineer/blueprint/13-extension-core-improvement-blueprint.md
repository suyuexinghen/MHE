# Extension Core-Improvement Blueprint

> Status: proposed
> Scope: cross-extension upgrade blueprint for adopting the upgraded MHE core assembly, instantiation, selection, and metrics framework.
> Primary references: `docs/plan-drafts/mhe-core-upgrade-analysis-assembly-instantiation.md` and `docs/wiki/meta-harness-engineer/meta-harness-wiki/11-upgraded-core-framework-and-extension-improvement.md`.

## Purpose

This blueprint defines how existing MHE extensions should evolve after the core assembly/instantiation upgrade. The goal is not to rewrite every extension or add more wrappers. The goal is to make each extension's dependencies, execution boundary, external evidence, component selection state, and benchmark/report sidecars auditable through the new core framework.

The upgraded core provides reusable governance services that extensions can now adopt:

- `AssemblyLedger` for candidate, committed, and dependency-graph assembly evidence.
- `CopyCountIndex` for registered, candidate, committed, dependency, invoked, and externally verified reuse signals.
- `DependencyGraphSnapshot` and `AssemblyHealthSummary` for assembly index, lineage, history folding, and low-copy critical dependency reporting.
- `ExecutionMode` and `InstantiationRecord` for separating simulation, dry-run, staged, instantiated, externally verified, and unknown evidence.
- `AssemblyHealthPolicy` for default warn-only reporting and opt-in defer/reject enforcement.
- `SelectionLifecycle` for promoted, suspended, deprecated, and graveyard component states.
- `AssemblyMetricsService` and `metaharness metrics assembly` for JSON/Markdown evidence reports.

## Claim Boundary

This blueprint is a design and rollout plan. It does not claim that all extensions already emit complete assembly metrics, externally verified instantiation records, or selection lifecycle evidence.

The following boundaries must stay explicit in every extension document and report:

- Metrics do not prove scientific validity.
- Simulation and dry-run evidence are not real-world instantiation.
- Generated input files, rendered configs, and validation-only workflows are not solver execution.
- Externally verified execution requires `execution_mode == external_verified` and non-empty external evidence refs.
- Human approval, benchmark pass/fail, and scientific/domain correctness are separate claims.
- Unknown or legacy evidence must remain `unknown` or `partial`, not inferred as success or failure.

## Upgrade Objective

Each extension should progress from a local, solver-specific wrapper into a governed MHE extension family with the following properties:

- manifest dependency edges express the real component chain rather than only boot convenience;
- native execution modes are preserved but mapped into core `ExecutionMode`;
- executor, validator, benchmark, or governance adapters can emit `InstantiationRecord` objects;
- real tool, backend, hardware, or solver runs produce inspectable external evidence refs;
- selection lifecycle records explain which components are promoted, suspended, deprecated, or graveyarded;
- benchmark and research outputs can attach assembly metrics sidecars;
- stricter assembly health policy remains opt-in and evidence-backed.

## Cross-Extension Architecture Pattern

The recommended extension chain is:

```text
extension gateway
  -> problem/config compiler
    -> environment/backend probe
      -> executor or staged runner
        -> postprocess/collector
          -> validator
            -> evidence/governance adapter
              -> core instantiation and assembly metrics sidecar
```

The exact component names differ by extension family, but the evidence flow should be consistent:

```text
manifest dependencies
  -> dependency DAG snapshot
    -> assembly health summary
      -> execution evidence
        -> instantiation record
          -> selection lifecycle decision
            -> metrics JSON/Markdown report
```

## Manifest Dependency Target

Every extension should audit its manifests for three dependency classes.

| Dependency class | Purpose | Example |
|---|---|---|
| Component dependency | Explains ordering and assembly path | validator depends on executor output |
| Capability dependency | Explains required semantic ability | postprocess requires solver output capability |
| Critical dependency | Marks safety or evidence-sensitive components | external receipt adapter or real backend launcher |

The manifest audit is complete for an extension only when `metaharness metrics assembly` can produce dependency graph snapshots whose assembly index and low-copy critical dependency counts reflect the actual extension pipeline.

## Instantiation Boundary Target

Each extension must map local execution vocabulary into the core execution boundary without deleting native fields.

| Core mode | Meaning | Extension examples |
|---|---|---|
| `simulation` | simulated or mock backend only | QCompute simulator, fake solver summary |
| `dry_run` | schema/config/input generation or validation-only path | JEDI `validate_only`, Nektar session render |
| `staged` | workspace or multi-stage workflow prepared but not fully executed | DP-GEN config/workspace generation |
| `instantiated` | real local tool/backend action occurred | real solver binary completed with artifacts |
| `external_verified` | real action plus external receipt/hash/log/backend proof | provider receipt, solver log, artifact hash |
| `unknown` | legacy or incomplete evidence | old benchmark artifact without mode metadata |

## External Evidence Ref Target

An external evidence ref should be a durable pointer to something a reviewer or tool can inspect. Good refs include:

- solver binary path and version snapshot;
- launcher command manifest;
- stdout/stderr/log snapshot;
- output directory or artifact hash;
- validation summary path;
- provider/backend receipt;
- environment probe result;
- benchmark run summary path.

Avoid using prose-only claims such as “ran successfully” as evidence. If the extension cannot provide a receipt, it should not mark the record as externally verified.

## Selection Lifecycle Target

Selection lifecycle should encode component fate after benchmark or review evidence accumulates.

| State | Use when | Required evidence |
|---|---|---|
| `promoted` | component profile is recommended for the next workflow tier | focused tests, metrics sidecar, clear claim boundary |
| `suspended` | component is temporarily blocked but evidence is worth preserving | failure report, environment gap, or incomplete receipt |
| `deprecated` | component remains available but is no longer recommended | replacement path and rationale |
| `graveyard` | component or route is high-risk, misleading, or scientifically invalid | explicit mismatch or negative-result evidence |

## Metrics Sidecar Target

Each benchmark or research run that evaluates an extension should be able to preserve an assembly metrics sidecar:

```text
.runs/<suite>/<run>/assembly-metrics.json
.runs/<suite>/<run>/assembly-metrics.md
```

The sidecar should include:

- source graph and manifest roots;
- dependency graph count and max assembly index;
- history folding ratio and low-copy critical dependency count;
- instantiation record counts by mode and reconciliation status;
- externally verified count, only when external refs exist;
- selection state counts;
- non-claims.

## Extension Family Targets

| Extension | Primary upgrade theme | First evidence target |
|---|---|---|
| AI4PDE | research-loop evidence reconciliation | hypothesis/solver/validator records linked through `InstantiationRecord` |
| Nektar | real solver evidence boundary | session render as dry-run; real binary logs as instantiated/external refs |
| JEDI | native execution mode mapping | `schema`/`validate_only`/`real_run` mapped to core modes |
| DeepMD / DP-GEN | staged workflow honesty | workspace/config stages separated from training/sampling evidence |
| QCompute | simulator versus real backend proof | mock/simulator as simulation; provider receipt for external verified |
| ABACUS | file-driven DFT execution boundary | input generation separated from launcher/binary output evidence |
| Octave | lightweight regression baseline | real `octave-cli` receipt separated from agent script generation |
| FEALPy | PDE benchmark sidecar integration | backend-labeled metrics and solver summary refs |
| PyCFD | early pipeline maturation | compiler/runner/validator dependencies and real-solver skip evidence |
| BOUT++ | late-stage maturity route | BOUT++ binary/log/artifact refs and warn-only health reports |
| MOOSE | FEM workflow instantiation boundary | input deck generation separated from executable run and output evidence |

## Non-Goals

This blueprint does not require:

- a one-shot rewrite of all extension contracts;
- removal of extension-local native mode vocabulary;
- default hard rejection from assembly health gates;
- real binary execution in default CI;
- scientific superiority claims from framework metrics;
- external dashboard infrastructure beyond JSON/Markdown reports.

## Acceptance Criteria

The blueprint is accepted when:

- each extension has a documented upgrade target and first evidence slice;
- the implementation plan defines staged, testable work without forcing a rewrite;
- the roadmap separates high-priority shared foundation work from extension-specific maturity work;
- all claim boundaries remain explicit;
- reviewer/verifier feedback confirms the docs do not imply unsupported real execution or scientific validation.
