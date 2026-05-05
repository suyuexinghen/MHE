# Lean Extension for MHE Wiki

> Version: v0.1-proposed | Last updated: 2026-05-04

This directory discusses how to design `metaharness_ext.lean` inside MHE.

The Lean extension is proposed as an MHE-native proof-engineering integration for Lean projects. It is intended to make Lean task intake, project probing, blueprint compilation, proof-workspace preparation, execution, validation, and evidence boundaries explicit through typed MHE components.

Important: this extension is still a proposed design. The presence of this wiki does not mean Lean runtime execution, theorem proving, or proof repair has been implemented.

## Navigation

| Document | Topic | Audience |
|---|---|---|
| `README.md` | Design router, status, and reading path | Everyone |
| `../blueprint/14-lean-extension-blueprint.md` | Durable design position and contract boundaries | Architects / extension implementers |
| `../blueprint/14-lean-roadmap.md` | Proposed execution phases and support matrix target | Project leads / implementers |
| `../blueprint/14-lean-implementation-plan.md` | First executable baseline slice | Implementers / reviewers |

## Terminology

| Term | Meaning |
|---|---|
| Lean task | A typed MHE request involving a Lean file, declaration, project, or proof-audit target. |
| Blueprint item | A dependency-aware definition, lemma, theorem, or proof target in a formalization plan. |
| Proof workspace | A bounded workspace or artifact model for proof attempts and validation inputs. |
| Mocked execution | Test-mode simulated Lean outcomes; proves MHE wiring only. |
| Dry-run | Command/workspace planning without calling Lean or Lake. |
| Real check | Opt-in execution of local Lean/Lake commands against a real project. |
| Formal completeness | Lean accepts the target and no disallowed `sorry` remains. |
| Policy acceptance | MHE governance accepts the validation/evidence boundary for the requested mode. |

## Design Principles

- Treat Lean compiler and diagnostic feedback as runtime evidence, not final-only prose.
- Keep proof task contracts separate from autonomous proof-search strategy.
- Make `sorry`, statement drift, and environment skips visible in validation reports.
- Use mocked and dry-run paths before opt-in real Lean execution.
- Distinguish compiler success from proof readability, Mathlib style, and scientific significance.
- Preserve plan, run, artifact, and validation identities in evidence bundles.

## MHE Integration Stance

The proposed component chain is:

```text
Lean gateway
  -> Lean environment probe
    -> Lean blueprint compiler
      -> Lean proof workspace
        -> Lean executor
          -> Lean validator
            -> Lean evidence / policy adapter
```

MHE core owns graph assembly, manifests, lifecycle, provenance, protected slots, policy, and benchmark/report surfaces. The Lean extension owns Lean-specific task semantics, project probing, command planning, diagnostic interpretation, and proof evidence shaping.

## Design Sources

This wiki borrows design lessons from Numina-Lean-Agent without aligning to it as an implementation target:

- blueprint DAGs for long formalization work;
- feedback-driven proof loops;
- subgoal isolation for context control;
- informal strategy refinement as a separate concern;
- validation that keeps incomplete proof state explicit.

These ideas are adapted to MHE’s component, manifest, validation, and evidence model rather than copied as a Claude Code agent pipeline.

## Division of Responsibility

- **Wiki**: stable design boundaries and terminology.
- **Blueprint**: durable extension architecture and invariants.
- **Roadmap**: proposed phase ordering, remaining slices, risks, and support matrix targets.
- **Implementation plan**: the smallest actionable slice for code and tests.
- **Tests/evidence**: source of truth for what has actually landed.

## Recommended Reading Order

For design review:

1. `README.md`
2. `../blueprint/14-lean-extension-blueprint.md`
3. `../blueprint/14-lean-roadmap.md`

For implementation:

1. `../blueprint/14-lean-implementation-plan.md`
2. existing extension examples under `src/metaharness_ext/abacus/` and `src/metaharness_ext/qcompute/`
3. existing manifest parity tests under `tests/test_metaharness_abacus_manifest.py` and `tests/test_metaharness_qcompute_manifest.py`

For claim review:

1. `../blueprint/14-lean-roadmap.md`
2. focused Lean extension tests once they exist
3. support matrix language in any repository-level README update

## Out of Scope for This Wiki

- Lean language tutorial;
- Mathlib contribution guide;
- Numina-Lean-Agent setup guide;
- external theorem-search service manual;
- benchmark leaderboard claims;
- proof-generation prompt recipes;
- daily rollout logs.

## Current Claim Boundary

Until implementation and tests land, the Lean extension can only be described as proposed. After the first implementation slice, the expected claim should be limited to contract and manifest baseline support unless mocked runtime tests also land.

Real Lean execution should only be claimed after an opt-in real smoke test preserves command, environment, log, artifact, and validation evidence.
