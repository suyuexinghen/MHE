# Workflow Modes

Use this file to choose the right workflow before reading heavier MHE core upgrade references.

## Target-Tree Guard

Before doing substantive MHE core work, confirm the real target tree and avoid stale coordination state:

- core source: `MHE/src/metaharness/`
- focused tests: `MHE/tests/`
- current implementation manual: `MHE/docs/TECHNICAL_MANUAL.md`
- relevant design docs: `MHE/docs/wiki/`, `MHE/docs/plan-drafts/`, `MHE/docs/blueprint/`

If the active Claude CWD is not the real MHE tree, stop and locate the correct tree before editing. If worktree, teammate, or task state conflicts with current files, trust verified code/tests/docs over chat or coordination state.

## Source-Truth Triage

Core upgrade docs, wiki pages, plan drafts, and implementation may describe different maturity levels. Before designing or changing core behavior:

1. Read current source and focused tests for the subsystem.
2. Read `MHE/docs/TECHNICAL_MANUAL.md` for implementation-aligned behavior.
3. Compare current code truth with wiki/plan/roadmap claims.
4. Anchor claims to current implementation truth.
5. Explicitly label gaps as proposed, partially implemented, future work, or non-claims.

Do not let aspirational architecture docs override source/test truth.

## Resume After Team Or Task State Loss

When team state, task state, or agent history is cleared or stale:

1. Do not assume implementation work was lost.
2. Verify the current main worktree first:
   - grep/read expected code anchors;
   - run focused tests when relevant;
   - inspect docs or generated artifacts that represent the claimed state.
3. Reconstruct only missing coordination state if needed.
4. Report code truth separately from orchestration truth.

Treat team/task state as coordination metadata, not implementation truth.

## Mode A: Framework Upgrade Design

Use when the user asks to evolve core architecture, governance, runtime semantics, provenance, metrics, or research-loop capability.

Start here:

1. Name the repeated framework gap or audit question.
2. Identify the current authoritative layer: graph snapshot, runtime event, execution evidence, provenance/audit, metrics, benchmark artifact, or research record.
3. Separate example from invariant: which prior upgrade is only a case study, and what reusable rule belongs in core?
4. Prefer a companion abstraction: ledger, gateway, index, event, policy gate, report field, lifecycle model, or dashboard.
5. Define the smallest evidence-producing slice before broad refactor.
6. State claim boundaries and non-claims before implementation.

Do not begin by rewriting core primitives such as `GraphSnapshot`, `ComponentRegistry`, or `AuditLog` unless the companion-layer option has been ruled out.

## Mode B: Continuation / Resume

Use when the task starts from an existing blueprint, roadmap, handoff, plan draft, or partially landed core upgrade.

Start here:

1. Read the relevant blueprint, roadmap, handoff, or plan draft.
2. Read the current source and tests for the same subsystem.
3. Identify accepted, implemented, partial, proposed, and stale items.
4. Move accepted baseline items out of acceptance debt in docs when updating docs.
5. Keep backlog and future work separate from implemented framework capability.
6. Resume from the smallest unfinished slice that creates auditable evidence.

Do not restart from first principles unless existing docs are missing or untrustworthy.

## Mode C: Implementation Slice

Use when a specific core model, service, persistence path, CLI/report field, policy gate, or test slice should be added.

Minimum truthful slice:

- one clearly named invariant;
- additive model/service/gateway/index/gate where possible;
- persisted or reconstructable artifact/event/metric;
- focused tests for positive and boundary behavior;
- docs update with implemented/proposed/non-claim boundaries;
- extension regression checks if SDK/runtime contracts change.

Prefer record-first implementation before warnings, gates, or automation. A safe progression is:

```text
record -> expose -> warn -> gate -> automate promotion/retirement
```

## Mode D: Governance-Validation Slice

Use before promoting a new core abstraction into an enforced gate, automated decision, or manager-facing framework claim.

Validation flow:

1. Run the new abstraction in non-blocking record/report mode.
2. Verify persisted events, artifacts, metrics, reports, or conclusion fields exist.
3. Check that skips, rejects, unsupported states, and invalid candidates are visible.
4. Confirm claim boundaries are encoded in artifacts or gates, not only prose.
5. Use reviewer/verifier acceptance before enabling enforcement.

This is the core analogue of extension usage-validation: prove the workflow is observable and truthful before turning it into a stronger gate.

## Mode E: Verification / Audit Only

Use when the user asks to verify progress, validate recent changes, audit docs, or recommend next steps without asking for implementation.

Default behavior:

- Do not enter plan mode by default.
- Do not create a large team by default.
- Use one auditor/explorer or no agent unless the audit spans many subsystems.
- Report findings directly unless the user asks for implementation tasks.

Audit flow:

1. Check source/test truth for the claimed subsystem.
2. Check docs/roadmap/handoff truthfulness.
3. Check evidence persistence and report visibility.
4. Check claim-boundary language.
5. Report passed, concerns/drift, recommendation, and next smallest slice.

## Mode F: Pattern Extraction

Use when prior core upgrade experience should become reusable rules, skill content, blueprints, or roadmap guidance.

Extraction flow:

1. Collect two or more examples or one high-value repeated friction point.
2. Identify the invariant that generalizes beyond the example.
3. Name where that invariant belongs in core governance.
4. Specify evidence required before the invariant can support stronger claims.
5. Save the rule in skill/reference form if it will help future sessions.

Do not encode a past project decision as a universal rule unless it generalizes across MHE core, extensions, benchmarks, or research loops.
