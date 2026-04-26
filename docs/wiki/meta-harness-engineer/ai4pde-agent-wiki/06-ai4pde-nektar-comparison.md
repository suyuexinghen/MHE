# AI4PDE and Nektar Extension Comparison Manual

This manual explains how to run the `AI4PDE` extension and the `Nektar` extension in `MHE` on the same numerical PDE problem, compare their outputs, and interpret the results honestly.

## 1. Overview and Current-State Disclaimer

`MHE` currently contains two different domain extensions with different maturity levels:

- `metaharness_ext.ai4pde` provides a runnable PDE-agent workflow through the public CLI in `src/metaharness/cli.py`.
- `metaharness_ext.nektar` provides a real Nektar++ execution pipeline in `src/metaharness_ext/nektar/`, but it does not yet have a dedicated public CLI subcommand.

This matters for comparison:

- `AI4PDE` is currently strongest as an **orchestration / planning / validation / evidence** flow.
- `Nektar` is currently strongest as a **real numerical execution / postprocess / validator** flow.

The comparison described here is therefore a **methodological comparison on the same PDE problem definition**, not a claim that both extensions are already solving the PDE through the exact same execution engine.

### 1.1 The key asymmetry

Today, `AI4PDE` can record a Nektar-oriented backend choice in its plan and run artifact, but its `classical_hybrid` execution path is still synthetic:

- `src/metaharness_ext/ai4pde/executors/classical_hybrid.py` returns a stub `PDERunArtifact`
- `src/metaharness_ext/ai4pde/components/reference_solver.py` returns a synthetic/config-driven baseline

By contrast, the `Nektar` extension can invoke real binaries and parse real outputs:

- `src/metaharness_ext/nektar/session_compiler.py`
- `src/metaharness_ext/nektar/solver_executor.py`
- `src/metaharness_ext/nektar/postprocess.py`
- `src/metaharness_ext/nektar/validator.py`

## 2. Recommended Benchmark Problem

For a same-problem comparison, use a **simple scalar PDE** as the primary benchmark.

Recommended first benchmark:

- a Helmholtz / Laplace / ADR-style scalar PDE
- reason: the Nektar extension has real ADR support today through `ADRSolver`
- reason: the AI4PDE extension already has simple Laplace-like demo paths in its gateway/tests

You can also inspect the richer AI4PDE case file:

- `docs/xml-demo/cylinder-flow-re100.xml`

However, the cylinder-flow case is currently better for demonstrating:

- AI4PDE case parsing
- AI4PDE graph/template selection
- Nektar-oriented metadata propagation

It is not yet the best strict apples-to-apples comparison case, because AI4PDE does not yet execute the real Nektar extension behind `classical_hybrid`.

## 3. Prerequisites and Environment

## 3.1 Python environment

From `MHE/`:

```bash
python -m pip install -e .
```

Or run without installation:

```bash
PYTHONPATH=src python -m metaharness.cli version
```

## 3.2 Nektar prerequisites

The Nektar extension requires real solver binaries on `PATH` for execution:

- `ADRSolver`
- `IncNavierStokesSolver`
- `FieldConvert`

The real Nektar pipeline may also depend on local mesh/session/example assets when using e2e test paths.

## 3.3 What is publicly runnable today

Public CLI commands in `src/metaharness/cli.py`:

- `metaharness demo`
- `metaharness validate`
- `metaharness ai4pde-case`
- `metaharness validate-case`
- `metaharness version`

There is **no dedicated `metaharness nektar ...` subcommand yet**.

## 4. Running AI4PDE on a PDE Case

## 4.1 Validate the case file

Example:

```bash
PYTHONPATH=src python -m metaharness.cli validate-case docs/xml-demo/cylinder-flow-re100.xml
```

This parses the AI4PDE case XML and emits a JSON summary containing:

- `status`
- `case`
- `task_id`
- `plan_id`
- `selected_method`
- `graph_family`

Implementation reference:

- `src/metaharness/cli.py:90`

## 4.2 Run the AI4PDE case flow

```bash
PYTHONPATH=src python -m metaharness.cli ai4pde-case docs/xml-demo/cylinder-flow-re100.xml
```

Equivalent direct demo entrypoint:

```bash
PYTHONPATH=src python -m metaharness_ext.ai4pde.demo docs/xml-demo/cylinder-flow-re100.xml
```

