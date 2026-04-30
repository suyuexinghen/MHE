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
| R3 scientific validation | 已完成 validator contract 切片/真实验证仍阻断 | 新增 `bridge_validation.json`，可对 tiny dense H/S reference fixture 执行 generalized eigenproblem tolerance check；默认 sentinel 仍记录缺少管理员认可 fixture、tolerance table、reviewer sign-off、production converter | 只能声称 validation contract 可测试；不能声称真实 ABACUS H/S 科学验证已完成 |
| R4 benchmark promotion | 阻断中 | `readiness_gates` 要求 real-mode executable bridge summary、comparison bundle、repeat-run stability；`bridge_validation.promotion_ready=false` | `abacus-hs-bridge-pending` 必须保持 capability skip |

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

新增 `bridge_validation.json` 用于表达 R3 validator contract 状态；默认 sentinel 仍阻断：

```json
{
  "status": "blocked",
  "validation_kind": "small_dense_hs_eigenproblem",
  "reference_validated": false,
  "scientifically_validated": false,
  "promotion_ready": false,
  "blockers": [
    "administrator_approved_reference_fixture_missing",
    "tolerance_table_missing",
    "scientific_reviewer_signoff_missing",
    "production_converter_missing"
  ]
}
```

对于显式 tiny dense reference fixture，validator 可计算 2×2 generalized eigenproblem 并比较 reference eigenvalues；这只证明 validation contract，不证明 production ABACUS H/S conversion。

新增 `review_signoff.json` 用于表达 reviewer evidence 状态；默认 deterministic/ACP reviewer 仍必须阻断 promotion：

```json
{
  "reviewer_backend": "deterministic_policy",
  "decision": "block",
  "claim_boundary_ok": true,
  "reviewer_evidence_only": true,
  "replaces_human_scientific_signoff": false,
  "sentinel_must_remain_skipped": true,
  "accepted_evidence": [
    "bridge_status.json",
    "bridge_validation.json"
  ],
  "missing_evidence": [
    "administrator_approved_reference_fixture_missing",
    "tolerance_table_missing",
    "scientific_reviewer_signoff_missing",
    "production_converter_missing",
    "abacus_hs_to_fcidump_converter"
  ]
}
```

ACP-connected Claude Code 可在 JSON diagnostic 稳定通过后填充同一 schema；`reviewer_evidence_only=true` 与 `replaces_human_scientific_signoff=false` 是强制 claim boundary，表示它能补强 reviewer evidence，但不能替代 human/scientific sign-off 或管理员认可的真实 fixture。

新增 `approval_manifest.json` 用于把管理员/科学负责人认可变成显式机器可读证据；默认缺失状态仍阻断 promotion：

```json
{
  "status": "missing",
  "approved_by": null,
  "approval_role": null,
  "fixture_refs": [],
  "tolerance_table_ref": null,
  "reference_observable": null,
  "notes": [
    "No abacus_hs_approval.json approval manifest was provided."
  ]
}
```

即使提供 `abacus_hs_approval.json`，也必须包含 `approved_by`、`approval_role`、`fixture_refs`、`tolerance_table_ref` 和 `reference_observable`；否则状态为 `invalid`。

新增 `promotion_gate.json` 汇总 bridge status、validation、review signoff 与 approval manifest，作为 R4 是否可晋升的单一 gate；默认仍阻断：

```json
{
  "status": "blocked",
  "promotion_ready": false,
  "required_artifacts": [
    "bridge_status.json",
    "bridge_validation.json",
    "review_signoff.json",
    "abacus_hs_approval.json",
    "production_converter_evidence",
    "real_mode_repeat_summary"
  ],
  "missing_evidence": [
    "human_scientific_approval_manifest_missing",
    "administrator_approved_reference_fixture_missing",
    "tolerance_table_missing",
    "scientific_reviewer_signoff_missing",
    "production_converter_missing",
    "abacus_hs_to_fcidump_converter",
    "real_mode_repeat_summary_missing"
  ],
  "missing_evidence_by_category": {
    "human_approval": [
      "human_scientific_approval_manifest_missing"
    ],
    "scientific_validation": [
      "administrator_approved_reference_fixture_missing",
      "tolerance_table_missing",
      "scientific_reviewer_signoff_missing"
    ],
    "production_converter": [
      "production_converter_missing",
      "abacus_hs_to_fcidump_converter"
    ],
    "real_repeat_evidence": [
      "real_mode_repeat_summary_missing"
    ]
  },
  "claim_boundary_ok": true,
  "sentinel_must_remain_skipped": true
}
```

因此，管理员认可 manifest 只是必要条件之一；没有 production converter evidence 和 real-mode repeat summary 时，仍不能晋升 sentinel，也不能声称真实 ABACUS × QCompute conversion 已可用。分类 gate 的责任边界如下：

| blocker category | 可满足方 | ACP/Claude reviewer 能做什么 | CI/tests 能做什么 | claim boundary |
|---|---|---|---|---|
| `human_approval` | 授权管理员/科学负责人 | 只能检查 manifest schema 与缺失字段，不能批准 | 验证 `missing` / `invalid` / `approved` 状态解析 | human approval 是必要条件，不是充分条件 |
| `scientific_validation` | 科学负责人/领域 reviewer | 可审查 evidence completeness 和 overclaim 风险 | 验证 tiny dense validator contract 和 blocker 输出 | validator contract 不等于 production scientific validation |
| `production_converter` | converter 实现与代码/科学审查 | 可审查 conversion plan、claim boundary 和缺口 | 验证 converter evidence artifact 存在并通过真实 fixture 测试 | proxy/header conversion 不能冒充 production converter |
| `real_repeat_evidence` | benchmark runner + 真实工具环境 | 可辅助报告 repeat evidence，但不能制造真实运行 | 验证 `repeat_summary.json` schema、非 dry-run 标记和稳定性字段 | repeated dry-run 不能证明真实数值稳定性 |


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

结果：`43 passed`（focused CLI + QCompute ABACUS tests），lint 通过，格式检查通过。

## 5. 仍然不能声称的内容

- 不能声称 ABACUS H/S matrix 已被完整解析成科学可用矩阵。
- 不能声称 ABACUS H/S matrix 已科学正确地转换为 FCIDUMP 或 production QCompute `pauli_dict`。
- 不能声称 QCompute 已消费科学验证过的真实 ABACUS H/S Hamiltonian；当前只有 proxy conversion contract。
- 不能声称 real ABACUS × QCompute 数值准确性、性能优势或 quantum advantage。
- 不能把 `abacus-hs-bridge-pending` 提升为 executable bridge case。

## 6. 下一步进入真实支持所需条件

真实支持需要管理员或科学负责人提供并确认：

1. 一个可公开/可测试的 ABACUS H/S reference fixture；
2. 对应 ABACUS reference energy、spectrum 或 operator-level reference；
3. parser tolerance、conversion tolerance 与 validator tolerance table；
4. scientific reviewer sign-off；
5. production converter evidence and real-mode repeated benchmark evidence。

在这些条件满足前，MHE 的真实优势仍应表述为 workflow controllability、evidence completeness 和 overclaim prevention。
