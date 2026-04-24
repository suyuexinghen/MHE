# 08. 运行生命周期

## 8.1 为什么需要单独的 lifecycle 页面

当前 `abacus-engine-wiki` 已经说明了组件边界，但如果缺少一页专门描述 **task spec 如何变成一次 ABACUS 运行**，读者仍然很难建立完整心智模型。

ABACUS 的扩展设计主线，不只是：

- 有哪些组件
- 有哪些 contracts

还包括：

- 一次运行从什么输入开始
- 在哪几个阶段被收紧和验证
- 哪些 artifacts 在哪个阶段出现
- family 差异在生命周期中的哪个位置发生

---

## 8.2 canonical lifecycle

对 `metaharness_ext.abacus` 来说，当前最小 canonical lifecycle 可以概括为：

```text
AbacusExperimentSpec
  -> environment probe
    -> INPUT / STRU / KPT compile
      -> workspace materialization
        -> launcher + abacus execution
          -> OUT.<suffix>/ discovery
            -> validation report
```

这条主线的重点，不是把 ABACUS 包成任意命令执行器，而是把它稳定的 file-driven workflow 纳入受控 lifecycle。

---

## 8.3 Phase A：task shaping

第一阶段由 gateway 负责把高层意图整理成 `AbacusExperimentSpec`。

在这个阶段，最重要的不是“配置全部参数”，而是固定：

- `application_family`
- `basis_type`
- `esolver_type`
- launcher contract
- family-specific prerequisite fields

例如：

- `nscf` 必须显式带 `charge_density_path` 或 `restart_file_path`
- `md + esolver_type=dp` 必须显式带 `pot_file`
- `md` 当前不能走 `basis_type=lcao`

因此 task shaping 已经是 lifecycle 的正式约束层，而不是薄薄的一层默认值填充。

---

## 8.4 Phase B：environment probe

environment probe 在生命周期里承担的是 **前置筛查**，不是附带提示。

它当前关注：

- `abacus` binary 是否存在
- launcher 是否存在
- `--version` / `--info` / `--check-input` 的 best-effort probe
- DeePMD / GPU support 的保守检测
- required paths 与 prerequisite 完整性

这一步的设计意义是：把“环境是否允许这次运行开始”从 runtime failure 中分离出来。

---

## 8.5 Phase C：input compile

compiler 把 typed spec 收敛成稳定输入文件：

- `INPUT`
- `STRU`
- `KPT`（按 family / mode 需要）

这里的主张是：

- compiler 生成 canonical 文本
- 不做任意输入文本 passthrough
- 不把 family-specific 逻辑留给 executor 临时猜测

对 ABACUS 来说，这一阶段很关键，因为输入文件本身就是最重要的控制面。

---

## 8.6 Phase D：workspace materialization

一次真实 ABACUS 运行并不只依赖三份文本输入，还依赖 workspace 语义：

- `INPUT` / `STRU` / `KPT` 的落盘位置
- pseudo / orbital / model assets 的可访问性
- `working_directory`
- 预期输出目录 `OUT.<suffix>/`

因此 workspace 不是“执行前的小细节”，而是 lifecycle 的正式部分。

---

## 8.7 Phase E：execution

execution 阶段由 executor 负责：

- 构造 launcher + `abacus` 命令
- 记录 stdout / stderr / return code
- 扫描 `OUT.<suffix>/`
- 收集 family-aware output files

这里需要特别强调的是：

- ABACUS 是 launcher-aware executable，不是富子命令 CLI
- 执行期的真实语义很大程度依赖输出目录与产物发现
- return code 只是证据的一部分

---

## 8.8 Phase F：validation

validation 不是执行后的薄后处理，而是 lifecycle 的最后一个正式阶段。

当前 validator 至少要回答：

- 这是 environment failure、input failure、runtime failure，还是 validation failure
- `OUT.<suffix>/` 与 family-specific artifacts 是否足够形成最小成功判据
- 当前结果是否带有治理意义上的 blocker / issue / scored evidence

因此 validation 是从“运行结果”到“治理可消费结果”的边界。

---

## 8.9 family-specific lifecycle 差异

### `scf`

最小主线是：

```text
spec -> INPUT/STRU/KPT -> run -> OUT.<suffix>/ + SCF evidence -> validation
```

### `nscf`

关键差异不在执行器，而在前置依赖：

- charge density / restart prerequisite 必须先被固定
- validator 不能把缺失前置当成普通 runtime 问题

### `relax`

关键差异在终态证据：

- final structure evidence 是成功面的一部分
- 不能只凭 output root 存在就判定成功

### `md`

关键差异在时序型产物：

- `MD_dump`
- `Restart_md.dat`
- `STRU_MD_*`

因此 `md` 的 lifecycle 天然比普通静态计算更强调 trajectory / restart surface。

### `md + esolver_type=dp`

它不是新 family，而是在 `md` lifecycle 中附加 DeePMD prerequisite：

- `pot_file` 成为强制前提
- environment probe 对 DeePMD support 采用保守策略
- validator 不把 feature-unknown 误当成“已支持”

---

## 8.10 lifecycle 与 runtime authority 的关系

ABACUS 的 lifecycle 结束在 validation report，而不是结束在 graph promotion。

更准确地说：

- extension 负责把一次运行变成结构化 result
- runtime authority 再决定这份 result 是否足以进入后续 promotion / audit / provenance path

因此 lifecycle 页应刻意停在 validation / evidence handoff，而不是跨越到更高层 authority 逻辑内部。

---

## 8.11 结论

ABACUS 的 lifecycle 设计主张应是：

- 先用 task shaping 固定 family 语义
- 再用 environment probe 收紧前提
- 再用 compiler / workspace 固定 file-driven control plane
- 再由 executor 产生运行证据
- 最后由 validator 把结果解释成治理可消费的 surface

这样组件链、contracts 与 family 差异才会在同一条主线上被理解。
