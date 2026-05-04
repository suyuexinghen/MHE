# Extension Core-Improvement Roadmap

> Status: proposed
> Scope: staged roadmap for improving MHE extensions with upgraded core assembly, instantiation, selection, and metrics capabilities.

## Current Baseline

MHE core now has record/report surfaces for assembly history, dependency DAG snapshots, copy-count signals, instantiation boundaries, selection lifecycle, and assembly metrics reports. Existing extensions already contain many local contract, compiler, executor, validator, governance, and benchmark patterns, but they do not yet use the new core evidence framework consistently.

The roadmap therefore starts from a mixed maturity baseline:

- some extensions have mature runnable pipelines and benchmark evidence;
- some extensions have dry-run or staged workflow coverage;
- some extensions have real-tool paths that are opt-in and environment-gated;
- some extension docs predate the core assembly/instantiation framework;
- cross-extension reports cannot yet compare assembly health or execution honesty uniformly.

## Target State

The target state is a governed extension portfolio where each extension can answer:

- how its component graph is assembled;
- which components are reused, low-copy, or critical;
- whether a run is simulation, dry-run, staged, instantiated, externally verified, or unknown;
- which external receipts support real execution claims;
- which components are promoted, suspended, deprecated, or graveyarded;
- which metrics are framework evidence and which claims still require domain validation.

## Phase Map

| Phase | Status | Deliverable | Evidence unlocked |
|---|---|---|---|
| Portfolio audit | proposed | extension manifest/evidence gap matrix | known dependency and instantiation gaps |
| Manifest dependency pass | proposed | updated manifests and dependency tests | assembly index and low-copy critical dependency signals |
| Execution mode pass | proposed | native-to-core mode mappings | simulation/dry-run/staged/real execution separation |
| Instantiation record pass | proposed | serialized records from executor/validator/governance lanes | claim/action/evidence reconciliation |
| External receipt pass | proposed | standardized receipt refs for real-tool lanes | externally verified eligibility where evidence exists |
| Metrics sidecar pass | proposed | JSON/Markdown sidecars in benchmark/research outputs | cross-extension assembly and instantiation reporting |
| Selection lifecycle pass | proposed | promoted/suspended/deprecated/graveyard records | auditable component fate and negative-result memory |
| Enforcement pilot | later | opt-in `defer_high_risk` or `reject_critical` lanes | evidence-backed governance beyond warn-only |

## Priority Ladder

| Priority | Work | Why now | Exit signal |
|---|---|---|---|
| High | manifest dependency audit | metrics depend on truthful DAG inputs | dependency graph snapshots reflect real extension chains |
| High | execution mode mapping | prevents dry-run and simulation overclaims | native modes map to core modes with tests |
| High | InstantiationRecord handoff | creates shared evidence boundary | records serialize and appear in reports |
| High | receipt refs for real execution | enables external verified claims without prose | external verified count requires mode plus refs |
| Medium | metrics sidecars | makes benchmark conclusions comparable | `.runs/.../assembly-metrics.json` retained |
| Medium | selection lifecycle | turns review conclusions into evidence | selection counts appear in reports |
| Medium | docs/wiki updates | prevents roadmap and README overclaims | each extension states evidence boundary |
| Later | opt-in enforcement | should follow stable evidence collection | configured lanes defer/reject only with evidence |

## Extension Progression Matrix

