# 07. QCompute × ABACUS Hamiltonian Proxy 实验分析报告

> 版本：v0.2 | 生成依据：`.runs/benchmark-wiki/qcompute-abacus-benchmark/` | 日期：2026-04-28

## 7.1 实验范围

本报告对应 `qcompute-abacus` suite，用于验证 MHE benchmark driver 能否把 ABACUS-adjacent Hamiltonian proxy 任务组织成可复查的三 lane benchmark：

1. `extension`：无 LLM 的 MHE/QCompute extension baseline；
2. `direct`：direct Claude CLI proposal baseline；
3. `agent`：Claude proposal + MHE extension-shaped pipeline lane。

本轮运行是 dry-run benchmark，没有使用 `--allow-real-tools`。因此，本报告只分析 benchmark driver、case catalog、summary schema、evidence layout、comparison bundle、manifest 记录和 unsupported bridge 表达；不声明真实 ABACUS DFT、真实 ABACUS H/S matrix conversion、真实 QPU、quantum advantage，或正式 quantum chemistry 数值结论。

## 7.2 数据来源

- 运行根目录：`.runs/benchmark-wiki`
- Suite 目录：`.runs/benchmark-wiki/qcompute-abacus-benchmark/`
- Case specs：`.runs/benchmark-wiki/qcompute-abacus-benchmark/specs/*.json`
- Lane summaries：`.runs/benchmark-wiki/qcompute-abacus-benchmark/{extension,direct,agent}/*/summary.json`
- Comparison bundle：`.runs/benchmark-wiki/qcompute-abacus-benchmark/comparison/result_bundle.json`
- Manifest：`.runs/benchmark-wiki/qcompute-abacus-benchmark/comparison/run_manifest.json`
- Generated report：`.runs/benchmark-wiki/qcompute-abacus-benchmark/reports/qcompute-abacus-analysis-report.md`

Manifest 记录的环境信息包括：

| Item | Observed value |
|---|---|
| Python | `3.13.11` |
| Claude Code | `2.1.114 (Claude Code)` |
| Git revision | `810499d` |
| `qiskit` | available |
| `qiskit_aer` | available |
| `pennylane` | available |
| `abacus` binary | not found / `null` |

这些信息只说明本地环境探测状态。由于本轮未开启 `--allow-real-tools`，即使 `qiskit` 与 `qiskit_aer` 可见，本报告中的 lane metrics 仍是 dry-run wiring metrics，不是 simulator 实测结果。若 real mode 下 `qiskit` 或 `qiskit_aer` 不可用，应报告为 dependency skip；若依赖可用但执行或 validation 失败，才可归类为 QCompute numerical/execution failure。QPU 可用性也必须单独报告，不能由本地 simulator dependency 推断。

## 7.3 Case 覆盖与 comparator verdict

本轮共覆盖 3 个 cases，每个 case 均进入 `extension`、`direct`、`agent` 三条 lane。

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
- Direct repairs recorded: 0
- Agent repairs recorded: 0

## 7.4 Case-level observations

### 7.4.1 `h2-fcidump-vqe-proxy`

该 case 是正向 proxy case。它以 ABACUS H2 input refs 作为 provenance anchor，并在 lane output 目录中 materialize 一个 H2 STO-3G-style `hamiltonian.fcidump` fixture。

Dry-run summary 显示：

- `extension` lane：`passed`，evidence count = 3；
- `direct` lane：`passed`，evidence count = 6；
- `agent` lane：`passed`，evidence count = 6；
- expected metrics 均存在；
- `convergence_iterations = 5.0`；
- `num_qubits = 2.0`；
- `energy_error = 0.0` 是 reference echo，用于验证 comparator/tolerance wiring。

需要强调：这里的 `energy`、`energy_error`、`shots_completed` 是 dry-run 指标，不是 Qiskit Aer 执行后的物理或数值结论。正式数值分析必须使用：

```bash
PYTHONPATH=src python -m metaharness.cli benchmark-run \
  --suite qcompute-abacus \
  --lanes extension,agent \
  --cases h2-fcidump-vqe-proxy \
  --runs-root .runs/benchmark-real \
  --allow-real-tools
```

并复查 `run_plan.json`、`run_artifact.json`、`validation.json` 和 `evidence.json`。

### 7.4.2 `h2-fcidump-jw-vs-bk`

