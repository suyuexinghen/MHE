# 07. Scope and Boundaries

## 1. Wiki Responsibility

This wiki (`fealpy-engine-wiki/`) discusses **how the extension should be designed** — stable design boundaries, component responsibilities, contract shapes, and family design rules. It does not track implementation progress or phase sequencing.

## 2. Blueprint Responsibility

`blueprint/08-fealpy-extension-blueprint.md` is the formal design position document. It covers:
- Extension goals, domain boundaries, design stance
- Component chain architecture
- Contracts design rationale
- Security and governance model
- Test strategy
- Risk register

The blueprint should remain stable across implementation phases. When implementation reveals new design constraints, update the blueprint to reflect them.

## 3. Roadmap Responsibility

`blueprint/08-fealpy-roadmap.md` is the execution roadmap. It covers:
- Current state snapshot (files, tests, components)
- Completed phase summaries
- Remaining gap analysis
- Phase map overview
- Risk/dependency tracking

Update the roadmap after each phase completion. The roadmap is the single source of truth for "what's done and what's next."

## 4. Implementation Plan Responsibility

Implementation plans (e.g., `.claude/plans/*.md`) are ephemeral execution documents for a single slice of work. They should reference the blueprint and roadmap, not duplicate them. Archive or delete after the slice is complete.

## 5. Historical Material

This extension currently has no `.trash/` directory. If old blueprint/roadmap versions need preservation, create `.trash/` under `docs/wiki/meta-harness-engineer/` rather than leaving stale docs in active paths.

## 6. Explicit Out of Scope

### Not in This Wiki
- fealpy library user manual — see `/home/linden/code/work/Solvers/python/fealpy/docs/`
- fealpy build/install guide
- MHE core architecture — see `meta-harness-wiki/`
- Daily rollout logs or operational runbooks

### Not in This Extension
- FVM, VEM, CDG, CEM, CFD computation modes
- fealpy ML modules (PINN, PENN, RFM)
- Adaptive mesh refinement execution (field declared in contracts, not enforced)
- External user-provided script execution (compiler-generated scripts only)
- Full fealpy PDE catalog parity — 18 of 32 recognized families rendered, remaining fall back to scalar diffusion

## 7. Version Compatibility

| Component | Pinned Version | Notes |
|---|---|---|
| fealpy | v3.4.0 | Environment probe reports actual version |
| numpy | Any (required) | Backend must be importable |
| pytorch | Any (optional) | Checked but not required |
| jax | Any (optional) | Checked but not required |
| MHE core | ≥0.1.0 | Per manifest `harness_version` |

The environment probe reports actual versions at runtime. Breaking fealpy API changes are the primary risk — mitigation is version pinning and probe-based gating.
