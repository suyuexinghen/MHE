# 04. 环境、验证与证据

## 4.1 为什么 environment probe 是正式组件

ABACUS 的常见早期失败，很多不是输入逻辑错误，而是环境前提没有满足：

- `abacus` binary 不存在
- launcher 不可用
- `--version` / `--info` / `--check-input` 支持度不一致
- required runtime paths 缺失
- `md + dp` 请求下 DeePMD support 未检测到或不可确认

如果没有独立 environment probe，这些问题就会被模糊地压到 executor 或 validator 阶段，破坏 failure taxonomy。

---

## 4.2 当前 `AbacusEnvironmentReport`

当前环境报告已经形成可用的 probe baseline，但仍应被理解为**开发中的现有实现面**，而不是已经完全封闭的环境语义：

- binary availability
- launcher availability
- version/info/check-input probe supported / succeeded 状态
- DeePMD / GPU feature detection
- required path 完整性
- prerequisite 列表与缺失项
- `evidence_refs`

它当前的价值，不只是 preflight，而是把运行前提显式变成后续治理输入；但像 DeePMD / GPU 之类 feature probe，现阶段仍应按保守、best-effort 的实现理解，而不是把它写成绝对完备的 capability detection。

---

## 4.3 当前 baseline failure taxonomy

当前 validation status surface 为：

- `environment_invalid`
- `input_invalid`
- `runtime_failed`
- `validation_failed`
- `executed`

这组状态的意义是：

- `environment_invalid`：环境前提不满足
- `input_invalid`：输入组合或要求本身不合法
- `runtime_failed`：执行期失败
- `validation_failed`：命令可能结束，但证据不足以支持成功判定
- `executed`：当前最小执行判据通过

它们当前不只是 extension-local 状态，也是更上层治理分类入口的 baseline surface；但文档不应把这组状态写成未来所有治理分类语义都已冻结完毕。

---

## 4.4 ABACUS 的 evidence-first surface

ABACUS 的主证据面不是 return code，而是：

- `prepared_inputs`
- `OUT.<suffix>/`
- output / structure / diagnostic files
- `stdout` / `stderr`
- `evidence_refs`

因此 validator 的成功判断应建立在多类证据组合之上，而不是某个单点文件存在性。

---

## 4.5 `AbacusValidationReport` 的治理含义

当前 validation report 已经包含：

- `issues`
- `blocks_promotion`
- `governance_state`
- `scored_evidence`

这说明 ABACUS validator 已经不再只是普通 post-run helper，而是当前 extension-local 的 protected governance boundary。

但文档语气仍应保持克制：这些字段说明 **治理对齐方向已经进入当前 contract surface**，不等于所有更高层 policy / review / provenance path 都已经完全实现闭环。

它当前至少回答的问题包括：

- 失败是否足以阻断 promotion
- 当前证据是否完整到足以进入 review
- 哪些问题属于治理级缺口，而不是普通运行失败

---

## 4.6 `md + dp` 的保守策略

对于 `md + esolver_type=dp`，当前环境与验证策略应保持保守：

- 只有在 prerequisite 满足时才允许进入运行路径
- DeePMD support 不能明确确认时，按前提不足处理
- 不把 feature-unknown 误写成“已经支持”

这也是为什么 ABACUS wiki 需要明确写出“仍在开发中”，避免把尚在补齐的 feature path 写成已经完全稳定。

---

## 4.7 结论

ABACUS 的环境、验证与证据设计主张应是：

- 先把环境失败、输入失败、运行失败分开
- 再把 artifacts 与 evidence refs 组织成可审计证据面
- 再由 validator 输出治理可消费的 validation result

当前实现已经提供了这条主线的最小闭环，但仍应继续以“保守 probe、稳定 taxonomy、逐步补强治理接缝”的方式推进，而不是把现阶段写成已经完全成熟的证据系统。
