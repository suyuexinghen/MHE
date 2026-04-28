# QCompute × ABACUS Hamiltonian Proxy Benchmark Method

> 版本：v0.1 | 最后更新：2026-04-28

## 1. Purpose

This benchmark records a narrow, evidence-first method for using MHE to route an ABACUS-adjacent Hamiltonian task through the QCompute extension. The suite name is `qcompute-abacus`.

The benchmark is intentionally a Hamiltonian proxy benchmark: ABACUS input files provide scientific provenance, while QCompute consumes an FCIDUMP Hamiltonian fixture and runs the compile / execute / validate / evidence path.

## 2. Scope and non-claims

This benchmark does cover:

- H2 FCIDUMP parsing and active-space metadata.
- Fermion-to-qubit mapping through Jordan-Wigner and Bravyi-Kitaev paths.
- VQE-style deterministic-grid parameter selection in QCompute.
- Qiskit Aer simulator execution when real tools are enabled and available.
- QCompute validation, energy-error reporting, and evidence bundle creation.
- Explicit provenance references back to ABACUS H2 source inputs.

This benchmark does not claim:

- QCompute solves general ABACUS DFT, SCF, band, DOS, phonon, work-function, or vacancy cases.
- ABACUS currently exports FCIDUMP through the MHE ABACUS extension.
- ABACUS H/S matrix outputs are currently converted into FCIDUMP or qubit Hamiltonians.
- The VQE proxy is a production quantum-chemistry workflow or quantum-advantage result.

The missing ABACUS H/S bridge is represented by a skipped sentinel case rather than a fake pass.

## 3. Suite and cases

Suite:

```text
qcompute-abacus
```

Output root:

```text
.runs/qcompute-abacus-benchmark/
```

### 3.1 `h2-fcidump-vqe-proxy`

Positive proxy case.

Inputs:

- ABACUS H2 source references from `ABACUS-agent-tools/tests/integrate_test/abacus_inputs_dirs/H2` and upstream ABACUS H2 regression inputs.
- Embedded H2 STO-3G-style FCIDUMP fixture materialized as `hamiltonian.fcidump` in the lane output directory.

QCompute settings:

- backend: `qiskit_aer`
- simulator: `true`
- ansatz: `vqe`
- qubits: `2`
- shots: `256`
- active space: `(2, 2)`
- mapping: `jordan_wigner`
- reference energy: `-1.137`
- max iterations: `5`

Expected metrics:

- `energy`
- `energy_error`
- `convergence_iterations`
- `num_qubits`
- `term_count`
- `shots_completed`
- `elapsed_seconds`

### 3.2 `h2-fcidump-jw-vs-bk`

Mapping comparison case.

The same H2 FCIDUMP fixture is mapped with:

- Jordan-Wigner
- Bravyi-Kitaev

This case compares metadata shape, not ABACUS physics:

- qubit count
- Pauli term count
- mapping metadata

Expected metrics:

- `jw_num_qubits`
- `jw_term_count`
- `bk_num_qubits`
- `bk_term_count`
- `elapsed_seconds`

### 3.3 `abacus-hs-bridge-pending`

Unsupported bridge sentinel.

Source references point at ABACUS examples/tests that request H/S matrix output, including `out_mat_hs` and `out_mat_hs2` families. The expected status is skipped because MHE does not yet implement an ABACUS H/S-to-FCIDUMP or H/S-to-qubit-Hamiltonian converter.

The lane summary uses:

```text
status = skipped
skip_reason = unsupported_source_format: ABACUS H/S-to-FCIDUMP bridge is not implemented
```

## 4. Lanes

The suite keeps the same lane vocabulary as the existing benchmark framework.

### 4.1 `extension`

The deterministic MHE extension baseline.

Dry run:

- writes lane summaries and evidence metadata without importing Qiskit or running ABACUS.

Real mode with `--allow-real-tools`:

