# Lean Proof Benchmark Evidence Roadmap

> Status: active roadmap; phases 1-5 have initial implementation evidence as of 2026-05-05.
> Scope: next evidence needed for `lean-proof` benchmark promotion after the initial simple theorem smoke.

## Current Evidence State

The current `lean-proof` evidence proves a bounded proof-workflow slice:

- `simple-true-proof`, `implication-chain-proof`, `conjunction-swap-proof`, and `project-helper-chain-proof` pass dry-run `extension`, `direct`, and `agent` lanes.
- `malformed-proposal-repair` preserves a deterministic dry-run repair contrast where direct fails contract validation and agent repairs from case defaults.
- Real Lean/Lake checks pass the positive theorem catalog, including the small Lake project fixture with `Helper.lean`.
- Repeated real-Claude + real-Lean comparison with `repeat_count = 2` passes all five cases across `extension`, `direct`, and `agent` lanes, with valid proposal contracts and zero repairs/failures in the real-Claude slice.
- `benchmark-compare --config-root .mhe` records configured approval as `approved_with_limitations` in comparison artifacts.
- CI dry ladder runs `ruff check`, focused Lean pytest, and dry-run benchmark smoke by default.

This evidence supports proof-workflow wiring, real-tool checkability for small cases, proposal-contract stability for two real-Claude repeats, and approval-boundary plumbing. It does not support theorem-discovery superiority, broad formalization quality, proof search quality, or runtime superiority.

## Evidence Gap Analysis

| Gap | Why it matters | Current risk | Evidence needed |
|---|---|---|---|
| Case difficulty | One `True` theorem is too easy to characterize Lean behavior. | Passing may only prove trivial syntax and pipeline wiring. | Add small but nontrivial theorem cases with assumptions and local reasoning. |
| Malformed proposal repair | Agent workflow advantage is not visible when direct and agent both pass. | No evidence for repair advantage or controlled validation. | Add a controlled malformed/underspecified proposal case where direct fails and agent repairs. |
| Proposal source visibility | Comparator must distinguish real, fake, fallback, and repaired proposals. | Proposal-source claims can be ambiguous. | Read Lean proposal contract artifacts into comparison context. |
| Repeated real-Claude evidence | One run cannot show stability or pass/repair rates. | Real-Claude success may be flaky. | Run repeated real-Claude comparison and aggregate contract/pass/repair rates. |
| Project-scale fixtures | Single-file proof does not test Lake project or blueprint behavior. | No evidence for multi-file formalization workflow. | Add a small project fixture with helper theorem and dependent theorem. |
| Approval plumbing | `benchmark-compare` currently records approval as `not_configured` without explicit config root. | Comparison bundle and approval-check evidence can diverge. | Make comparator-visible approval config path explicit or document the separate check. |

## Implementation Roadmap

### Phase 1: Controlled challenge cases

Goal: make the benchmark show more than a happy path while staying deterministic and safe.

Tasks:

1. Add `implication-chain-proof`, a nontrivial positive Lean theorem that requires applying a hypothesis. Done.
2. Add `conjunction-swap-proof`, a nontrivial positive Lean theorem that decomposes and rebuilds a conjunction. Done.
3. Add `malformed-proposal-repair`, a controlled workflow case where a fake/underspecified direct proposal fails contract validation and the agent lane repairs from case defaults. Done.
4. Extend the Lean proposal prompt to use each case's theorem statement instead of hard-coding `theorem main : True`. Done.
5. Preserve claim boundaries in each case spec. Done.

Acceptance criteria:

- Dry-run comparison includes at least one `all_passed` positive row and one repair-contrast row.
- The repair-contrast row exposes `direct_proposal_contract_status = invalid`, `agent_proposal_contract_status = valid`, `agent_repairs = 1`, and `repair_advantage = agent_repaired_direct_failure`.
- No dry-run row claims real Lean execution or theorem-search ability.

Validation commands:

```bash
ruff check src/metaharness_ext/lean tests/test_metaharness_lean_*.py src/metaharness/benchmark_drivers src/metaharness/cli.py
PYTHONPATH=src pytest tests/test_metaharness_lean_*.py
PYTHONPATH=src python -m metaharness.cli benchmark-run --suite lean-proof --lanes extension,direct,agent --cases simple-true-proof,implication-chain-proof,conjunction-swap-proof,project-helper-chain-proof,malformed-proposal-repair --runs-root .runs/lean-proof-challenge-dry
PYTHONPATH=src python -m metaharness.cli benchmark-compare --suite lean-proof --runs-root .runs/lean-proof-challenge-dry
```

