# Lean Proof Benchmark Evidence Roadmap

> Status: active roadmap; phases 1-7 have implementation evidence as of 2026-05-06.
> Scope: next evidence needed for `lean-proof` benchmark promotion after the initial simple theorem smoke.

## Current Evidence State

The current `lean-proof` evidence proves a bounded proof-workflow slice:

- `simple-true-proof`, `implication-chain-proof`, `conjunction-swap-proof`, `negation-contrapositive-proof`, `exists-conjunction-swap-proof`, `project-helper-chain-proof`, and `blueprint-structure-project-proof` pass dry-run `extension`, `direct`, and `agent` lanes.
- `malformed-proposal-repair` preserves a deterministic dry-run repair contrast where direct fails contract validation and agent repairs from case defaults.
- `underspecified-real-claude-stress`, `malformed-json-real-claude-stress`, and `sorry-proof-real-claude-stress` preserve stress-prompt coverage for natural-language non-contract, missing-field JSON, and incomplete-`sorry` source proposals.
- Curated harder theorem cases now emit `lean_human_review_manifest.json` with `external_review_status = pending_external_signoff`, making the missing external review artifact explicit instead of implicit.
- Real Lean/Lake checks pass the positive theorem catalog, including the small Lake project fixture with `Helper.lean` and a blueprint-style project with `Blueprint/Domain.lean` and `Blueprint/Proof.lean`.
- `mathlib-add-zero-sentinel` records a dependency-gated Mathlib sentinel with `promotion_ready = false` and `mathlib_scale_claim = dependency_gated_not_promoted`; it is not Mathlib-scale coverage evidence.
- Repeated real-Claude + real-Lean comparison with `repeat_count = 3` passes all positive cases across `extension`, `direct`, and `agent` lanes; the original stress case records `direct failed_count = 3` and `agent passed_count = 3`.
- `benchmark-compare --config-root .mhe` records configured approval as `approved_with_limitations` in comparison artifacts.
- CI dry ladder runs `ruff check`, focused Lean pytest, and dry-run benchmark smoke by default.

This evidence supports proof-workflow wiring, real-tool checkability for small cases, proposal-contract stability for three real-Claude repeats, stress-prompt contract gating, blueprint-style project artifact retention, pending human-review visibility, Mathlib sentinel skip evidence, theorem-family proposal-rate reporting, and approval-boundary plumbing. It does not support theorem-discovery superiority, broad formalization quality, proof search quality, completed external human review, Mathlib-scale coverage, or runtime superiority.

## Evidence Gap Analysis

| Gap | Why it matters | Current risk | Evidence needed |
|---|---|---|---|
| Case difficulty | One `True` theorem is too easy to characterize Lean behavior. | Passing may only prove trivial syntax and pipeline wiring. | Add small but nontrivial theorem cases with assumptions and local reasoning. |
| Malformed proposal repair | Agent workflow advantage is not visible when direct and agent both pass. | No evidence for repair advantage or controlled validation. | Add a controlled malformed/underspecified proposal case where direct fails and agent repairs. |
| Proposal source visibility | Comparator must distinguish real, fake, fallback, and repaired proposals. | Proposal-source claims can be ambiguous. | Read Lean proposal contract artifacts into comparison context. |
| Repeated real-Claude evidence | One run cannot show stability or pass/repair rates. | Real-Claude success may be flaky. | Run repeated real-Claude comparison and aggregate contract/pass/repair rates. |
| Project-scale fixtures | Single-file proof does not test Lake project or blueprint behavior. | No evidence for multi-file formalization workflow. | Add a small project fixture with helper theorem and dependent theorem. |
| Approval plumbing | `benchmark-compare` can now read explicit config root. | Approval evidence can still be overinterpreted as scientific approval. | Keep `approved_with_limitations` and excluded claims in reports. |
| Human mathematical review | Curated harder cases are Lean-validated and now emit pending review manifests, but no external signoff exists. | Reports could imply human mathematical review that has not happened. | Keep `external_review_status = pending_external_signoff` until a signed external review artifact exists. |
| Mathlib-scale coverage | Blueprint-style project fixture tests project orchestration; Mathlib sentinel is dependency-gated and skipped. | Passing a small project or skipped sentinel could be overclaimed as broad formalization quality. | Add executable Mathlib fixtures only behind dependency gates and separate non-claims. |
| Theorem-family rates | Per-case repeat rows can hide systematic prompt-family behavior. | Reports may miss whether failures cluster by stress prompt, project fixture, or theorem family. | Aggregate proposal validity and repair rates by `theorem_family`. |

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

### Phase 6: Expanded repeat, stress, and blueprint evidence

Goal: move from minimal repeated evidence to a broader challenge slice while keeping review boundaries explicit.

Tasks:

1. Add curated harder theorem cases: `negation-contrapositive-proof` and `exists-conjunction-swap-proof`. Done, with `human_math_review = pending_external_signoff`.
2. Add a real-Claude stress prompt case: `underspecified-real-claude-stress`. Done.
3. Add a blueprint-style project fixture: `blueprint-structure-project-proof`. Done, without claiming Mathlib-scale coverage.
4. Run expanded real-Claude + real-Lean comparison with `repeat_count = 3`. Done at `.runs/lean-proof-expanded-real-claude-r3`.
5. Preserve dry stress evidence at `.runs/lean-proof-expanded-dry`. Done.