1. write `hamiltonian.fcidump`
2. build `QComputeExperimentSpec`
3. probe `QComputeEnvironmentProbeComponent`
4. compile with `QComputeConfigCompilerComponent.build_plan_from_hamiltonian()`
5. execute with `QComputeExecutorComponent.execute_plan()`
6. validate with `QComputeValidatorComponent.validate_run()`
7. build `QComputeEvidenceBundle`

If Qiskit or Qiskit Aer is unavailable, the lane is skipped instead of failing the benchmark.

### 4.2 `direct`

The direct Claude CLI baseline.

Dry run uses the configured brain provider and writes Claude evidence files, but it does not call MHE QCompute extension components. This preserves the boundary between direct proposal and extension-mediated execution.

### 4.3 `agent`

The MHE agent lane.

Dry run writes Claude proposal evidence. Real mode uses the proposal evidence and then sends the task through the QCompute extension pipeline, mirroring the existing benchmark convention that the agent lane combines LLM proposal with extension validation/evidence.

## 5. Artifacts

Each lane writes a valid generic `LaneSummary` plus lane-specific evidence under:

```text
.runs/qcompute-abacus-benchmark/<lane>/<case_id>/
```

Common files:

```text
case_spec.json
metrics.json
attempt_log.json
summary.json
```

QCompute extension/agent files for positive cases:

```text
hamiltonian.fcidump
qcompute_spec.json
environment.json
run_plan.json
run_artifact.json
validation.json
evidence.json
```

Claude lane files:

```text
claude_prompt.txt
claude_command.json
claude_stdout.json
claude_stderr.txt
claude_result.json
proposal.json
```

Unsupported bridge evidence:

```text
source_refs.json
```

Comparison outputs reuse the generic benchmark comparator:

```text
.runs/qcompute-abacus-benchmark/comparison/summary_table.csv
.runs/qcompute-abacus-benchmark/comparison/result_bundle.json
.runs/qcompute-abacus-benchmark/comparison/run_manifest.json
.runs/qcompute-abacus-benchmark/comparison/comparison_report.md
.runs/qcompute-abacus-benchmark/reports/qcompute-abacus-analysis-report.md
.runs/qcompute-abacus-benchmark/reports/qcompute-abacus-backlog.md
```

## 6. Commands

Dry-run all cases and lanes:

```bash
PYTHONPATH=src python -m metaharness.cli benchmark-run \
  --suite qcompute-abacus \
  --lanes extension,direct,agent \
  --runs-root .runs
```

Dry-run a focused H2 case:

```bash
PYTHONPATH=src python -m metaharness.cli benchmark-run \
  --suite qcompute-abacus \
  --lanes extension,direct,agent \
  --cases h2-fcidump-vqe-proxy \
  --runs-root .runs
```

Real extension run, dependency-gated:

```bash
PYTHONPATH=src python -m metaharness.cli benchmark-run \
  --suite qcompute-abacus \
  --lanes extension \
  --cases h2-fcidump-vqe-proxy \
  --runs-root .runs \
  --allow-real-tools
```

Compare outputs:

```bash
PYTHONPATH=src python -m metaharness.cli benchmark-compare \
  --suite qcompute-abacus \
  --runs-root .runs
```

## 7. Acceptance checklist

A result is acceptable only when:

- all lane summaries validate against the generic `LaneSummary` schema;
- positive proxy cases include Hamiltonian metadata and QCompute evidence files;
- `energy_error` is derived from QCompute validation when a real run executes;
- dry-run outputs never claim real numerical execution;
- the H/S bridge sentinel remains skipped until a converter is implemented;
- generated artifacts stay under `.runs/` or an explicit `--runs-root`.

## 8. Future bridge work

The natural next implementation is an ABACUS H/S matrix bridge:

1. parse ABACUS `out_mat_hs` / `out_mat_hs2` text or CSR outputs;
2. capture basis and k-point metadata;
3. define a supported conversion target, either FCIDUMP or a QCompute `pauli_dict`;
4. validate the converted Hamiltonian against an ABACUS reference and a QCompute parser;
5. promote `abacus-hs-bridge-pending` from skipped sentinel to executable bridge case.
