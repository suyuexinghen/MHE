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
4. Decide whether this is implementation or verification-only.
5. Pick the **smallest next slice** that can be completed truthfully.
6. Read only the references needed for the current slice.

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
