# Phase Playbook

Use this file when the task requires the full MHE extension workflow rather than a small verification-only pass.

## Phase 0: Foundation Survey

Before designing, understand the landscape:

1. Read MHE framework docs:
   - `MHE/docs/wiki/meta-harness-engineer/meta-harness-wiki/README.md`
   - `MHE/src/metaharness/core/`
   - existing extensions under `MHE/src/metaharness_ext/`
2. Read target software docs:
   - official user guide / technical manual
   - API reference if available
   - build/install guides
3. Identify extension slot and numbering:
   - check `MHE/docs/wiki/meta-harness-engineer/blueprint/`
   - use one canonical numbering prefix consistently across extension docs
   - canonical names:
     - `blueprint/NN-<name>-extension-blueprint.md`
     - `blueprint/NN-<name>-roadmap.md`
     - `blueprint/NN-<name>-implementation-plan.md`
4. If multiple versions exist:
   - compare them
   - judge which is more reliable
   - merge into one numbered canonical set

## Phase 1: Explore & Design Wiki

1. Survey target software docs and existing MHE extensions for patterns.
2. Create wiki under `MHE/docs/wiki/meta-harness-engineer/<name>-engine-wiki/`.
3. Keep filenames aligned with `wiki-outline-template.md`.
4. Ensure README includes:
   - truthfulness disclaimer
   - scope boundaries vs. blueprint / roadmap / .trash
   - recommended reading order
   - explicit design-boundary framing
5. Call an auditor agent to review the design against:
   - official docs
   - existing extension wikis
   - MHE core interfaces

## Phase 2: Blueprint & Planning Docs

Create in `MHE/docs/wiki/meta-harness-engineer/blueprint/` using one canonical numbering prefix.

Required docs:
- `NN-<name>-extension-blueprint.md`
- `NN-<name>-roadmap.md`
- `NN-<name>-implementation-plan.md`
- `MHE/docs/<NAME>_EXTENSION_HANDOFF_REPORT.md`

Read `design-doc-templates.md` before writing these docs.

Rules:
- keep docs truthful to landed code
- do not list completed code/tests as remaining backlog
- update wiki references to the canonical numbered blueprint
- store the next concrete deliverable and next smallest slice in the handoff report
- make fallback scope explicit when a slice may need to degrade safely


## Phase 3: Per-Phase Implementation

Use the smallest-next-slice rule:
- one typed contract family
- one environment probe seam
- one validator surface
- one minimal executable baseline
- one regression/E2E coverage slice
- one payload alignment fix
- one handoff-truth sync pass
- one docs-only sync slice when code/tests are already landed but roadmap/handoff is stale

If a phase is too broad, split it into smaller slices before implementation.

For team execution, verification, merge, and handoff details, read `team-verification-handoff.md`.

## Phase 4: Cross-Extension Impact Analysis

When MHE core changes affect multiple extensions:
1. audit existing extensions in parallel
2. write impact analysis
3. apply updates in the smallest safe slices
4. add tests for new behavior

## Phase 5: Post-Implementation Review

After planned slices complete:
1. compare wiki design vs. actual code
2. check doc truthfulness
3. classify remaining gaps:
   - mandatory now
   - can defer
4. recommend the next smallest slice if meaningful work remains