### Phase 2: Real Lean positive smoke expansion

Goal: verify that added positive cases are executable with local Lean/Lake.

Tasks:

1. Run `extension` lane with `--allow-real-tools` for `simple-true-proof`, `implication-chain-proof`, `conjunction-swap-proof`, and `project-helper-chain-proof`. Done.
2. Preserve `lean_environment_report.json`, `lean_evidence_bundle.json`, `lean_run_artifact.json`, and claim-boundary artifacts. Done.
3. Classify missing Lean/Lake prerequisites as dependency skip, not failure. Done.

Acceptance criteria:

- Positive cases pass or produce capability skip evidence.
- Malformed proposal repair remains a workflow case and is not promoted as real proof superiority evidence.

### Phase 3: Repeated real-Claude challenge run

Goal: measure proposal stability without overstating proof quality.

Tasks:

1. Run real-Claude comparison for positive and repair-challenge cases with `--repeat 2`. Done at `.runs/lean-proof-real-claude-challenge-r2`.
2. Track pass rate, proposal-contract validity rate, repair rate, failure category rate, and flaky rows. Done through `repeat_summary.json` and `result_bundle.json`.
3. Preserve `run_manifest.json`, `summary_table.csv`, `result_bundle.json`, `comparison_report.md`, and approval output. Done.

Acceptance criteria:

- Report distinguishes real Lean execution from real Claude proposal quality.
- Any agent advantage is expressed as pass/repair-rate evidence, not theorem-proving superiority.

### Phase 4: Project-scale Lean fixture

Goal: test small Lake project workflow and blueprint-style dependency evidence.

Tasks:

1. Add a two-declaration fixture with a helper theorem and dependent `main` theorem. Done as `project-helper-chain-proof`.
2. Capture project metadata: toolchain, Lake file, target file, helper dependency, and validation status. Done through case `project_files`, generated `lakefile.lean`, `lean_task_spec.json`, and `lean_evidence_bundle.json`.
3. Extend evidence bundle assertions to ensure helper/dependent artifacts stay auditable. Done in focused Lean benchmark tests.

Acceptance criteria:

- The benchmark can run a small project fixture in dry-run and opt-in real-tool mode.
- Evidence separates project orchestration success from broad formalization claims.

### Phase 5: Comparator approval plumbing

Goal: reduce divergence between comparison bundle approval status and separate approval-check output.

Tasks:

1. Add a `benchmark-compare --config-root` option or equivalent plumbing. Done.
2. Pass `.mhe` approval policy into `write_comparison_outputs`. Done.
3. Add a test proving `approval_gate.json` records configured approval for `lean-proof`. Done.

Acceptance criteria:

- Comparison artifacts no longer show `not_configured` when `.mhe` approval policy exists.
- Approval status remains `approved_with_limitations` and continues to exclude numerical/runtime/scientific superiority claims.

## Claim Boundary

The roadmap strengthens workflow evidence: proposal contracts, repair visibility, real-tool gating, repeated proposal stability, project artifact retention, and approval-boundary consistency. The 2026-05-05 repeated run shows 2/2 pass counts for every lane/case row in the retained challenge catalog and zero real-Claude repairs/failures. It does not claim Lean theorem-discovery superiority or mathematical creativity. Stronger proof-quality claims still require harder expert-reviewed theorem suites, larger repeat counts, direct prompt stress cases, and human mathematical review.

## Terminology Explanation

`challenge case` means a benchmark case designed to expose a specific behavior, such as malformed proposal repair. `proposal contract` is the required JSON/source shape for Claude output. `repair advantage` means the agent lane repaired a proposal failure that direct could not handle. `real Lean smoke` means Lean/Lake actually checked the file. `repeated real-Claude` means running real Claude proposal generation multiple times to estimate stability. `project-scale fixture` means a small Lean project with more than one declaration or file, not a full Mathlib-scale formalization. `approved_with_limitations` means the benchmark comparison is allowed only inside the documented claim boundary and still excludes numerical/runtime/scientific superiority claims.