| Extension | Current improvement posture | Next milestone | Stronger claim blocked by |
|---|---|---|---|
| AI4PDE | research-loop evidence rich, core mode mapping incomplete | InstantiationRecord from evidence manager | real solver receipts and repeated workflow metrics |
| Nektar | traditional solver pipeline, real execution boundary needs sharpening | session render dry-run plus solver log receipt mapping | stable real `nektar++` artifacts across selected cases |
| JEDI | native execution modes already useful | map `schema`/`validate_only`/`real_run` with diagnostics refs | structured diagnostics or external receipt completeness |
| DeepMD / DP-GEN | staged workflow model fits core boundary | staged records for workspace/config/train/sample phases | real training/checkpoint/validation closure |
| QCompute | simulator/real backend distinction is critical | provider receipt requirement for external verified | real backend or hardware receipt availability |
| ABACUS | file-driven execution and launcher evidence fit core model | input generation dry-run; launcher/binary refs for real runs | SCF/convergence logs and output hashes |
| Octave | lightweight regression baseline | real `octave-cli` InstantiationRecord sidecar | repeated native cases beyond a single smoke |
| FEALPy | benchmark/research handoff exists | backend-labeled metrics sidecar | backend-specific retained real execution evidence |
| PyCFD | early pipeline needs assembly maturity | manifest dependency audit and environment skip evidence | real solver environment and retained residual metrics |
| BOUT++ | new extension suitable for full evidence ladder | binary probe/log/artifact instantiation records | opt-in real BOUT++ smoke evidence |
| MOOSE | newer FEM integration should adopt boundary early | input deck versus executable run boundary | real executable/output receipt evidence |

## Shared Backlog

| ID | Area | Symptom | Suggested fix | Priority |
|---|---|---|---|---|
| EXT-DAG | Assembly evidence | manifests may not express real pipeline dependencies | audit component/capability/critical dependencies | High |
| EXT-MODE | Instantiation boundary | local modes are not comparable across extensions | add native-to-core `ExecutionMode` mapping helpers | High |
| EXT-RECORD | Evidence reconciliation | benchmark outputs may lack core `InstantiationRecord` | emit records from evidence/governance adapters | High |
| EXT-RECEIPT | External verification | prose claims can stand in for receipts | standardize binary/log/hash/provider refs | High |
| EXT-METRICS | Report visibility | benchmark summaries only show extension-local metrics | add assembly metrics sidecars under `.runs/` | Medium |
| EXT-SELECT | Selection pressure | promoted/suspended decisions live only in docs | record `SelectionLifecycle` states with evidence refs | Medium |
| EXT-DOCS | Claim boundaries | extension wikis predate core framework language | add evidence boundary sections to each wiki | Medium |
| EXT-GATE | Enforcement | stricter policy could overblock legacy evidence | pilot opt-in defer/reject only after reports stabilize | Later |

## Extension-Specific Backlog

| ID | Extension | Improvement | Evidence needed | Priority |
|---|---|---|---|---|
| AI4PDE-CORE | AI4PDE | connect problem formulator, method router, solver executor, validator, and evidence manager dependencies | dependency graph snapshot and research handoff record | High |
| AI4PDE-INST | AI4PDE | distinguish symbolic plans, template instantiation, solver execution, and validation | native/core mode mapping tests | High |
| NEKTAR-RECEIPT | Nektar | classify session rendering as dry-run and real binary execution as instantiated/external only with logs | solver version, stdout/stderr, mesh/session hash | High |
| JEDI-MODE | JEDI | preserve `JediExecutionMode` while mapping to core modes | schema/validate/real-run mode tests | High |
| JEDI-DIAG | JEDI | require diagnostics or receipt for external verified real-run claims | structured diagnostics refs | High |
| DEEPMD-STAGE | DeepMD / DP-GEN | model DP-GEN workspace/config/training as staged phases | staged record and checkpoint refs | Medium |
| QCOMPUTE-RECEIPT | QCompute | require provider/backend receipt for external verified | circuit hash, backend name, shot count, result hash | High |
| ABACUS-LAUNCH | ABACUS | separate input deck generation from launcher/binary execution | command manifest, SCF logs, output hash | High |
| OCTAVE-SIDECAR | Octave | attach assembly metrics to real `octave-cli` smoke outputs | generated script hash and summary JSON path | Medium |
| FEALPY-BACKEND | FEALPy | label backend execution mode and preserve solver metrics refs | backend availability and L2/H1 metrics | Medium |
| PYCFD-DAG | PyCFD | solidify compiler/runner/validator dependencies | manifest tests and assembly report | High |
| PYCFD-SKIP | PyCFD | make missing environment a first-class skip artifact | environment probe and skip summary refs | High |
| BOUTPP-INST | BOUT++ | emit records from BOUT++ binary probe, executor, and validator | run directory hash, logs, restart/output artifacts | High |
| MOOSE-INST | MOOSE | distinguish input deck generation from executable FEM run | executable path, command manifest, output refs | Medium |

