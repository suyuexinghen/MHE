# 04. Testing and Extension Guide

## 4.1 测试策略概览

`metaharness_ext.nektar` 当前有一套相对完整的分层测试策略：

1. **manifest / 装配测试**
2. **compiler / renderer 单元测试**
3. **executor / postprocess / validator 行为测试**
4. **真实 Nektar++ e2e 测试**

这种结构很适合 solver 集成类代码：

- 单元测试锁住 contract 和命令构造
- e2e 测试验证本地真实环境下的 CLI 契约没有漂移

---

## 4.2 manifest 层测试

`MHE/tests/test_metaharness_nektar_manifest.py:23` 检查了五个核心组件 manifest：

- manifest 文件集合完整
- manifest 字段与预期一致
- entry importable
- `declare_component()` 后的 API snapshot 与 manifest 对齐

这保证了 `metaharness_ext.nektar` 不只是“模块能 import”，而是能正确接入 `MetaHarness` 的组件注册体系。

---

## 4.3 单元测试覆盖面

### 4.3.1 compiler / renderer

现有测试覆盖了：

- ADR / IncNS 默认选择
- inline geometry / external mesh 模式
- unsteady 时间积分默认值
- Robin BC 与 `PRIMCOEFF`
- forcing / exact solution / function rendering
- renderer 对不支持 surface 的拒绝

### 4.3.2 executor

现有测试覆盖了：

- 缺少 `runtime.storage_path`
- 非法 `task_id`
- solver binary 找不到
- external mesh 缺失
- nonzero exit / timeout
- `.fld` / `.chk` 发现
- solver 输出中的误差提取
- solver 输出中的 step/time 指标提取
- IncNS stdout 误差提取

### 4.3.3 postprocess / validator

`MHE/tests/test_metaharness_nektar_postprocess.py` 覆盖面尤其完整，包含：

- `.fld` 优先于 `.chk`
- 回退到最新 checkpoint
- binary 缺失
- 无输入文件
- nonzero exit / timeout
- 无 postprocess plan
- `FieldConvert -e` 真实输出格式
- 忽略坐标误差
- `-m vorticity`、`-m extract:bnd=0`
- 多步 postprocess 计划
- IncNS convergence metrics 提取
- validator 对 postprocess 状态和容差的解释

---

## 4.4 真实 e2e 基线

`MHE/tests/test_metaharness_nektar_e2e.py:151` 提供了真实环境基线。

### 4.4.1 ADR Helmholtz

已覆盖：

- `Helmholtz1D_8modes.xml`
- `Helmholtz2D_DirectFull.xml`

验证点包括：

- solver 真正执行成功
- `.fld` 产物存在
- `FieldConvert` 能输出 `solution.vtu`
- validator 最终 `passed is True`

### 4.4.2 `FieldConvert -e`

已覆盖 1D / 2D 两条真实误差评估基线：

- `FieldConvert -e session.xml session.fld error.vtu`
- 校验 `error.vtu` 存在
- 校验真实 `l2_error_u` / `linf_error_u`
- 校验坐标误差未进入验证逻辑

这部分尤其重要，因为它锁住了本机 Nektar++ 5.9.0 的真实 CLI 行为，避免未来误解 `-e` 的参数契约。

### 4.4.3 IncNS Taylor vortex

已覆盖 `TaylorVor_dt1.xml`：

- 真实运行 `IncNavierStokesSolver`
- 提取 `u / v / p` 的 solver-side error norms
- 生成 `solution.vtu`
- validator 通过且 `error_vs_reference is True`

---

## 4.5 扩展入口

若你要继续扩展这个包，当前最自然的入口如下。

## 4.5.1 新增 solver family

需要至少修改：

- `MHE/src/metaharness_ext/nektar/types.py`
- `MHE/src/metaharness_ext/nektar/contracts.py`
- `MHE/src/metaharness_ext/nektar/session_compiler.py`
- `MHE/src/metaharness_ext/nektar/xml_renderer.py`
- `MHE/src/metaharness_ext/nektar/solver_executor.py`
- 相关 manifest / tests

建议顺序：

1. 先扩枚举与 contracts
2. 再扩 compiler 默认值
3. 再扩 renderer surface
4. 再扩 executor 指标提取
5. 最后补 mocked tests 与真实 e2e

## 4.5.2 新增 postprocess step 类型

当前 `_execute_step()` 只支持 `fieldconvert`。若要新增其他后处理器，建议：

- 保持 step-level dispatch 结构不变
- 为新 step 定义独立 command builder / result parser
- 继续把结果汇总到 `artifact.result_summary["postprocess"]`
- 继续把派生文件落入 `derived_files` 与 `fieldconvert_intermediates` 的同类结构（如有必要可重命名成更通用字段）

## 4.5.3 增强 validator

当前 validator 很轻量。如果未来想加更强的 scientific checks，建议保持以下原则：

- 提取逻辑不要塞进 validator
- validator 只消费 artifact 里已存在的证据
- 任何新规则都最好配套结构化 `metrics` 与清晰 `messages`

---

## 4.6 当前值得注意的技术债

基于现有实现，可以看到几类后续演进空间：

### 4.6.1 `analyzers.py` 仍很薄

`MHE/src/metaharness_ext/nektar/analyzers.py:9` 当前只是 stub 风格实现，说明分析能力还没有真正沉淀到独立可复用层。

### 4.6.2 `global_system_solution_info` 只在 contract 中预留

目前还没有完整渲染与测试支持。

### 4.6.3 geometry / mesh pipeline 仍偏简化

当前 external mesh 模式更多是 overlay，而不是完整 mesh preparation pipeline。

### 4.6.4 validator 容差规则仍偏单一

目前主要依赖最大 L2 误差与固定容差，未来可能需要：

- 按变量分开判定
- family-specific tolerance
- time history / conservation / residual curve 级别的规则

---

## 4.7 建议的扩展节奏

如果要继续推进 `metaharness_ext.nektar`，一个稳妥的顺序是：

### Phase A：补强已有 slice

- 整理 `analyzers.py`
- 统一 solver/postprocess 指标提取工具
- 明确 artifact metadata 结构

### Phase B：扩后处理与验证

- 增加更多 `FieldConvert -m` 模块支持
- 丰富 validator 的 family-specific 规则
- 增加更多真实 benchmark e2e

### Phase C：扩输入与编排

- 更丰富的 mesh 预处理
- 更丰富的 case authoring / parser
- 接入更上层 AI4PDE runtime 或模板系统

---

## 4.8 总结

当前 `metaharness_ext.nektar` 的实现已经具备一个很扎实的工程基线：

- contracts 清晰
- 渲染边界明确
- solver 执行真实可跑
- `FieldConvert` 后处理真实可跑
- validator 能消费真实误差与收敛证据
- mocked + e2e 双层测试都在位

因此，后续扩展最重要的不是“重写架构”，而是继续沿着现有边界补充：

- 更多可证明的 capability
- 更多 solver-specific evidence
- 更多基于真实 Nektar++ 行为的测试基线
