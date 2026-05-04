# Team, Verification, and Handoff

Use this file when the task needs implementation lanes, focused verification, or handoff synchronization.

## Coverage / Docs-Only Slice

Use a coverage/docs-only slice when the remaining work is mainly:
- adding focused regression or E2E coverage
- proving one registry / plugin-path execution path
- tightening a support matrix tied to tested coverage
- syncing docs / handoff truth after code already landed

In this slice:
- avoid unnecessary production refactors
- inspect current tests first
- edit one canonical docs file when possible
- use focused read/grep verification for docs truthfulness
- run relevant tests when the docs claim depends on recent test additions
- update support matrix / handoff only if tested support status changes

If code/tests pass but roadmap or handoff still says landed work is remaining, create a docs-only sync slice before continuing feature work.

## Registry Proof Terminology

Do not use ambiguous "registry/plugin-path proof" wording.

Use one of these explicit proof types:
- **manifest-registry proof**: `load_manifest`, `declare_component`, and `ComponentRegistry`-based proof
- **plugin-path discovery proof**: environment/path-based dynamic discovery such as `METAHARNESS_PLUGIN_PATH`

Name TODOs, tests, and docs using the correct proof type.

## Governance Seam Pattern

For non-short-circuit environment/governance findings, prefer this seam:
1. keep the executor path unchanged
2. attach findings to evidence bundle metadata / warnings / provenance
3. let policy produce explicit gates
4. let governance convert those gates into validation issues
5. add minimal demo coverage proving the executor still ran

Do not short-circuit gateway/executor flow for environment findings unless the user explicitly asks.
Prefer:
- probe → execute → validate → evidence / policy / governance

## Docs Matrix Placement Rule

Before writing a support matrix, choose exactly one canonical location:
- family support status → `07-family-design.md`
- test strategy matrix → `09-testing-and-review.md`

Do not create both unless the user explicitly asks for both.

## Team Strategy

If a team for the extension already exists, reuse it and append lanes instead of creating a fresh phase team.

Create a new team only when there is not already a healthy team context for the same extension slice.

If a team lookup fails or prior team state disappeared:
1. do not treat this as implementation failure
2. verify current files/tests in the main worktree first
3. create a new narrow team only if meaningful work remains

When the work is verification-only, recommendation-only, or clearly a single narrow slice, prefer:
- no team, or
- one auditor / verifier agent

Possible narrow lanes for continuation work:
- `<name>-hofx-coder`
- `<name>-forecast-coder`
- `<name>-registry-coder`
- `<name>-docs-writer`
- `<name>-todo-verifier`

Task assignment should match the actual slice rather than force production-code work when the remaining gap is tests/docs.

## Shared-Contract Broadcast Rule

If one agent changes a shared contract, payload, manifest shape, validator output, evidence surface, or governed handoff semantics, broadcast that change immediately to the relevant teammates.

When reconciling multi-agent work, preserve the merge-ready agent's stated invariants unless tests or current code prove them wrong.

## Late Agent Handoff Conflict Handling

If a delayed handoff arrives after target-tree work is already verified:
- compare it only for missed facts or evidence
- do not blindly merge duplicate docs or duplicate fixes
- preserve the final decision and any rejected duplicate handoff in the final report

## Multi-Worktree Merge Strategy

After each agent handoff, the lead must:
1. inspect the diff directly
2. accept only the intended files or hunks from that worktree
3. merge/cherry-pick/apply accepted changes into the main working tree
4. confirm the changes are in the main worktree, not only the worktree branch
5. rerun focused tests for the accepted slice before final verification
6. run `ruff` yourself before marking the slice done

Do not blindly merge every worktree result when multiple coder lanes are active.

## Verification Commands

Standard focused verification:

```bash
pytest MHE/tests/test_metaharness_<name>_*.py -v
ruff check MHE/src/metaharness_ext/<name>/
ruff format MHE/src/metaharness_ext/<name>/
pytest MHE/tests/test_metaharness_<name>_minimal_demo.py -v
pytest MHE/tests/test_metaharness_<name>_environment.py -v
pytest MHE/tests/test_metaharness_<name>_compiler.py -v
pytest MHE/tests/test_metaharness_<name>_validator.py -v
```

DeepMD-like governance seam template:

```bash
PYTHONPATH=MHE/src pytest \
  MHE/tests/test_metaharness_<name>_evidence.py \
  MHE/tests/test_metaharness_<name>_policy.py \
  MHE/tests/test_metaharness_<name>_governance.py \
  MHE/tests/test_metaharness_<name>_environment.py \
  MHE/tests/test_metaharness_<name>_minimal_demo.py

ruff check \
  MHE/src/metaharness_ext/<name> \
  MHE/tests/test_metaharness_<name>_*.py
```

## Manual Review Pass

After automated checks pass, perform one manual review pass before committing:
- read the changed code directly
- confirm naming and file placement fit local patterns
- confirm docs reflect actual code rather than intended future state
- confirm no oversized scope slipped into the slice
- confirm no stale TODO-ish wording remains in roadmap/handoff
- confirm tested support claims match current evidence

## No-Op Audit Outcome

If the audit shows the code is already correct:
- do not force code churn just to make a change
- tighten tests, docs, roadmap truthfulness, or handoff precision instead
- if nothing needs changing, report that the slice is already landed and identify the next smallest unfinished slice

## Verification Fan-Out Rule

In verification-only mode, do not create duplicate verification tasks by default.

Report findings directly unless the user explicitly asks for task-list items or follow-up task decomposition.

## Commit and Handoff Rules

When a slice passes verification:
- stage only the extension-relevant slice
- separate unrelated pre-existing repo edits from the extension work
- avoid broad doc churn unless needed for truthfulness of this slice
- for one-test or docs-only slices, skip broad doc rewrites unless public support status changes

Update the handoff report after each landed slice:
- mark the completed phase or slice
- update the current next step to the next smallest slice
- sync roadmap/wiki status to landed code
