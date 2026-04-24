# Design Document Templates

Use these templates when creating or repairing the formal planning docs for an extension.

All docs below should stay truthful to landed code and tests.

## 1. Extension Blueprint Template

Canonical filename:
- `MHE/docs/wiki/meta-harness-engineer/blueprint/NN-<name>-extension-blueprint.md`

What a good blueprint should do:
- state the formal design position for the extension
- define boundaries and invariants that should remain stable across slices
- explain runtime semantics and contract shapes clearly enough that later implementation plans can reference them instead of restating them
- distinguish design truth from roadmap sequencing and from current implementation status

Suggested structure:

```markdown
# <Name> Extension Blueprint

> Status: proposed | Formal implementation blueprint for `MHE/src/metaharness_ext/<name>`

## Technical Alignment Notes
- list factual corrections or non-obvious constraints learned from current docs / code / tests
- explicitly call out terms that must not be simplified incorrectly
- distinguish observed environment facts from assumptions

## 1. Goal
- extension purpose
- target software boundary
- why MHE should integrate at this layer
- current design stance in one sentence

## 2. Platform vs Domain Boundary
- what MHE core remains responsible for
- what the extension itself owns
- protected boundary / governance boundary if relevant

## 3. Design Position
- which interface level the extension targets
- why this level is preferred
- what higher-risk layers are explicitly deferred

## 4. Current Reality / Constraints
- current workspace or runtime reality
- build/install/runtime caveats
- observed executable/data/environment facts
- constraints that should shape the first implementation slices

## 5. Supported Family Design
- supported families
- per-family boundary
- baseline examples
- family vs baseline distinction
- not-yet-supported families
- family extension rule

## 6. Component Chain
- gateway / environment / compiler / preprocessor / executor / validator / evidence / policy chain
- per-component responsibilities
- handoff surface between adjacent components

## 7. Contracts Surface
- typed input/task contracts
- manifest / capability / slot surface
- run-plan contract
- run-artifact contract
- validation report / evidence / policy report surface

## 8. Runtime Semantics
- execution modes
- canonical lifecycle
- environment-first vs execute-first ordering
- short-circuit vs non-short-circuit decisions
- failure taxonomy

## 9. Governance & Validation
- environment findings model
- evidence / provenance semantics
- policy gates
- governance issue mapping
- what counts as execution success vs scientific success

## 10. Packaging & Registration
- package layout
- exports
- capabilities
- slots / protected slots
- manifest-registry proof or plugin-path discovery proof

## 11. Tests & Evidence Expectations
- focused unit / regression expectations
- minimal demo or E2E expectations
- evidence anchors proving support
- which family has the first formal baseline

## 12. Explicit Out of Scope
- deferred features
- unsupported workflows
- risky areas intentionally excluded

## 13. Open Questions / Risks
- unresolved design choices
- dependency risk
- truthfulness risk if docs overclaim
```

Blueprint rules:
- prefer design invariants over phase checklists
- if the extension already has landed code, describe the current design truth instead of pretending the document is greenfield
- keep implementation sequencing in roadmap / implementation plan, not in the blueprint body
- use a `Technical Alignment Notes` section when current docs need explicit correction
- explicitly distinguish family, baseline, execution mode, artifact, and evidence terms when confusion is likely

## 2. Roadmap Template

Canonical filename:
- `MHE/docs/wiki/meta-harness-engineer/blueprint/NN-<name>-roadmap.md`

What a good roadmap should do:
- reflect current landed truth first
- separate completed work from remaining slices
- show phase ordering without inflating scope
- record evidence for why a slice is considered done

Suggested structure:

```markdown
# <Name> Extension Roadmap

> Status: updated | Formal execution roadmap for `metaharness_ext.<name>`

## Technical Alignment Notes
- record important corrections the roadmap assumes
- separate observed environment facts from assumptions
- list naming or runtime facts that phase planning must honor

## 1. Current State Snapshot
- landed code truth
- landed tests truth
- docs truth status
- orchestration truth if relevant
- main current remaining gaps

## 2. Recommended Execution Order
```text
Phase 0 -> Phase 1 -> Phase 2
```
- explain why this order is chosen
- explain what must be proven before moving deeper

## 3. Completed Items
- only landed work
- include evidence anchor or test anchor where useful
- note if a phase is largely done but still has doc-sync leftovers

## 4. Remaining Slices
- smallest next slices only
- one deliverable family per slice when possible
- note docs-only sync slices explicitly

## 5. Phase Map
### Phase 0: <name>
- status
- goal
- key tasks
- acceptance criteria
- evidence

### Phase 1: <name>
- status
- goal
- key tasks
- acceptance criteria
- evidence

## 6. Risks / Dependencies
- external software dependency
- runtime dependency
- test environment dependency
- doc truthfulness dependency
```

