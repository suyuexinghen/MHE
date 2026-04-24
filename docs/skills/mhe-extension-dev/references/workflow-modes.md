# Workflow Modes

Use this file to choose the right workflow before reading heavier references.

## Target-Tree Guard

Before doing any substantive work, confirm the real target tree contains the extension under the same root:
- `MHE/src/metaharness_ext/<name>/`
- `MHE/tests/test_metaharness_<name>_*.py`
- the extension docs / handoff / roadmap you intend to update

If the active Claude CWD is not the real target tree, stop and locate the correct tree before editing.

## Untracked Extension Tree Warning

If `git status --short` shows untracked extension paths such as:
- `?? MHE/src/metaharness_ext/<name>/`
- `?? MHE/tests/test_metaharness_<name>_*.py`

then isolated worktree agents may miss the real extension state.

In that case:
- inspect the absolute target paths directly
- do not assume a clean worktree copy is the source of truth
- verify docs/tests/code from the same real target tree before making changes

## Resume After Team/Task State Loss

When team state, task state, or agent history is cleared or looks stale:
1. Do **not** assume the implementation work was lost.
2. Verify the current main worktree first:
   - grep/read expected code anchors
   - run focused tests
   - run `ruff`
3. Reconstruct only missing coordination state if needed.
4. Report **code truth** separately from **orchestration truth**.

If orchestration state conflicts with code/test state, trust verified code/test state.
Treat team/task state as coordination metadata, not implementation truth.

## Mode A: Greenfield

Use when the extension does not yet have a meaningful wiki / blueprint / handoff baseline.

Start here:
1. Read MHE framework docs, target software docs, and existing extension patterns.
2. Identify the numbered blueprint slot for the extension.
3. Create the extension design wiki from `wiki-outline-template.md`.
4. Create the numbered blueprint, roadmap, and implementation-plan docs.
5. Then move into the smallest implementation slice.

## Mode B: Continuation / Resume

Use when the user says things like:
- "Continue from where you left off"
- "refer to `*_EXTENSION_HANDOFF_REPORT.md`"
- "continue Phase N"
- "sync the handoff/roadmap/wiki and keep going"

Start here:
1. Read `MHE/docs/<NAME>_EXTENSION_HANDOFF_REPORT.md` if it exists.
2. Read the numbered roadmap / blueprint docs for the extension.
3. Read the current extension code and focused tests.
4. Identify the **smallest unfinished slice** that moves the extension forward truthfully.
5. Resume directly from that slice.

Do not restart from Phase 0 unless the existing docs are missing or untrustworthy.

## Mode C: Verification / Audit Only

Use when the user asks to:
- verify work progress
- check whether a slice is complete
- validate recent changes
- recommend next steps

Default behavior:
- Do **not** enter plan mode by default.
- Do **not** create a team by default.
- Use one auditor agent or no agent unless verification reveals a complex unresolved problem.
- Report findings directly unless the user explicitly asks to create task-list items.

Verification flow:
1. Read current code, focused tests, manifests, wiki, roadmap, and handoff.
2. Check truth at four layers:
   - code/test truth
   - manifest/interface truth
   - wiki/design truth
   - roadmap/handoff truth
3. Run targeted extension verification.
4. Audit semantics for the claimed behavior.
5. Report:
   - passed
   - concerns / drift
   - recommendation
   - next smallest slice

Verification checklist:
- Check code semantics against stated design.
- Run focused extension tests.
- Run `ruff` on the extension and touched tests.
- Check manifest / `declare_interface` / contract drift.
- Check docs / handoff / roadmap truthfulness.
- Recommend the next smallest slice only if needed.
