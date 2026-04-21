# 06. Nektar Next-Phase Roadmap

> 状态：proposed | 面向 `metaharness_ext.nektar` 的正式执行路线图

## 6.1 推荐执行顺序

建议执行顺序如下：

```text
Phase 0: Analyzers
  -> Phase 1: Convergence MVP
    -> Phase 2: Convergence Real Baseline
      -> Phase 3: 3D Baseline
        -> Phase 4: External Mesh Strengthening
          -> Phase 5: Advanced Geometry Modes
```

虽然收敛研究的业务价值最高，但从实施角度看，**先完成 analyzers，再做 convergence** 能明显降低返工。

**通用验收标准**：每个 Phase 完成后，全量测试套件必须保持 76+ tests 零回归（`pytest` + `ruff check`）。

---

## 6.2 Phase 0：Analyzers

## 6.2.1 目标

完成 `MHE/src/metaharness_ext/nektar/analyzers.py`，把它升级为共享分析底座。

## 6.2.2 任务

1. 在 `contracts.py` 新增三个 Pydantic 返回模型：`SolverLogAnalysis`、`FilterOutputAnalysis`、`ErrorSummary`
2. 更新三个函数签名为类型化返回值（不再返回 `dict` 或 `FilterOutputSummary`）
3. 实现 solver log 解析（warnings、errors、step metrics、error norms、IncNS convergence）
4. 实现派生文件摘要（存在性、格式、大小统计）
5. 实现 reference error 汇总（L2/Linf 提取、tolerance 判定、status 分类）
6. 新增 `MHE/tests/test_metaharness_nektar_analyzers.py`

## 6.2.3 交付物

- `contracts.py` 新增 3 个 Pydantic model
- `analyzers.py` 三个存根替换为有效实现，返回类型化 model
- `test_metaharness_nektar_analyzers.py` 新增

## 6.2.4 验收标准

- 三个 stub 全部替换为有效实现
- 返回值为 Pydantic model（非 `dict`）
- 缺失文件、空输入、正常输入、IncNS 特殊日志都有稳定返回
- 单元测试覆盖主要分支
- 全量测试套件零回归

---

## 6.3 Phase 1：Convergence MVP

## 6.3.1 目标

新增 `ConvergenceStudyComponent`，支持 `NUMMODES` 维度的最小收敛研究。

## 6.3.2 任务

1. 新增 `NektarMutationAxis`、`ConvergenceStudySpec`、`ConvergenceStudyReport` 到 `contracts.py`
2. 新增 `convergence.py` 与 `convergence.json`
3. 增加 `convergence_study.primary` slot 与 `nektar.study.convergence` capability
4. 实现基于 `base_problem` 的 typed mutation 循环
5. 通过构造时注入已激活子组件的方式协调 executor / postprocess / validator
6. 串联 compile -> execute -> postprocess -> validate
7. 新增 `MHE/tests/test_metaharness_nektar_convergence.py`

## 6.3.3 范围边界

首版仅支持：

- axis kind = `num_modes`
- 串行执行
- 基于 artifact / validator 结果做判定
- 子组件通过参数注入（非 convergence 自行激活）

## 6.3.4 验收标准

- 能生成结构化 `ConvergenceStudyReport`
- mock tests 全绿
- 不破坏现有组件职责边界
- 全量测试套件零回归

---

## 6.4 Phase 2：Convergence Real Baseline

## 6.4.1 目标

把 convergence 功能从 mock 层推进到真实 Nektar 基线层。

## 6.4.2 当前已落地内容

1. report 已接入 analyzer 输出（`SolverLogAnalysis`、`FilterOutputAnalysis`、`ErrorSummary`）
2. `ConvergenceStudySpec` 已支持 `convergence_rule`、`relative_drop_ratio`、`plateau_tolerance`
3. `ConvergenceStudyReport` 已支持 `observed_order`、`recommended_reason`、`error_sequence`、`drop_ratios`
4. `absolute` / `relative_drop` / `plateau` 三类规则已接入同一套 rule engine
5. `stop_on_first_pass` 已升级为 rule-aware 提前停止
6. Helmholtz 1D / 2D 真实 `NumModes` sweep e2e 已补齐

## 6.4.3 当前验收状态

- 真实 Helmholtz 1D / 2D baseline 可输出稳定 study report
- study 结论可被 CLI / report / agent 直接消费
- targeted pytest 与 ruff 验证已通过

---

## 6.4.4 后续可选增强