该 case 验证同一 H2 FCIDUMP fixture 的 mapping comparison 产物结构。它不是 ABACUS 物理正确性比较，而是 benchmark driver 能否表达 QCompute Hamiltonian metadata comparison。

Dry-run summary 显示：

- `extension` lane：`passed`，evidence count = 3；
- `direct` lane：`passed`，evidence count = 6；
- `agent` lane：`passed`，evidence count = 6；
- `jw_num_qubits = 2.0`；
- `bk_num_qubits = 2.0`；
- `jw_term_count` / `bk_term_count` 在 dry-run 中为 wiring placeholder。

正式 mapping 分析应读取 real-mode 的 `mapping_metadata.json` 或 `run_plan.json` 中的 Hamiltonian metadata，而不是引用 dry-run term counts。

### 7.4.3 `abacus-hs-bridge-pending`

该 case 是 unsupported bridge sentinel，用于防止报告误称 ABACUS H/S matrix 已可进入 QCompute。

Comparator 结果：

- `extension` lane：`skipped`，evidence count = 1；
- `direct` lane：`skipped`，evidence count = 6；
- `agent` lane：`skipped`，evidence count = 6；
- verdict：`capability_skip`。

三条 lane 的 skip reason 均为：

```text
unsupported_source_format: ABACUS H/S-to-FCIDUMP bridge is not implemented
```

这是本轮最重要的 truthfulness guardrail：ABACUS `out_mat_hs` / `out_mat_hs2` source refs 已被记录，但不会被伪装成已支持的 FCIDUMP 或 qubit Hamiltonian input。

后续实现已补充 `bridge_status.json`：runner 会从可读 ABACUS `INPUT` refs 中提取 `basis_type`、`gamma_only`、`ks_solver`、`out_mat_hs` / `out_mat_hs2` 等 metadata，用于证明 source format 被识别；同时写入 `conversion_plan`，定义 accepted artifacts、目标表示和 validation requirements。当前只有 toy `ABACUS_HS_TOY` fixture conversion 用于测试 FCIDUMP contract；真实 ABACUS H/S matrix 到 FCIDUMP 或 QCompute Pauli dictionary 的 converter 仍未实现，因此 `promotion_ready` 仍为 `false`。

Reviewer 复查 `bridge_status.json` 时应优先确认这些字段：

```json
{
  "status": "converter_missing",
  "promotion_ready": false,
  "missing_capabilities": ["abacus_hs_to_fcidump_converter"],
  "failure_code": "converter_missing",
  "matrix_metadata": [
    {
      "format_family": "abacus_sparse_csr",
      "matrix_role": "H",
      "parse_status": "metadata_only",
      "conversion_status": "unsupported"
    }
  ],
  "conversion_plan": {
    "status": "metadata_only",
    "target_format": "qcompute_pauli_dict"
  },
  "parsed_metadata": {
    "input_refs": [
      {
        "parameters": {"basis_type": ["lcao"], "out_mat_hs2": ["1"]},
        "hs_output_keys": ["out_mat_hs2"]
      }
    ]
  }
}
```

`source_refs.json` 同步嵌入 `bridge_status`，因此 reviewer 可以从同一个 lane output 目录同时追踪 source provenance 和 skip rationale。以上字段说明 bridge 已具备 metadata-aware unsupported path，但并不构成真实 H/S conversion 或 scientific validation。

## 7.5 Workflow lane observations

### Extension baseline

`extension` lane 对正向 proxy cases 写入 deterministic dry-run evidence：

- `validation.json`
- `evidence.json`
- `hamiltonian.fcidump`

对 H/S bridge sentinel，只写入 `source_refs.json` 并返回 `skipped`。这说明 driver 已经具备区分“可执行 proxy case”和“未实现 bridge case”的能力。

### Direct Claude CLI lane

`direct` lane 每个 case 记录一次 Claude proposal attempt，并写入：

- `claude_prompt.txt`
- `claude_command.json`
- `claude_stdout.json`
- `claude_stderr.txt`
- `claude_result.json`
- `proposal.json`

在 dry-run 模式下，direct lane 不调用 MHE QCompute extension components。这保持了 direct baseline 与 extension-mediated workflow 的边界。

### MHE Claude CLI agent lane