Acceptance criteria:

- Positive cases report `passed_count = 3`, `failed_count = 0`, and no flaky flags in repeated real evidence.
- Stress case reports direct proposal-contract failure and agent success in real-Claude evidence.
- Reports distinguish Lean validation from external human mathematical review.
- Reports distinguish blueprint-style project evidence from Mathlib-scale evidence.

Validation commands:

```bash
ruff check src/metaharness_ext/lean tests/test_metaharness_lean_*.py src/metaharness/cli.py
PYTHONPATH=src pytest tests/test_metaharness_lean_*.py
PYTHONPATH=src python -m metaharness.cli benchmark-run --suite lean-proof --lanes extension,direct,agent --cases simple-true-proof,implication-chain-proof,conjunction-swap-proof,negation-contrapositive-proof,exists-conjunction-swap-proof,project-helper-chain-proof,blueprint-structure-project-proof,malformed-proposal-repair,underspecified-real-claude-stress --runs-root .runs/lean-proof-expanded-real-claude-r3 --allow-real-tools --allow-real-claude --repeat 3 --claude-max-turns 1 --claude-permission-mode bypassPermissions
PYTHONPATH=src python -m metaharness.cli benchmark-compare --suite lean-proof --runs-root .runs/lean-proof-expanded-real-claude-r3 --allow-real-tools --allow-real-claude --repeat 3 --config-root .mhe
```

### Phase 7: Review manifests, gated repeats, stress variants, Mathlib sentinel, and family rates

Goal: make the remaining promotion blockers reviewer-visible without turning them into unsupported proof-quality claims.

Tasks:

1. Emit `lean_human_review_manifest.json` for curated harder theorem cases. Done, with `external_review_status = pending_external_signoff`.
2. Add more stress prompt variants: `malformed-json-real-claude-stress` and `sorry-proof-real-claude-stress`. Done.
3. Add `mathlib-add-zero-sentinel` as a dependency-gated Mathlib sentinel. Done, with `promotion_ready = false` until a Mathlib dependency gate is configured.
4. Add theorem-family proposal validity and repair-rate aggregation to comparison evidence and generated reports. Done.
5. Extend gated workflows so `lean-proof` can be selected in weekly real-Claude and nightly real-tools jobs. Done.
6. Preserve expanded dry validation evidence at `.runs/lean-proof-next-evidence-dry`. Done.

Acceptance criteria:

- Curated cases expose pending external human review as an artifact, not only metadata.
- Stress prompt variants preserve direct contract failure and agent repair/success evidence in dry comparison.
- Mathlib sentinel rows skip with explicit dependency-gate evidence and no Mathlib-scale coverage claim.
- Comparison bundles include `theorem_family_repeat_rows` with pass, contract-validity, invalid-contract, and repair rates.
- Larger repeats remain gated/manual/scheduled, not default PR CI.

## Claim Boundary

The roadmap strengthens workflow evidence: proposal contracts, repair visibility, real-tool gating, repeated proposal stability, project artifact retention, stress-prompt behavior, pending human-review visibility, Mathlib dependency gating, theorem-family rate reporting, and approval-boundary consistency. The 2026-05-06 repeated run shows `repeat_count = 3`; positive cases pass for every lane, while `underspecified-real-claude-stress` records direct contract failure and agent success. Phase 7 adds new dry/gated evidence paths but does not by itself rerun a larger final real-Claude comparison. It does not claim Lean theorem-discovery superiority, mathematical creativity, completed external human mathematical review, Mathlib-scale coverage, or runtime superiority. Stronger proof-quality claims still require signed external review artifacts, larger retained real-Claude repeats, broader stress runs, executable Mathlib dependency gates, and reviewed theorem suites.

## Terminology Explanation

`challenge case` means a benchmark case designed to expose a specific behavior, such as malformed proposal repair. `proposal contract` is the required JSON/source shape for Claude output. `repair advantage` means the agent lane repaired a proposal failure that direct could not handle. `real Lean smoke` means Lean/Lake actually checked the file. `repeated real-Claude` means running real Claude proposal generation multiple times to estimate stability. `stress prompt` means a prompt deliberately made underspecified or non-contract-shaped to test validation and recovery behavior. `project-scale fixture` means a small Lean project with more than one declaration or file, not a full Mathlib-scale formalization. `blueprint-style project` means a local project shaped like a formalization plan with domain/proof modules, not an actual Mathlib-scale development. `human_math_review = pending_external_signoff` and `external_review_status = pending_external_signoff` mean Lean validated the fixture but no signed external human mathematical approval artifact has been recorded. `Mathlib sentinel` means a case that records the missing Mathlib dependency gate and must stay skipped until executable Mathlib setup exists. `theorem_family_repeat_rows` means proposal validity, failure, and repair rates grouped by theorem or prompt family rather than only by individual case. `approved_with_limitations` means the benchmark comparison is allowed only inside the documented claim boundary and still excludes numerical/runtime/scientific superiority claims.
