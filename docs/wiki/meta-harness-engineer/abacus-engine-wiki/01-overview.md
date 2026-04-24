# 01. 概述与定位

## 1.1 目标

`metaharness_ext.abacus` 的目标，不是重写 `ABACUS` 的求解器内核，也不是把它包装成任意输入文本运行器，而是把 ABACUS 的稳定控制面，以 **受控、可声明、可验证、可审计** 的方式接入 MHE。

ABACUS 的稳定运行模型可以概括为：

```text
workspace(INPUT/STRU/KPT + assets) + launcher + abacus
  -> OUT.<suffix>/ + logs + structures + restart artifacts + structured validation
```

因此扩展层的核心职责是：

1. 用 typed contracts 表达可控的 ABACUS 运行规格
2. 将规格编译成稳定的 `INPUT` / `STRU` / `KPT`
3. 在受约束的 workspace / launcher 语义下运行 `abacus`
4. 收集 `OUT.<suffix>/` 及 family-aware artifacts
5. 生成包含工程结果、证据线索与治理语义的 validator/report

---

## 1.2 为什么 ABACUS 适合接入 MHE

ABACUS 的控制面天然具有以下特征：

- 运行以固定命名输入文件为核心控制面：`INPUT`、`STRU`、`KPT`
- 并行语义主要由 launcher 管理：`mpirun`、`mpiexec`、`srun`
- 输出天然归档在 `OUT.<suffix>/` 下
- `OUT.<suffix>/INPUT` 可作为有效输入证据
- MD 模式天然产生 restart / trajectory / structure evidence
- `calculation=md` + `esolver_type=dp` + `pot_file` 可表达 DPMD-in-ABACUS mode

这与 MHE 的 environment / compiler / executor / validator 模式高度同构。

---

## 1.3 MHE 接哪一层

对 `metaharness_ext.abacus` 来说，当前合理落点是：

- **以输入文件层为主**：typed spec 编译到稳定输入文件
- **以执行层为核心运行面**：launcher + executable 受控运行
- **以结果与诊断层为 validator 的证据面**：成功不只看 return code
- **不直接进入全自由 Level 1 建模**：不承诺任意 ABACUS 参数都能无约束透传

这是一种刻意收缩边界的设计，而不是能力不足。

---

## 1.4 关键现实约束

### 1.4.1 ABACUS 是 file-driven，不是 rich-subcommand CLI

扩展的主战场不是 CLI 参数拼接，而是：

- workspace 布局
- 输入文件生成
- launcher 语义
- 输出目录发现

### 1.4.2 feature availability 必须被 probe，而不是默认假设

ABACUS 的一些能力是 build-time / environment dependent：

- DeePMD support
- GPU support
- launcher availability
- required runtime path completeness

因此 environment probe 必须先于正式执行。

### 1.4.3 ABACUS extension 仍在开发中

当前 ABACUS extension 已经形成清晰的 contracts、component slots、manifests 与 validator 方向，但它**仍在开发阶段，尚未完全开发**。

因此当前文档的正确语气应是：

- 把已经清晰的设计边界写稳
- 把代码中已经存在的 surface 与限制写清
- 对未完全完成的治理对齐保持明确的“待补齐”表述

而不是把它写成一个已经完全成熟封闭的扩展。

---

## 1.5 当前支持边界

当前在包与 contracts 层定义的 family 为：

- `scf`
- `nscf`
- `relax`
- `md`

当前关键 mode 维度包括：

- `basis_type`: `pw` / `lcao`
- `launcher`: `direct` / `mpirun` / `mpiexec` / `srun`
- `esolver_type`: `ksdft` / `dp`

但当前代码还包含明确限制：

- `md` 不支持 `basis_type=lcao`
- `scf` / `nscf` / `relax` 不支持 `esolver_type=dp`
- `md + esolver_type=dp` 需要 `pot_file`
- `nscf` 需要 `charge_density_path` 或 `restart_file_path`

这些限制属于当前真实边界，不应被文档写松。

---

## 1.6 结论

`metaharness_ext.abacus` 最合理的定位，是一个：

- **file-driven**
- **launcher-aware**
- **artifact-first**
- **environment-explicit**
- **governance-alignment-aware**

的科学执行后端扩展。

它已经具备清晰的设计骨架，但仍处于持续开发与治理面对齐阶段；因此 design wiki 的职责是把这个骨架写稳，而不是夸大已完成度。