`agent` lane 每个 case 也记录一次 Claude proposal attempt。对 positive proxy cases，dry-run 写入 agent-lane evidence；在 real mode 设计中，该 lane 应在 proposal 之后进入 QCompute extension pipeline，以获得 `run_plan.json`、`run_artifact.json`、`validation.json` 和 `evidence.json`。

## 7.6 Numeric interpretation

本轮不能解读为真实 quantum simulation 或 ABACUS/QCompute 数值结果，原因如下：

1. 未使用 `--allow-real-tools`；
2. positive case 的 metrics 是 dry-run reference echoes；
3. `shots_completed = 0.0` 表明未执行 simulator shots；
4. `energy_error = 0.0` 只验证 tolerance wiring，不是 VQE 收敛结论；
5. ABACUS binary 在 manifest 中为 `null`，本轮没有 ABACUS 运行；
6. H/S bridge sentinel 被正确 skipped。

正式数值报告至少需要补充：

- real-mode `extension` lane 的 Qiskit Aer execution status；
- `run_artifact.json` 中的 `counts`、`probabilities`、`shots_completed`；
- `validation.json` 中的 `metrics.energy`、`metrics.energy_error`、`promotion_ready`；
- `evidence.json` 中的 provenance refs；
- 多次重复运行的 timing / flaky 标记。

## 7.7 Evidence completeness

当前 dry-run 的 evidence 完整性满足 benchmark framework 级别复查：

| Case | Extension evidence count | Direct evidence count | Agent evidence count |
|---|---:|---:|---:|
| `h2-fcidump-vqe-proxy` | 3 | 6 | 6 |
| `h2-fcidump-jw-vs-bk` | 3 | 6 | 6 |
| `abacus-hs-bridge-pending` | 1 | 6 | 6 |

独立 reviewer 可从产物重建：

1. case spec；
2. lane summary；
3. direct/agent prompt 与 fake Claude result；
4. positive proxy cases 的 FCIDUMP fixture；
5. H/S bridge sentinel 的 source refs 与 skip reason；
6. comparator verdict 与 manifest 环境记录。

## 7.8 Acceptance status

| Requirement | Status | Notes |
|---|---|---|
| `qcompute-abacus` CLI suite | Complete | `benchmark-run` 和 `benchmark-compare` 均可执行。 |
| Three cases catalogued | Complete | H2 VQE proxy、JW/BK comparison、H/S bridge sentinel 均进入 suite。 |
| Three lanes per case | Complete for dry-run | `extension`、`direct`、`agent` summaries 均生成。 |
| Generic comparator support | Complete | `summary_table.csv`、`result_bundle.json`、`run_manifest.json`、report/backlog 均生成。 |
| Schema failures | None observed | Comparator 未发现 schema failure。 |
| H/S bridge truthfulness | Complete | Sentinel case 为 `capability_skip`，未伪造支持。 |
| H/S bridge metadata parser | Implemented scaffold | `bridge_status.json` 解析可读 ABACUS `INPUT` refs 与 H/S output flags，但不做矩阵转换。 |
| Real QCompute execution | Pending formal report | 本地 `qiskit` / `qiskit_aer` 可见，但本轮未启用 `--allow-real-tools`。 |
| Real ABACUS H/S bridge | Pending | 需要 converter 设计与测试。 |

## 7.9 Backlog

1. 运行 `h2-fcidump-vqe-proxy` 的 real extension lane，并记录 `run_plan.json`、`run_artifact.json`、`validation.json`、`evidence.json`。
2. 运行 real agent lane，验证 Claude proposal 后是否能稳定进入 QCompute extension pipeline。
3. 将 real-mode energy / energy_error 与 dry-run reference echo 明确分表展示。
4. 为 `h2-fcidump-jw-vs-bk` 输出 real mapping metadata 表，包括 Pauli term count、mapping method、qubit count。
5. 扩展 ABACUS bridge parser，从 `INPUT` metadata 进入真实 `out_mat_hs` / `out_mat_hs2` matrix artifact 解析。
6. 定义 H/S matrix 到 FCIDUMP 或 QCompute Pauli dictionary 的正式转换目标。
7. 只有在 converter tests 通过后，才允许把 `abacus-hs-bridge-pending` 从 skipped sentinel 提升为 executable bridge case。
8. 增加 repeated real runs，记录 median elapsed time、driver overhead、simulator variance 和 flaky flags。
