# MOOSE Extension Roadmap

## Phase 1

- Land the package skeleton, manifests, and the core runtime components.
- Keep the slice limited to input files, execution, and evidence capture.
- Verify the package with mocked subprocess and path-based tests.

## Phase 2

- Add a small catalog of input templates for common finite-element patterns.
- Add richer artifact discovery for Exodus outputs and log summaries.
- Add study support for parameterized input placeholders.

## Phase 3

- Add optional source-tree awareness for generated app layouts.
- Add policy gates for large runs, mesh-only shortcuts, and output completeness.
- Add better provenance around input template provenance and output files.

## Phase 4

- Expand validation to inspect numeric summaries where available.
- Add domain-specific helper flows for common MOOSE tutorial cases.
- Keep the runtime claims aligned with the executable and the available outputs.

## Next Evidence Roadmap

The CI/CD benchmark integration made the next MOOSE evidence ladder explicit. Treat these as claim-boundary upgrades, not as solver superiority claims.

| Priority | Evidence slice | Implementation target | Acceptance evidence | Claim boundary |
|---|---|---|---|---|
| High | Repeated real extension smoke | Run `simple-diffusion-hit` through the extension lane multiple times behind `--allow-real-tools` and local MOOSE environment gates | retained per-repeat summaries, environment reports, run artifacts, validation reports, and aggregate pass count | Selected local test-app execution stability only |
| High | Safe real direct/agent CLI gates | Keep direct/agent real MOOSE lanes skipped until workspace isolation, command construction, and proposal preflight are explicit | skip artifacts explain missing real-lane contract and do not fail default CI | Truthful unsupported-state evidence only |
| High | Proposal repair rate tracking | Preserve malformed proposal contract, direct failure, agent repair, `repair_count`, and `repair_advantage` in comparison bundles | dry-run bundle shows `agent_repaired_direct_failure` for malformed input | Workflow repair evidence only, not solver evidence |
| Medium | Solver log metrics | Parse stdout/stderr for convergence, residual, nonlinear/linear iteration, or MOOSE-reported diagnostics when available | validation/evidence bundle contains domain-labeled metrics and missing-metric reasons | Domain metric evidence only after reviewer signoff |
| Later | Broader input families | Add source-truth anchored MOOSE tutorial/test inputs one at a time | each case names source refs, expected outputs, real-tool gate, and non-claims | No broad MOOSE app coverage from one test-app case |
