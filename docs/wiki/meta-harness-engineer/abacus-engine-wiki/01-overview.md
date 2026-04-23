# 01. ABACUS 概述与定位

## 1.1 目标

`metaharness_ext.abacus` 的目标，不是重写 `ABACUS` 的求解器内核，也不是包装成任意输入文本运行器，而是把 ABACUS 的稳定控制面以 **受控、可声明、可验证、可审计** 的方式接入 MHE。

ABACUS 的稳定运行模型可以概括为：

```text
workspace(INPUT/STRU/KPT + assets) + launcher + abacus
  -> OUT.<suffix>/ + logs + structures + restart artifacts + structured validation
```

因此扩展层的核心职责是：

1. 用 typed contracts 表达可控的 ABACUS 运行规格
2. 将规格编译成稳定的 `INPUT` / `STRU` / `KPT`
3. 在受约束的 workspace / launcher 语义下运行 `abacus`
4. 收集 `OUT.<suffix>/` 及家族相关产物
5. 生成包含工程结果与科学证据的 validator/report
6. 为后续 study / mutation / orchestration 提供稳定证据面

---

## 1.2 为什么 ABACUS 适合接入 MHE

从本地 ABACUS 文档可以看到，ABACUS 的控制面天然具有声明式、分阶段和证据丰富的特征：

- 运行以固定命名输入文件为核心控制面：`INPUT`、`STRU`、`KPT`
- 并行语义主要由 launcher 管理：`mpirun`、`mpiexec`、`srun`
- 输出天然归档在 `OUT.<suffix>/` 下
- `OUT.<suffix>/INPUT` 可作为有效输入证据
- MD 模式天然产生 restart / trajectory / per-step 结构证据
- DPMD 集成是稳定配置面的一部分：`calculation=md`、`esolver_type=dp`、`pot_file`

这与 MHE 的 `environment -> compiler -> executor -> validator` 体系高度同构。

---

## 1.3 设计立场：选择 ABACUS 的哪一层作为 MHE 接口

结合 ABACUS 文档，可把可接入层大致分为四层：

- Level 1：物理问题与体系构造层（结构、势函数、边界条件、K 点与数值设置）
- Level 2：输入文件层（`INPUT` / `STRU` / `KPT` 及相关资产）
- Level 3：执行层（launcher + `abacus` binary）
- Level 4：结果与诊断层（`OUT.<suffix>/`、日志、结构产物、MD restart 证据）

对 MHE 来说，首版明确选择：

- **Level 2 为主**：typed spec 编译到稳定输入文件
- **Level 3 为核心执行面**：launcher + executable 受控运行
- **Level 4 为 validator 的证据面**：成功不只看 return code
- **不直接进入 Level 1 的全自由建模**：不承诺任意 ABACUS 参数的无约束透传

---

## 1.4 关键现实约束

### 1.4.1 ABACUS 是 file-driven，而不是 rich-subcommand CLI

ABACUS 不是像某些工具那样依赖丰富子命令；它主要依赖工作目录中固定命名文件：

- `INPUT`
- `STRU`
- `KPT`（按模式可选）

所以首版扩展的主战场不是 CLI 参数拼接，而是：

- workspace 布局
- 输入文件生成
- launcher 语义
- 输出目录发现

### 1.4.2 feature availability 必须被 probe，而不是默认假设

ABACUS 的若干重要能力是 build-time / environment dependent：

- DeePMD 支持
- GPU 支持
- basis/solver 兼容性
- launcher 可用性

因此 environment probe 必须先于正式执行，避免把环境缺失误判成物理或算法失败。

### 1.4.3 DPMD-in-ABACUS 属于 ABACUS mode，不是第二个扩展

ABACUS 文档表明，DPMD 通过 `calculation=md` + `esolver_type=dp` + `pot_file` 接入。

因此在 MHE 里更合理的边界是：

- `metaharness_ext.deepmd` 负责 DeepModeling-native workflow
- `metaharness_ext.abacus` 负责 ABACUS-native workflow
- `esolver_type=dp` 是 ABACUS extension 的一个受控 execution mode

---

## 1.5 首版支持边界

### 首版正式支持的 family

1. `scf`
2. `nscf`
3. `relax`
4. `md`

### 首版关键维度

- `basis_type`: `pw` / `lcao`
- `launcher`: `direct` / `mpirun` / `mpiexec` / `srun`
- `esolver_type`: 至少 `ksdft` / `dp`

### 首版明确不支持的方向

- 任意 ABACUS 文本参数透传
- 任意外部脚本/后处理自由拼接
- 直接把 HPC 集群编排写死进 executor
- 把 DeePMD native training workflow 混进 ABACUS extension
- 无约束支持所有 ABACUS 子模块和边缘模式

---

## 1.6 首版的价值

如果首版 ABACUS extension 做对了，它会给 MHE 带来几个稳定收益：

- 把 ABACUS 从“手工目录 + 手工 launcher”转换成 typed, auditable workflow
- 为 SCF/NSCF/relax/MD 提供统一 validator 语义
- 为 ABACUS+DeePMD 提供清晰边界和受控接入点
- 为未来 study、mutation、policy gate 和更复杂 orchestrator 铺好接口
