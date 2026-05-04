---
name: mhe-extension-dev
description: Build, continue, or verify a Meta-Harness Engine extension (`metaharness_ext.<name>`). Use for: creating a new MHE extension, resuming from handoff/roadmap/wiki, verifying extension progress, checking docs/backlog truthfulness, or coordinating extension implementation/tests/docs across parallel lanes. Triggers: "develop MHE extension", "build extension for MHE", "implement extension", "continue extension from handoff", "resume Phase N", "verify MHE extension progress", "recommend next extension slice", "add new extension to MHE".
---

# MHE Extension Development

Use this skill as a lightweight router.

## Operating Bias

Prefer current code, tests, manifests, wiki, roadmap, and handoff over noisy transcript residue.

## Choose One Mode First

- **Greenfield**: use when the extension does not yet have a meaningful wiki / blueprint / handoff baseline.
- **Continuation / Resume**: use when the task starts from an existing handoff, roadmap, or partially landed implementation.
- **Verification / Audit Only**: use when the user asks to verify progress, validate recent changes, or recommend next steps without asking for new implementation.

Read `references/workflow-modes.md` before doing multi-step work.

## Minimal Startup Checklist

1. Confirm the **real target tree** before reading or editing:
   - `MHE/src/metaharness_ext/<name>/`
   - `MHE/tests/test_metaharness_<name>_*.py`
   - extension docs under the same tree
2. If the active Claude CWD is not the real extension tree, stop and locate the correct tree first.
3. Read the current handoff, roadmap, code, and focused tests if they exist.
4. Triage **source truth** before design: compare local docs, source README/tutorials, examples, and actual CLI/runtime behavior; if they describe different projects, anchor claims to the target source tree and call out the mismatch.
5. Decide whether this is implementation or verification-only.
6. Pick the **smallest next slice** that can be completed truthfully.
7. Read only the references needed for the current slice.

## Team Routing

- Load `omc-reference` before creating or using extension teammates; use the supported OMC team runtime (`TeamCreate`, shared `TaskCreate`/`TaskUpdate`, `Agent(..., team_name=...)`, `SendMessage`) rather than ad hoc pane or tmux management.
- Use `project-leader` when the task touches roadmap, wiki, handoff, benchmark direction, cross-slice coordination, reviewer gates, or portfolio-level extension planning.
- For multi-extension implementation, create or reuse one named team, seed a shared task list, then assign role-specific teammates such as auditor, solver executor, research executor, QCompute executor, and verifier.
- Keep leadership, implementation, and acceptance separate: implementers complete assigned task slices, while a distinct reviewer/verifier provides the acceptance gate before closing the work.
- Use direct single-use agents only for bounded explore, read-only audit, one-off advisory checks, or final verification when team routing is unnecessary or unavailable.
- If teammate pane creation fails, follow `project-leader` pane-capacity rules: do not retry the same spawn loop, do not close non-Claude user application panes, use existing routable teammates or `SendMessage` when possible, and pause or fall back to main-context coordination when concrete team execution cannot be spawned safely.

## Greenfield Minimum Slice

For a new runnable extension, aim for the smallest truthful package that includes contracts, capabilities, slots, component manifests, example manifests, mocked runtime tests, and bounded docs/roadmap coverage.

## Usage-Validation Slice

After the baseline extension is implemented, prefer a dry-run usage-validation slice before any opt-in real binary smoke work. Compare extension, direct CLI/manual, and agent-assisted lanes, and keep real execution explicitly opt-in and environment-gated.

## Claim Boundaries

- Keep docs explicit about implemented, proposed, opt-in, future-work, and non-goal claims.
- Do not let roadmap or README text imply real execution support unless evidence exists.
- When source docs, examples, and runtime behavior disagree, anchor claims to the target source tree and call out the mismatch.

## Roadmap Hygiene

- Move accepted baseline items out of acceptance debt and into future work.
- Keep backlog items clearly separated from implemented slices.
- Update wiki and README indexes whenever extension status changes.

## Post-Greenfield Verification Gate

Before calling a greenfield slice complete, check manifest/runtime consistency, artifact identity provenance, custom workspace output discovery, docs truthfulness boundaries, focused tests, `ruff`, and independent reviewer/verifier acceptance.

## Read References On Demand

- `references/workflow-modes.md`
  - mode selection, startup flow, and verification-only behavior
- `references/phase-playbook.md`
  - detailed Phase 0–5 workflow, numbered blueprint naming, and doc truthfulness rules
- `references/design-doc-templates.md`
  - concrete blueprint, roadmap, fallback, implementation-plan, and handoff templates
- `references/wiki-outline-template.md`
  - canonical extension design wiki structure, README framing, and page-set choices
- `references/tested-support-matrix-template.md`
  - tested support matrix template for docs

## Default Behavior

- Do **not** start with a large team when the task is verification-only or a narrow docs/test slice.
- Do **not** restart from Phase 0 if continuation materials are already trustworthy.
- Do **not** overstate readiness in docs.
- Do **not** force code churn when audit shows the implementation is already correct.
- If the task spans roadmap, wiki, handoff, or cross-slice coordination, load and use `project-leader` to preserve the macro project schema and provide handoff directions.