Roadmap rules:
- do not leave landed work under "remaining"
- if code/tests landed but docs are stale, create a docs-only sync slice
- status should reflect main worktree truth, not stale team/task state
- if phases contain mixed status, say which parts are landed and which remain
- keep phase bullets small enough that an implementation plan can target one slice cleanly

## 3. Fallback Strategy Template

This can live inside the implementation plan or as a dedicated section/doc when the extension is risky.

Suggested structure:

```markdown
## Fallback Strategy

### Preferred Path
- smallest intended slice
- exact seam to modify
- expected verification

### Safe Fallback
- reduced-scope slice if preferred path proves too broad
- what is deferred
- what design truth remains valid after fallback

### Rollback Point
- which files / seams can be reverted cleanly
- which docs must be reverted or resynced
- whether support status must be downgraded from tested to partial

### Truthfulness Rule
- if fallback lands partial support, docs and matrix must say partial, not complete
- if only docs are synced, say docs-only rather than implying runtime change
```

Fallback rules:
- fallback should reduce scope, not silently change the design claim
- always note what user-visible support statement must change if fallback lands

## 4. Implementation Plan Template

Canonical filename:
- `MHE/docs/wiki/meta-harness-engineer/blueprint/NN-<name>-implementation-plan.md`

What a good implementation plan should do:
- target one smallest-next-slice
- list the exact files or seams expected to change
- state what is intentionally excluded from this slice
- define focused verification and completion criteria

Suggested structure:

```markdown
# <Name> Implementation Plan

> Status: proposed | Executable implementation plan for one slice under `<roadmap anchor>`

## Technical Alignment Notes
- restate only the facts that materially constrain this slice
- include naming/runtime facts the implementation must not violate

## 1. Objective
- exact next slice
- why this slice is next
- what capability becomes newly true after this slice

## 2. Scope
### In scope
- files / seams / behaviors to change

### Out of scope
- nearby work explicitly not included
- future slices intentionally deferred

## 3. Current Baseline
- current code truth
- current test truth
- current doc truth
- relevant prior extension patterns to follow

## 4. Design Decisions For This Slice
- contract changes
- runtime changes
- validation / evidence changes
- docs changes
- naming / semantics constraints

## 5. Target Files
- production code files
- tests
- docs / roadmap / handoff / wiki files
- manifest or registration files if any

## 6. Planned Changes
### 6.1 Contracts
- exact typed model additions/changes

### 6.2 Runtime / Execution
- gateway/compiler/preprocessor/executor/validator/policy changes

### 6.3 Tests
- new tests
- modified assertions
- evidence anchors to add

### 6.4 Docs / Handoff Sync
- roadmap sections to update
- handoff updates
- wiki or support matrix updates if support status changes

## 7. Verification Plan
- focused pytest
- ruff scope
- minimal demo / E2E proof
- read/grep checks for docs truthfulness
- any manual review pass needed

## 8. Fallback Strategy
- reduced scope if needed
- what will be explicitly deferred
- truthfulness changes required if fallback lands

## 9. Completion Criteria
- code landed
- tests passing
- docs synced
- handoff updated
- support claims match evidence
```

Implementation-plan rules:
- prefer one smallest slice per plan
- separate production-code changes from docs-only changes
- call out when the slice is verification-only or docs-only
- do not let a plan become a second roadmap
- if the slice depends on existing landed semantics, reference them rather than re-specifying the whole extension

## 5. Handoff Report Template

Canonical filename:
- `MHE/docs/<NAME>_EXTENSION_HANDOFF_REPORT.md`

Suggested structure:

```markdown
# <NAME> Extension Handoff Report

## Current Truth
- code truth
- test truth
- docs truth
- orchestration truth

## Last Completed Slice
- what landed
- evidence anchor
- files or seams changed

## Next Smallest Slice
- exact next step
- why it is next
- whether it is code, test, verification, or docs-only

## Open Risks / Caveats
- not yet proven
- environment limitations
- discovery / registration caveats
- truthfulness caveats in docs/support matrix

## Docs To Sync
- roadmap sections
- wiki pages
- support matrix location
- local/global skill sync if this work changed workflow guidance
```

Handoff rules:
- distinguish code/test truth from orchestration truth
- if team/task state was lost, record that code may still be fully landed
- never use the handoff to imply implementation work was lost unless code/tests prove loss
- keep the next slice small enough that a follow-up implementation plan can target it directly
