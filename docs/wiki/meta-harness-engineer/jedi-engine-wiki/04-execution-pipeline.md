# 04. 执行链设计

## 4.1 执行模式必须分层

JEDI extension 不能把所有动作都抽象成单一 `run()`，因为至少存在三类不同 execution mode：

1. `schema`
   - `<app>.x --output-json-schema=...`
2. `validate_only`
   - `<app>.x --validate-only config.yaml`
3. `real_run`
   - `<launcher> ... <app>.x config.yaml`

这三类模式的前提、产物和 validator 语义都不同，因此必须在 contracts、executor 和 validator 中显式分层。

---

## 4.2 规范执行链

JEDI extension 的规范执行链应保持为：

```text
request
  -> normalize to typed spec
  -> environment probe
  -> controlled YAML compile
  -> explicit preprocessing
  -> mode-aware execution
  -> validation report
```

这个顺序的设计意义在于：

- `environment probe` 在前，避免把环境问题误判成配置问题
- `compiler` 与 `preprocessor` 在 `executor` 之前，保证执行面只接收受控输入
- `validator` 作为统一判定面存在于链尾，而不是分散在各组件中

这里强调的是 **语义分层**，不是某一阶段实施计划中的步骤清单。

---

## 4.3 命令构造边界

执行链需要支持三种模式，但 command construction 的边界应保持克制：

### `schema`

- 负责生成 schema artifact
- 若未显式提供输出路径，应在 run workspace 内生成稳定默认路径

### `validate_only`

- 明确使用 `--validate-only`
- 关注 return code、stdout、stderr 与 config evidence

### `real_run`

- 负责 `<launcher> ... <app>.x config.yaml` 或 direct real run 的命令构造
- launcher 的选择属于执行面职责
- 资源编排、基线选择、科学判据不属于这一层

换言之，executor 需要理解 **如何执行**，但不应承担 **为什么选这个 baseline** 或 **如何解释科学结果** 的职责。

---

## 4.4 executable name 与 CTest test name 必须分离

这是 JEDI extension 中必须长期守住的边界：

- `qg4DVar.x`、`qgLETKF.x`、`qgHofX4D.x` 是 **executable name**
- `qg_4dvar_rpcg` 这类是 **CTest test name**

扩展的运行面必须围绕 executable 建模，而不能错误复用 test name。否则 command construction、environment probe 与 validator 语义都会失真。

---

## 4.5 artifact layout 是证据面设计，不是脚手架细节

执行链需要稳定的 artifact layout，但这里关心的是设计原则，而不是具体脚手架清单。

每次运行都应有可审计、可预测的证据布局，以支持：

- `config.yaml`、`stdout`、`stderr` 的稳定归档
- outputs / diagnostics / references 的稳定定位
- validator、CLI 与 agent 对证据文件的统一消费

artifact layout 的具体路径约定可以由 blueprint / implementation plan 进一步细化，但 wiki 中应把它描述为 **证据面稳定性要求**。

---

## 4.6 executor 不应理解业务 YAML 结构

一旦 executor 根据 family-specific 字段分支业务逻辑，架构会迅速失去清晰边界。

正确分工是：

- compiler 负责 family-specific YAML 结构
- executor 只负责 mode-aware command construction 与 process execution
- validator 负责结果判定

executor 最多知道 `execution_mode`、launcher 与 executable，不应该知道 `cost function`、`local ensemble DA` 或其他 family 内部块结构。