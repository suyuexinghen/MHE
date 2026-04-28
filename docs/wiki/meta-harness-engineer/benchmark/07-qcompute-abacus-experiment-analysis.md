# 07. QCompute × ABACUS Hamiltonian Proxy 实验分析报告

> 版本：v0.1 | 生成依据：`.runs/benchmark-wiki/qcompute-abacus-benchmark/` | 日期：2026-04-28

## 7.1 实验范围

本报告对应 `qcompute-abacus` suite，用于验证 ABACUS-adjacent Hamiltonian proxy benchmark 在三条 workflow lane 下的 driver、evidence、comparison bundle 和 non-claims 表达。

本轮是安全 dry-run / mocked benchmark，不声明真实 ABACUS DFT、ABACUS H/S matrix bridge、真实 QPU 或 quantum advantage 结论。它验证的是：H2 FCIDUMP proxy case、JW/BK mapping comparison case、unsupported ABACUS H/S bridge sentinel、Claude CLI evidence、QCompute evidence layout 和 generic comparator 支持。

## 7.2 数据来源

- 运行根目录：`.runs/benchmark-wiki`
- Suite 目录：`.runs/benchmark-wiki/qcompute-abacus-benchmark/`
- Case specs：`.runs/benchmark-wiki/qcompute-abacus-benchmark/specs/*.json`
- Lane summaries：`.runs/benchmark-wiki/qcompute-abacus-benchmark/{extension,direct,agent}/*/summary.json`
- Comparison bundle：`.runs/benchmark-wiki/qcompute-abacus-benchmark/comparison/result_bundle.json`
- Manifest：`.runs/benchmark-wiki/qcompute-abacus-benchmark/comparison/run_manifest.json`
- Generated report：`.runs/benchmark-wiki/qcompute-abacus-benchmark/reports/qcompute-abacus-analysis-report.md`

## 7.3 Case 覆盖

| Case | Extension | Direct | Agent | Verdict |
|---|---|---|---|---|
| `h2-fcidump-vqe-proxy` | passed | passed | passed | all_passed |
| `h2-fcidump-jw-vs-bk` | passed | passed | passed | all_passed |
| `abacus-hs-bridge-pending` | skipped | skipped | skipped | capability_skip |

Observed summary:

- Cases compared: 3
- Fully passed dry-run cases: 2
- Capability skips: 1
- Schema failures observed by comparator: 0
- Direct Claude CLI calls recorded: 3
- Agent Claude CLI calls recorded: 3

## 7.4 Workflow lane observations

### Extension baseline

The extension lane writes deterministic dry-run QCompute evidence for positive Hamiltonian proxy cases, including `hamiltonian.fcidump`, `validation.json`, and `evidence.json`. The unsupported ABACUS H/S bridge case writes `source_refs.json` and remains skipped.

### Direct Claude CLI lane

The direct lane records a Claude proposal and dry-run boundary evidence. It does not call MHE QCompute extension components in dry-run mode, preserving the direct baseline boundary.

### MHE Claude CLI agent lane

The agent lane records a Claude proposal and agent-lane evidence. Real mode is designed to combine proposal evidence with QCompute extension execution when dependencies are available and `--allow-real-tools` is used.

## 7.5 Non-claims

This benchmark does not claim:

- ABACUS currently exports FCIDUMP through MHE.
- ABACUS H/S matrix outputs are currently converted to FCIDUMP or qubit Hamiltonians.
- QCompute solves general ABACUS DFT, SCF, band, DOS, phonon, work-function, or vacancy workflows.
- The H2 proxy is a production quantum chemistry benchmark.
- Dry-run energy metrics are real Qiskit Aer or quantum hardware results.

## 7.6 Acceptance status

| Requirement | Status | Notes |
|---|---|---|
| Suite is available via CLI | Complete | `--suite qcompute-abacus` works for run and compare. |
| Positive H2 proxy case | Complete for dry-run | FCIDUMP fixture and metrics are emitted. |
| JW/BK mapping comparison case | Complete for dry-run | Mapping-shape metrics are emitted. |
| H/S bridge sentinel | Complete | Unsupported source format is skipped, not faked. |
| Generic comparator support | Complete | CSV, Markdown, JSON bundle and manifest are generated. |
| Real QCompute execution | Dependency-gated | Requires Qiskit/Qiskit Aer and `--allow-real-tools`. |
| Real ABACUS H/S bridge | Pending | Requires converter implementation. |

## 7.7 Backlog

1. Add an ABACUS H/S matrix parser for `out_mat_hs` / `out_mat_hs2` outputs.
2. Define a supported conversion target: FCIDUMP or direct QCompute Pauli dictionary.
3. Validate converted Hamiltonians against ABACUS provenance and QCompute parser expectations.
4. Promote `abacus-hs-bridge-pending` from skipped sentinel to executable bridge case only after converter tests pass.
5. Add real-mode smoke coverage when Qiskit and Qiskit Aer are available.