Implementation references:

- `src/metaharness/cli.py:83`
- `src/metaharness_ext/ai4pde/demo.py:105`

## 4.3 What AI4PDE returns

`AI4PDECaseDemoHarness.run_case()` returns a structured JSON payload with:

- `case_path`
- `graph_version`
- `task`
- `plan`
- `run_artifact`
- `validation_bundle`
- `evidence_bundle`
- `reference_result`
- `memory_record`

Implementation reference:

- `src/metaharness_ext/ai4pde/demo.py:56`

## 4.4 Comparison-relevant AI4PDE fields

When comparing to Nektar, focus on:

- `plan.selected_method`
- `plan.graph_family`
- `run_artifact.solver_family`
- `run_artifact.result_summary.residual_l2`
- `run_artifact.result_summary.boundary_error`
- `run_artifact.result_summary.backend`
- `run_artifact.result_summary.nektar_solver`
- `validation_bundle.residual_metrics`
- `validation_bundle.bc_ic_metrics`
- `validation_bundle.reference_comparison`

### Important limitation

Even if `run_artifact.result_summary.backend == "nektar++"`, this does **not** mean AI4PDE invoked the real Nektar extension today.

That metadata is currently emitted by the synthetic executor in:

- `src/metaharness_ext/ai4pde/executors/classical_hybrid.py:7`

## 5. Running the Nektar Extension on the Corresponding Problem

## 5.1 Real Nektar workflow

The actual Nektar execution chain is:

```text
NektarProblemSpec
  -> SessionCompilerComponent.build_plan()
  -> write_session_xml()
  -> SolverExecutorComponent.execute_plan()
  -> PostprocessComponent.process()
  -> NektarValidatorComponent.validate()
```

Relevant files:

- `src/metaharness_ext/nektar/session_compiler.py`
- `src/metaharness_ext/nektar/xml_renderer.py`
- `src/metaharness_ext/nektar/solver_executor.py`
- `src/metaharness_ext/nektar/postprocess.py`
- `src/metaharness_ext/nektar/validator.py`

## 5.2 Programmatic usage pattern

Use the exported APIs from `src/metaharness_ext/nektar/__init__.py`.

Typical flow:

```python
from metaharness_ext.nektar import (
    NektarGatewayComponent,
    SessionCompilerComponent,
    SolverExecutorComponent,
    PostprocessComponent,
    NektarValidatorComponent,
)

# 1. Build or issue a problem spec
# 2. Compile to a NektarSessionPlan
# 3. Execute the solver
# 4. Postprocess outputs
# 5. Validate the run
```

## 5.3 Recommended first real run: ADR / Helmholtz

Use ADR first because it is the simplest real family supported today.

`SessionCompilerComponent.build_plan()` currently maps:

- `NektarSolverFamily.ADR` -> `ADRSolver`
- `NektarSolverFamily.INCNS` -> `IncNavierStokesSolver`

Implementation reference:

- `src/metaharness_ext/nektar/session_compiler.py:223`

## 5.4 Real command shape used by the executor

The executor builds real subprocess commands of the form:

### Inline-geometry ADR

```bash
ADRSolver session.xml
```

### External-mesh IncNS overlay

```bash
IncNavierStokesSolver mesh.xml session.xml
```

Implementation reference:

- `src/metaharness_ext/nektar/solver_executor.py:231`

## 5.5 Postprocess command shapes

Examples already supported by the postprocess layer:

```bash
FieldConvert input.fld output.vtu
FieldConvert -e session.xml input.fld error.vtu
FieldConvert -m vorticity input.fld vorticity.fld
FieldConvert -m extract:bnd=0 input.fld boundary_b0.dat
```

Implementation reference:

- `src/metaharness_ext/nektar/postprocess.py`

## 6. Collecting Artifacts and Metrics

## 6.1 AI4PDE artifacts

AI4PDE currently emits structured JSON-level artifacts such as:

- artifact refs
- checkpoint refs
- telemetry refs
- validation bundle
- evidence bundle
- reference comparison summary

These are orchestration/evidence-layer outputs.

## 6.2 Nektar artifacts

Nektar emits concrete run artifacts:

- session files
- mesh files
- `.fld` field files
- `.chk` checkpoint files
- solver logs
- derived postprocess outputs such as `.vtu` and `.dat`
- extracted `error_norms`
- execution metrics such as `total_steps`, `final_time`, `cpu_time`, `wall_time`

