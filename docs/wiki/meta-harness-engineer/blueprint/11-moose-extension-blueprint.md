# MOOSE Extension Blueprint

## Scope

- Anchor the extension to the FEM source tree at `/home/linden/code/work/Solvers/FEM/moose`.
- Model the runtime flow around `moose-opt -i <input.i>` and the HIT input format.
- Treat the local docs in `/home/linden/code/work/Solvers/FEM/docs/moose-docs` as reference material, not as the runtime source of truth.

## Source Truth

- The source tree exposes the Idaho MOOSE finite-element framework.
- The local docs tree is a separate MOOSE manual export with mixed historical content.
- The extension should follow executable and input behavior visible in the source tree and tutorials.

## First Slice

- Environment probe for `moose-opt` and writable workspaces.
- Input compiler that materializes `.i` files and builds a run command.
- Executor that runs `moose-opt -i input.i` in an isolated workspace.
- Validator that checks exit status and declared output files.
- Evidence and policy adapters that bundle run artifacts and decide allow/reject/defer.

## Non-Goals

- No mesh-generation semantics beyond the minimal `--mesh-only` pathway.
- No attempt to model the full MOOSE module catalog.
- No GUI, app-construction, or PETSc/libMesh build orchestration.

## Truth Boundaries

- Do not claim support for every MOOSE application or module.
- Do not claim source-tree discovery is required for successful runs unless the user configures it.
- Do not imply the extension can validate physics correctness without a declared output contract.

## Validation Targets

- Manifest loading and component declaration.
- Mocked probe/compile/execute/validate flow.
- Optional smoke test gated behind a real `moose-opt` binary.

## Next Slice Candidates

- Add richer output parsing for Exodus metadata.
- Add module-aware input templating for common MOOSE problem families.
- Add a study helper that sweeps parameter tokens in input templates.
