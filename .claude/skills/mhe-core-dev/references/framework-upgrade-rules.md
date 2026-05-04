# Framework Upgrade Rules

Use this reference when turning MHE core upgrade experience into future implementation, roadmap, or verification guidance.

## Upgrade Smell

Consider a framework-level core upgrade only when at least one is true:

- the same governance need appears across multiple extensions, benchmark suites, or research workflows;
- current artifacts cannot answer an important audit question;
- runtime truth, evidence truth, and documentation truth have started to diverge;
- a repeated process needs promotion from manual convention to persisted core state;
- a stronger claim is blocked by missing framework evidence rather than missing domain logic.

Do not promote one solver's local needs into core unless the invariant is reusable beyond that solver.

## Pattern Extraction Flow

1. **Observe repeated friction**: name the recurring failure, ambiguity, or missing evidence.
2. **Separate instance from invariant**: identify what is universal across the examples.
3. **Locate current authority**: determine whether the truth belongs to graph state, runtime events, provenance, audit, safety, metrics, benchmark artifacts, or research records.
4. **Design the companion abstraction**: create a ledger, gateway, index, report field, policy gate, or lifecycle model that owns the new invariant.
5. **Define promotion evidence**: specify tests, artifacts, reports, and docs needed before stronger claims are allowed.
6. **Keep a non-claim list**: explicitly state what the new abstraction does not prove.
7. **Backfill roadmap/handoff**: update docs so future work continues from verified code truth, not chat context.

## Upgrade Ladder

Use this ladder for core changes:

```text
pattern recognized
  -> design boundary named
  -> smallest additive model/service
  -> focused tests
  -> persisted artifact/event/metric
  -> report/doc visibility
  -> verifier review
  -> roadmap promotion
```

Avoid jumping directly from concept to broad refactor.

## Evidence Lenses

### Runtime Governance Lens

Use this when an upgrade claims to move MHE beyond graph governance. Collect evidence for:

- current substrate: `GraphSnapshot`, candidate records, active graph, rollback target;
- runtime action: execution lifecycle, task state, side effect, external receipt, or instantiated artifact;
- gate: semantic validation, safety pipeline, policy veto, reviewer state, or post-commit health check;
- recovery: rollback, reject, defer, downgrade, dependency skip, or unsupported state;
- evidence trail: session events, execution evidence, audit record, PROV relation, metric, report field.

Do not call a change runtime governance if it only changes graph shape or docs wording.

### Scientific Research-Loop Lens

Use this when an upgrade claims to move MHE beyond case execution. Collect evidence for:

- research state: question, hypothesis, decision, experiment, comparison, or conclusion;
- evidence object: run artifact, benchmark bundle, report, dossier, negative result, or approval manifest;
- loop transition: proposal, execution, validation, repair, repeat aggregation, report, backlog, roadmap;
- boundary: dry-run vs real tools, proposal vs execution, approval vs scientific validation, domain metric separation;
- resumability: persisted artifacts and docs sufficient for a future agent to continue without chat memory.

Do not call a change research-loop governance if it only runs one case and writes a one-off summary.

## Common Companion Abstractions

| Missing invariant | Prefer this companion layer | Avoid first |
|---|---|---|
| runtime side-effect truth | instantiation gateway / execution-mode event | treating graph commit as proof of action |
| complex capability lineage | assembly ledger | stuffing provenance-only fields into every model |
| repeated use / reliability proxy | copy-count or reuse index | a single ambiguous `count` field |
| simulated vs real effects | instantiation gateway / execution mode | treating commit or success as real-world proof |
| research loop continuity | research session/evidence loop records | one-off report text only |
| promotion eligibility | safety/policy gate with explicit blockers | roadmap status labels only |
| cross-suite claim consistency | central conclusion/report artifact | chat-only summaries |
| metric comparability | domain-specific metric boundary records | one global score |

## Evidence Rules

- New framework state must be persisted or reconstructable from persisted artifacts.
- Reports may summarize evidence but should not be the only source of truth.
- Tests should assert both positive behavior and boundary behavior.
- Skips, rejects, unsupported states, and invalid candidates are first-class evidence.
- Dry-run proves workflow wiring; real tools prove selected execution; repeated runs support stability; scientific signoff supports scientific claims.

## Review Checklist

Before approving a core framework upgrade, check:

- Does this solve a repeated framework invariant, not a local convenience?
- Is the new abstraction owned by the correct layer?
- Does it preserve existing graph/runtime/provenance authority boundaries?
- Is the smallest implementation slice additive and reversible?
- Are existing extensions protected by focused regression tests?
- Are claim boundaries encoded in artifacts, gates, or tests, not only prose?
- Can future agents resume from docs and code without needing chat memory?

## Prior Upgrade Examples

Use these only as examples of abstraction discovery:

- Graph governance to runtime governance: the reusable lesson is that validity of structure is not enough; runtime side effects, safety, evidence, and rollback need their own governance surface.
- Case computation to scientific research loop: the reusable lesson is that a solver run is not the full scientific workflow; hypotheses, evidence, comparison, repair, reports, and backlog need durable loop state.
- Assembly/instantiation analysis: the reusable lesson is that complex framework capabilities require lineage, reuse, selection pressure, and explicit execution boundaries before reliability claims are safe.
