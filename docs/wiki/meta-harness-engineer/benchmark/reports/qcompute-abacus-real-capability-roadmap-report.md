# QCompute × ABACUS Real-Capability Roadmap Report

> 日期：2026-04-30 | 范围：ABACUS H/S bridge readiness | 证据类型：代码级 scaffold、header-level parser contract、proxy conversion contract、truthfulness gates

## 1. 背景

上一轮 `qcompute-abacus` benchmark 已证明 MHE 可以把 ABACUS-adjacent Hamiltonian proxy 任务组织成可复查的三 lane workflow，但不能证明真实 ABACUS H/S matrix 已可被 QCompute 数值消费。

本轮工作的目标是把这个缺口转化为可执行 roadmap，并继续提升 capability：完成 artifact inventory、header-level parser contract、QCompute `pauli_dict` proxy conversion contract，以及 scientific validation / benchmark promotion blocker evidence。

## 2. Roadmap 状态

| 阶段 | 状态 | 本轮结果 | 当前 claim boundary |
|---|---|---|---|
| R0 artifact inventory | 已完成当前切片 | 从 `INPUT` 所在目录和 `OUT.<suffix>` 自动发现 `.csr` / `.txt` H/S artifact | 可声称 artifact 被发现并结构化记录 |
| R1 parser contract | 已完成 header-level 切片 | CSR `Matrix Dimension` / `Matrix number` 与 text `rows` / `columns` header 可解析进 `matrix_metadata` | 可声称 header-level parser contract 可测试；不能声称完整矩阵语义解析 |
| R2 conversion contract | 已完成 proxy 切片 | H matrix artifact 可转换为 QCompute `QubitHamiltonian` proxy，`source_format=abacus_hs_header_proxy`、`mapping_method=diagonal_z_proxy` | 可声称 QCompute pipeline contract proxy conversion；不能声称科学正确的 H/S→Hamiltonian conversion |
| R3 scientific validation | 未开始/阻断中 | `readiness_gates` 要求 reference fixture、tolerance table、scientific reviewer sign-off | 不能声称科学数值正确性 |
| R4 benchmark promotion | 阻断中 | `readiness_gates` 要求 real-mode executable bridge summary、comparison bundle、repeat-run stability | `abacus-hs-bridge-pending` 必须保持 capability skip |

## 3. 新增证据面

`bridge_status.json` 现在可以表达以下新增字段语义：

```json
{
  "matrix_metadata": [
    {
      "format_family": "abacus_sparse_csr",
      "matrix_role": "H",
      "parse_status": "header_parsed",
      "parser_contract_status": "header_parsed",
      "shape": [26, 26],
      "nnz": 177,
      "conversion_status": "unsupported",
      "validation_blockers": [
        "scientific_reference_missing"
      ]
    }
  ],
  "readiness_gates": [
    {
      "stage": "R1_parser",
      "status": "metadata_only",
      "claim_boundary": "H/S artifacts may be inventoried, but real matrix parsing is not complete."
    },
    {
      "stage": "R2_conversion",
      "status": "metadata_only",
      "claim_boundary": "Only proxy conversion is available; scientific ABACUS H/S conversion remains unvalidated."
    },
    {
      "stage": "R3_scientific_validation",
      "status": "not_started",
      "claim_boundary": "No scientific numerical correctness claim is allowed."
    },
    {
      "stage": "R4_benchmark_promotion",
      "status": "blocked",
      "claim_boundary": "The sentinel must remain capability-skipped until R2 and R3 pass."
    }
  ],
  "promotion_ready": false,
  "failure_code": "converter_missing"
}
```

新增 `convert_abacus_hs_header_to_pauli_proxy()` 可把 H matrix artifact 的 header/numeric sample 转成 QCompute `QubitHamiltonian` proxy：

```json
{
  "status": "converted",
  "target_format": "qcompute_pauli_dict",
  "qubit_hamiltonian": {
    "source_format": "abacus_hs_header_proxy",
    "mapping_method": "diagonal_z_proxy"
  },
  "metadata": {
    "conversion_kind": "diagonal_header_proxy",
    "scientifically_validated": false,
    "claim_boundary": "Proxy conversion is for QCompute pipeline contract testing only."
  }
}
```

这些字段提升的是 capability scaffold 和 reviewer 可见性，不是 scientific promotion。

## 4. 验证

本轮聚焦验证：

```bash
python -m pytest tests/test_benchmark_drivers_qcompute_abacus.py -q
ruff check src/metaharness_ext/qcompute/abacus_bridge.py tests/test_benchmark_drivers_qcompute_abacus.py
```

结果：`14 passed`，lint 通过。

## 5. 仍然不能声称的内容

- 不能声称 ABACUS H/S matrix 已被完整解析成科学可用矩阵。
- 不能声称 ABACUS H/S matrix 已转换为 FCIDUMP 或 QCompute `pauli_dict`。
- 不能声称 QCompute 已消费真实 ABACUS H/S Hamiltonian。
- 不能声称 real ABACUS × QCompute 数值准确性、性能优势或 quantum advantage。
- 不能把 `abacus-hs-bridge-pending` 提升为 executable bridge case。

## 6. 下一步进入真实支持所需条件

真实支持需要管理员或科学负责人提供并确认：

1. 一个可公开/可测试的 ABACUS H/S reference fixture；
2. 对应 ABACUS reference energy、spectrum 或 operator-level reference；
3. parser tolerance 与 conversion tolerance table；
4. scientific reviewer sign-off；
5. real-mode repeated benchmark evidence。

在这些条件满足前，MHE 的真实优势仍应表述为 workflow controllability、evidence completeness 和 overclaim prevention。
