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