## Metrics Maturity Ladder

| Tier | Name | Required evidence | Claim boundary |
|---|---|---|---|
| Tier 0 | Unknown legacy | no core mode or incomplete refs | visible as unknown, not failure or success |
| Tier 1 | Assembly-visible | dependency DAG and assembly health summary exist | graph maturity, not execution truth |
| Tier 2 | Mode-aware | native and core execution modes recorded | execution boundary is classified |
| Tier 3 | Record-linked | InstantiationRecord links run and validation refs | action/evidence reconciliation exists |
| Tier 4 | Receipt-backed | real run has external evidence refs | eligible for externally verified count |
| Tier 5 | Lifecycle-governed | selection states and metrics sidecars are retained | component fate is auditable |
| Tier 6 | Enforcement-ready | stable evidence supports opt-in defer/reject | governance can harden in configured lanes |

## Release Milestones

### Foundation Milestone

Exit criteria:

- extension gap matrix exists;
- shared mode mapping conventions are documented;
- at least two mature extensions have manifest dependency tests;
- `metaharness metrics assembly` reports are retained for sample graphs.

### Evidence Milestone

Exit criteria:

- at least five extensions emit tested `InstantiationRecord` objects;
- external verified counts require both core mode and external refs;
- unknown/partial records appear in metrics reports;
- benchmark/research outputs can link metrics sidecars.

### Portfolio Milestone

Exit criteria:

- all in-scope extensions have evidence-boundary wiki sections;
- extension-specific backlogs classify promoted, suspended, deprecated, and graveyard candidates;
- metrics sidecars are available for the main comparison suites;
- roadmap conclusions avoid scientific superiority claims.

### Enforcement Milestone

Exit criteria:

- at least one mature lane runs with `defer_high_risk` in a controlled opt-in path;
- `reject_critical` is used only for explicit critical mismatch evidence;
- default extension behavior remains warn-only and backward compatible;
- reviewer acceptance confirms no unsupported hard-gate claims.

## Review Checklist

Before marking an extension improvement slice complete, verify:

- manifest dependencies match actual runtime/evidence flow;
- native execution mode is preserved;
- core `ExecutionMode` mapping is tested;
- generated config/input paths are not mislabeled as instantiated;
- externally verified records include external evidence refs;
- unknown evidence remains visible and is not counted as external verification;
- metrics reports include non-claims;
- selection lifecycle states include reasons and evidence refs;
- docs distinguish implemented behavior from proposed roadmap work.

## Stop Conditions

Pause the roadmap and re-evaluate if:

- an extension requires a contract rewrite that would break existing tests;
- real solver evidence requires unavailable or non-reproducible infrastructure;
- a report would imply scientific validation from framework metrics alone;
- a policy change would reject legacy evidence by default;
- external receipts contain sensitive or machine-specific data that should not be retained.

## Final Exit Criteria

The extension portfolio improvement roadmap is complete when:

- every in-scope extension reaches at least Tier 2 mode-aware evidence;
- mature real-tool extensions reach Tier 4 receipt-backed evidence for at least one representative case;
- benchmark/research lanes preserve assembly metrics sidecars where applicable;
- selection lifecycle records document promoted and blocked profiles;
- all extension docs state evidence boundaries and non-claims;
- opt-in enforcement is piloted only after evidence reports are stable.