- 将 `NektarMutationAxis` 从当前 `num_modes` 单轴扩展到 `mesh_path` / `time_step`
- 在 CLI / agent 层暴露三类规则与阈值调参入口
- 视需要把 study report 落盘为稳定产物或纳入更高层 report pipeline

---

## 6.5 Phase 3：3D Baseline

## 6.5.1 目标

支持最小 3D 问题进入 compile / render 流程。

## 6.5.2 任务

1. 为 `NektarGatewayComponent.issue_task()` 增加 `dimension`、`space_dimension`、`variables` 参数（参数透传，`NektarProblemSpec` 已有对应字段）
2. 将 `_default_geometry()` 拆为 `_default_geometry_2d()` 与 `_default_geometry_3d()`
3. 为 3D 提供 unit hex baseline geometry
4. 强化 3D geometry completeness 校验
5. 增加 3D golden XML / negative tests

## 6.5.3 验收标准

- 3D `NektarProblemSpec` 可被编译
- renderer 能稳定输出 3D `GEOMETRY`
- 3D success / negative tests 齐全
- 全量测试套件零回归

---

## 6.6 Phase 4：External Mesh Strengthening

## 6.6.1 目标

让 external mesh support 具备更清晰、更稳健的失败语义和校验链路。

## 6.6.2 任务

1. 明确 `source_mode` 语义
2. 增加 mesh existence / compatibility 预检查
3. 改善 external mesh 错误消息
4. 增加缺失路径、冲突模式等负向测试

## 6.6.3 验收标准

- external mesh 失败路径可解释
- 相关测试覆盖充分
- 全量测试套件零回归

---

## 6.7 Phase 5：Advanced Geometry Modes

## 6.7.1 目标

按需求逐步扩展更复杂几何/网格能力。

## 6.7.2 候选子项

- curved elements
- prism / hex mixed support
- homogeneous strip support
- `NekMesh` integration
- mesh-level convergence axis

## 6.7.3 启动条件

仅在以下条件满足后启动：

- analyzers 已稳定
- convergence 已有真实稳定基线
- 3D baseline 已验证

---

## 6.8 测试路线图

### 单元测试优先级

1. `MHE/tests/test_metaharness_nektar_analyzers.py`（Phase 0）
2. `MHE/tests/test_metaharness_nektar_convergence.py`（Phase 1）
3. 现有 compiler tests 中的 3D cases（Phase 3）
4. 现有 renderer tests 中的 3D golden / negative cases（Phase 3）

### e2e 测试优先级

1. Helmholtz 1D convergence sweep（Phase 2）
2. Helmholtz 2D convergence sweep（Phase 2）
3. 3D minimal case（Phase 3，仅在真实 3D 示例具备后）

### 回归保障

每个 Phase 的 PR 必须通过：

- `pytest` 全量测试（当前基线 76 tests）
- `ruff check` 零警告
- 不删除或跳过现有测试（除非有明确理由）

---

## 6.9 里程碑

### M1：Analyzer Foundation

交付：Phase 0 完成。3 个 Pydantic-typed analyzer 函数 + 测试。

### M2：Convergence MVP

交付：Phase 1 完成，支持 `NUMMODES` sweep。

### M3：Convergence Real Baseline

交付：Phase 2 完成，真实 Helmholtz 收敛研究可用。

### M4：3D Baseline

交付：Phase 3 完成，3D compile/render 受支持。

### M5：External Mesh Strengthening

交付：Phase 4 完成，external mesh 错误链路更健壮。

### M6：Advanced Geometry

交付：Phase 5 按实际需求推进。

---

## 6.10 风险与取舍

### 高杠杆投入

- `Analyzers + Convergence` 的组合投入最小、收益最大
- 它直接提升系统的解释力与研究力

### 高实现风险

- 3D / mesh 支持范围最容易膨胀
- 若没有真实 3D 需求，过早推进收益偏低

### 关键控制点

- analyzer 不与 validator 职责重叠
- convergence 不直接操纵 XML
- 3D 首阶段不提前扩展到完整 `NekMesh` 编排
- 每个 Phase 必须通过全量回归测试

---

## 6.11 最终建议

推荐用两轮推进：

### 第一轮

- Phase 0：Analyzers（Pydantic-typed 返回值）
- Phase 1：Convergence MVP
- Phase 2：Convergence Real Baseline

### 第二轮

- Phase 3：3D Baseline
- Phase 4：External Mesh Strengthening
- Phase 5：Advanced Geometry Modes

这一路线最符合当前代码成熟度，也最符合 `NEKTAR_BLUEPRINT` 中"先稳定 typed execution loop，再进入 adaptive iteration"的总体方向。