Implementation references:

- `src/metaharness_ext/nektar/contracts.py`
- `src/metaharness_ext/nektar/solver_executor.py:288`
- `src/metaharness_ext/nektar/postprocess.py`

## 6.3 Minimum comparison table

For each run, record:

| Field | AI4PDE | Nektar |
|---|---|---|
| PDE definition | From case/task/plan | From `NektarProblemSpec` / session plan |
| Boundary conditions | From case/task | From session plan / XML |
| Solver family | `run_artifact.solver_family` | `plan.solver_family` |
| Backend intent | `result_summary.backend` | real binary selected |
| Execution surface | demo/stub | real executable |
| Main outputs | JSON artifacts and evidence | field/checkpoint/log/postprocess files |
| Residual / error metrics | validation bundle + stub summary | parsed error norms + validator report |
| Validation outcome | validation bundle | validator report |
| Caveat | synthetic executor | real solver path |

## 7. Comparing Results Responsibly

Compare in this order:

1. **Problem statement equivalence**
   - same PDE
   - same geometry/domain assumptions
   - same boundary and initial conditions

2. **Method / backend intent**
   - AI4PDE selected method and graph family
   - Nektar selected solver family, projection, and binary

3. **Artifacts produced**
   - AI4PDE: JSON evidence and references
   - Nektar: concrete files and postprocess outputs

4. **Metrics and validation**
   - residuals
   - boundary consistency
   - reference error, if available
   - convergence or runtime metrics

### 7.1 What is comparable today

Comparable today:

- PDE/task description
- selected method/backend intent
- validation envelopes and thresholds
- residual/error summary fields
- evidence structure and artifact completeness

Not fully comparable today:

- final numerical solution fidelity between AI4PDE `classical_hybrid` and real Nektar
- strict field-by-field equivalence
- strict runtime performance comparison

## 8. Interpretation Limits

This section is critical.

### 8.1 AI4PDE limitations

- `AI4PDE` `classical_hybrid` is currently synthetic/stubbed.
- `AI4PDE` reference baseline is synthetic/config-driven.
- Therefore, AI4PDE numeric outputs should be interpreted as **workflow/demo summaries**, not proof of real classical solver execution.

Relevant files:

- `src/metaharness_ext/ai4pde/executors/classical_hybrid.py`
- `src/metaharness_ext/ai4pde/components/reference_solver.py`

### 8.2 Nektar limitations

- No dedicated Nektar CLI subcommand exists yet.
- Real supported families are currently ADR and IncNS.
- Some e2e cases depend on external Nektar assets or installed binaries.
- Some geometry/session features remain intentionally constrained.

### 8.3 Practical interpretation

The current comparison is best understood as:

- **AI4PDE**: planning, graph selection, validation, evidence, and PDE-agent workflow
- **Nektar**: real classical PDE execution, postprocess, and validation workflow

It is **not yet** a strict same-engine benchmark.

## 9. Suggested Next Engineering Steps

To make this comparison truly apples-to-apples in the future, the next high-value steps are:

1. Add a dedicated Nektar CLI subcommand, such as `metaharness nektar-run ...`
2. Bridge `AI4PDE` `classical_hybrid` into the real Nektar execution chain
3. Standardize a shared scalar benchmark case for both extensions
4. Standardize a shared result schema for:
   - residuals
   - reference error
   - generated artifacts
   - execution metrics
5. Add a one-command run-and-compare workflow

## 10. Reference Files

Core entrypoints:

- `src/metaharness/cli.py`
- `src/metaharness_ext/ai4pde/demo.py`
- `src/metaharness_ext/nektar/__init__.py`

AI4PDE implementation references:

- `src/metaharness_ext/ai4pde/case_parser.py`
- `src/metaharness_ext/ai4pde/executors/classical_hybrid.py`
- `src/metaharness_ext/ai4pde/components/reference_solver.py`

Nektar implementation references:

- `src/metaharness_ext/nektar/session_compiler.py`
- `src/metaharness_ext/nektar/xml_renderer.py`
- `src/metaharness_ext/nektar/solver_executor.py`
- `src/metaharness_ext/nektar/postprocess.py`
- `src/metaharness_ext/nektar/validator.py`

Example case:

- `docs/xml-demo/cylinder-flow-re100.xml`
