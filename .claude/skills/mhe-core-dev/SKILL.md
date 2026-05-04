---
name: mhe-core-dev
description: Guide framework-level upgrades to MHE core (`src/metaharness/`). Use when evolving MHE core architecture, governance layers, runtime semantics, research-loop infrastructure, graph/runtime promotion logic, provenance/audit/metrics, or framework-wide abstractions. Triggers: "upgrade MHE core", "MHE core architecture", "framework upgrade", "runtime governance", "research loop", "assembly ledger", "instantiation boundary", "core roadmap", "core blueprint", "Meta-Harness framework evolution".
---

# MHE Core Development

Use this skill as a lightweight router for framework-level MHE core upgrades.

## Core Principle

Treat MHE core upgrades as framework evolution, not feature accumulation. A good core upgrade extracts a reusable governance pattern from prior implementation experience, preserves current runtime truth, and makes new abstractions auditable before using them to justify stronger claims.

## Operating Bias

Prefer current code, tests, technical manual, upgrade analysis docs, and retained benchmark/research artifacts over chat memory or roadmap intent. Do not rewrite core architecture when a companion service, explicit boundary, or staged adapter can preserve existing behavior.

## Choose One Mode First

- **Framework Upgrade Design**: use when the user asks to evolve MHE core architecture, governance, runtime semantics, provenance, metrics, or research-loop capability.
- **Continuation / Resume**: use when the task starts from an existing blueprint, roadmap, handoff, plan draft, or partially landed core upgrade.
- **Implementation Slice**: use when a specific core service, model, CLI surface, persistence layer, policy gate, or test slice should be added.
- **Governance-Validation Slice**: use before promoting a new core abstraction into an enforced gate, automated decision, or manager-facing framework claim.
- **Verification / Audit Only**: use when checking whether a core upgrade is truthful, complete, or ready to promote in docs/roadmap.
- **Pattern Extraction**: use when prior upgrade experience should become reusable rules, skills, blueprints, or roadmaps.

Read `references/workflow-modes.md` first before multi-step work. Read `references/framework-upgrade-rules.md` when designing or extracting reusable framework-upgrade rules.

## Minimal Startup Checklist

1. Confirm the real target tree:
   - `MHE/src/metaharness/`
   - focused tests under `MHE/tests/`
   - relevant docs under `MHE/docs/`, `MHE/docs/wiki/`, or `MHE/docs/plan-drafts/`
2. Read implementation truth before design:
   - `MHE/docs/TECHNICAL_MANUAL.md`
   - `MHE/CLAUDE.md`
   - relevant current source and focused tests
3. If the task references prior upgrade experience, extract the general pattern first; do not copy the old solution shape blindly.
4. Identify the current authoritative layer: graph snapshot, runtime event, execution evidence, provenance/audit record, metrics, or research artifact.
5. Decide whether the change is implementation, docs/roadmap, verification-only, or skill/pattern extraction.
6. Pick the smallest slice that creates auditable evidence without breaking existing extension behavior.
7. Keep claims separate: implemented behavior, framework capability, policy boundary, future work, and non-claims.

## Reusable Framework-Upgrade Pattern

When upgrading MHE core, follow this pattern:

1. **Name the current substrate**: identify what the core already governs today, such as graph snapshots, component registry, boot lifecycle, execution evidence, or benchmark/research artifacts.
2. **Name the missing governance dimension**: identify the new axis that current abstractions cannot answer, such as runtime side effects, research-loop state, assembly lineage, copy count, instantiation boundary, or selection pressure.
3. **Separate instance from invariant**: state which observed upgrade experience is only an example, and which rule should become reusable core behavior.
4. **Add a companion layer before mutating core primitives**: prefer a ledger, gateway, index, policy gate, event stream, or dashboard over bloating `GraphSnapshot`, `ComponentRegistry`, `AuditLog`, or extension-specific models.
5. **Preserve authority boundaries**: XML is input, internal graph snapshots are runtime truth; plans/proposals are not execution; dry-run artifacts are not real-world instantiation; approval policy is not scientific validation.
6. **Propagate evidence end-to-end**: new concepts must appear in persisted records, CLI/report outputs, tests, docs, and roadmap/backlog consequences before they are used in conclusions.
7. **Use phased promotion**: design doc → smallest implementation slice → focused tests → artifact/report visibility → roadmap/handoff update → verification.
8. **State non-claims early**: every framework upgrade should say what it enables, what remains unproven, and what evidence would unlock stronger claims.

## Two Evidence Lenses

Use these two lenses when reviewing prior MHE core upgrade experience or proposing the next framework abstraction.

### Runtime Governance Lens

Ask whether the upgrade moves beyond graph validity into runtime truth. A credible runtime-governance upgrade should specify:

- the governed runtime action or side effect;
- the promotion gate that permits it;
- the rollback or downgrade path if it fails;
- the session events that record it;
- the execution evidence or external receipt that proves it happened;
- the provenance/audit links that make it reviewable.

Review these anchors before designing runtime governance changes: snapshot model, promotion path, safety gates, rollback target, session events, and audit/provenance records.

### Scientific Research-Loop Lens

Ask whether the upgrade moves beyond a single case run into durable research-loop state. A credible research-loop upgrade should specify:

- the research question, hypothesis, or decision being governed;
- the experiment/case/comparison evidence that informs it;
- the repair, failure taxonomy, negative-result memory, or repeat evidence produced;
- the report, conclusion, approval, or claim-boundary surface;
- the backlog/roadmap consequence that closes the loop.

