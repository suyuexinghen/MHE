# MOOSE Extension Implementation Plan

## Build Steps

- Create the `metaharness_ext.moose` package with exported capabilities, slots, and contracts.
- Add package-level and example manifests for gateway, environment, compiler, executor, validator, and study components.
- Add focused tests for manifests, environment probing, compilation, execution, validation, evidence, and policy behavior.

## Verification Steps

- Run targeted `pytest` files for the new extension.
- Run `ruff check` on the touched source and test files.
- Run the optional smoke test only if `moose-opt` is present and the relevant environment flag is set.

## Completion Criteria

- Imports resolve from `metaharness_ext.moose`.
- Manifests match the declared interfaces.
- Mocked tests pass without requiring a real solver installation.
- The docs describe the first slice without overstating runtime support.