Do not promote a research workflow into core if it only produces a one-off report without persisted artifacts, tests, and next-step governance.

## Lessons From Prior Core Upgrades

Use prior MHE core upgrades as examples of pattern extraction, not as templates to copy mechanically:

- A shift from graph governance toward runtime governance shows that a framework upgrade often starts by discovering a broader substrate: not only whether a graph is valid, but whether runtime actions, evidence, safety gates, rollback, and side effects are governed.
- A shift from case-oriented scientific execution toward research-loop governance shows that core abstractions should manage iterative inquiry: hypotheses, evidence, comparison, repair, reports, backlog, and conclusion boundaries, not only a single solver run.
- Assembly/instantiation analysis shows that complex framework capability needs history, reuse counts, selection pressure, and explicit simulation-versus-instantiation boundaries before stronger reliability claims are safe.

The universal rule is: when a repeated workflow outgrows the current abstraction, promote the missing invariant into a core-governed, testable, persisted, report-visible, and reviewable layer. Add governance in phases: record first, warn second, gate third, and automate promotion/retirement last.

## Core Anchor Map

Use these files as current-truth anchors before proposing or editing core behavior:

- `MHE/docs/TECHNICAL_MANUAL.md` — implementation-aligned current core behavior.
- `MHE/src/metaharness/core/boot.py` — `HarnessRuntime`, boot composition, graph promotion, safety review, rollback hooks.
- `MHE/src/metaharness/core/connection_engine.py` — candidate/active graph transitions and routing.
- `MHE/src/metaharness/core/models.py` — graph and validation models.
- `MHE/src/metaharness/core/graph_versions.py` — graph version, candidate, active, rollback, archive state.
- `MHE/src/metaharness/sdk/registry.py` — component registry, slot/capability indexes, pending declarations.
- `MHE/src/metaharness/sdk/dependency.py` — dependency ordering and DAG-like boot relation source.
- `MHE/src/metaharness/core/execution.py` — execution lifecycle and evidence recording.
- `MHE/src/metaharness/provenance/` — evidence graph, artifact snapshots, audit log, provenance queries.
- `MHE/src/metaharness/safety/` — safety pipeline, sandbox checks, rollback policy.
- `MHE/src/metaharness/observability/metrics.py` — metrics registry and statistics base.

## Read References On Demand

- `references/workflow-modes.md`
  - mode selection, target-tree guard, source-truth triage, resume behavior, minimum core slices, governance validation, and audit-only flow.
- `references/framework-upgrade-rules.md`
  - upgrade smells, pattern extraction, runtime governance lens, scientific research-loop lens, companion abstractions, evidence rules, and review checklist.

## Team Routing

- Load `omc-reference` before creating or using core-upgrade teammates; use the supported OMC team runtime (`TeamCreate`, shared `TaskCreate`/`TaskUpdate`, `Agent(..., team_name=...)`, `SendMessage`) rather than ad hoc pane or tmux management.
- Use `project-leader` when the task touches architecture blueprint, roadmap, handoff, benchmark/research direction, cross-slice coordination, reviewer gates, or manager-facing framework claims.
- For multi-slice core upgrades, create or reuse one named team, seed a shared task list, then assign role-specific teammates such as planner, implementer, verifier, test engineer, or docs reviewer.
- Keep leadership, implementation, and acceptance separate: implementers complete assigned slices, while a distinct reviewer/verifier provides the acceptance gate before closing architecture-sensitive work.
- Use read-only explore agents for broad source/doc mapping before major design, and direct single-use agents only for bounded audit, advisory checks, or final verification when team routing is unnecessary.
- Do not spawn large teams for narrow verification or skill/pattern extraction.
- If teammate pane creation fails, follow `project-leader` pane-capacity rules: do not retry the same spawn loop, do not close non-Claude user application panes, use existing routable teammates or `SendMessage` when possible, and pause or fall back to main-context coordination when concrete team execution cannot be spawned safely.

## Implementation Guardrails

- Preserve existing extension behavior when changing core interfaces.
- Prefer additive companion services over invasive rewrites.
- Keep optimizer/proposal systems proposal-only until explicit commit/safety/evidence paths promote them.
- Record invalid candidates, rejected promotions, dependency skips, and unsupported states explicitly.
- Make new runtime or research-loop concepts visible in persisted artifacts, not only in memory objects.
- Do not conflate graph validity, runtime instantiation, scientific correctness, human approval, or manager-facing readiness.
- Do not claim a framework capability from docs alone; require tests or retained artifacts.

## Verification Gate

Before calling a core upgrade complete, verify:

- focused core tests for the touched subsystem;
- extension regression tests if the change affects SDK/runtime contracts;
- provenance/audit/session/metrics persistence where relevant;
- docs truthfulness against implementation;
- claim-boundary wording for simulated, dry-run, instantiated, externally verified, approved, and scientifically validated states;
- independent reviewer/verifier acceptance for architecture-sensitive changes.

## Default Behavior

- Do **not** restart from first principles if current code already implements part of the architecture.
- Do **not** turn a one-off workflow into core unless the invariant recurs across extensions, benchmarks, or research loops.
- Do **not** bury framework boundaries in docs only; encode them in models, artifacts, tests, or gates.
- Do **not** overgeneralize domain-specific solver metrics into core semantics.
- If asked to summarize upgrade experience, extract portable rules first and cite prior upgrades only as examples.
