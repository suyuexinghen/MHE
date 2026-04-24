# 04. 执行链设计

## 4.1 执行模式必须分层

本文档中，概念层统一使用 **execution mode**；叙述性文字使用 **validate-only**、**real run**；代码字面量与 contract 字段继续使用 `validate_only`、`real_run`。

JEDI extension 不能把所有动作都抽象成单一 `run()`，因为至少存在三类不同模式：

1. `schema`
   - `<app>.x --output-json-schema=...`
2. `validate_only`
   - `<app>.x --validate-only config.yaml`
3. `real_run`
   - `<launcher> ... <app>.x config.yaml`

这三类模式的前提、产物和 validator 语义都不同。

---

## 4.2 当前 Phase 0 的最小执行链

Phase 0 现在实现：

```text
request
  -> normalize to typed spec
  -> environment probe
  -> controlled YAML compile
  -> explicit preprocessing
  -> mode-aware execution
  -> validation report
```

这个顺序不能随意打乱，原因是：

- environment probe 在前，避免把环境错误误报成 YAML 错误
- compiler / preprocessor 在 executor 前，避免 executor 接收未治理输入或缺失运行物料
- validator 在最后，作为统一判定面，而不是散落在各组件里

---

## 4.3 命令构造原则

### schema

- 命令应直接生成 schema artifact
- 若未提供 `schema_output_path`，组件应在 run workspace 内生成稳定默认路径

### validate_only

- 命令应明确使用 `--validate-only`
- 产物重点是 return code、stdout、stderr 和 config evidence

### real_run

- 属于当前基础执行接口面
- 负责 `<launcher> ... <app>.x config.yaml` 或 direct real run 的命令构造
- 当前 canonical launcher mapping 明确固定为：`mpiexec -> -n`、`mpirun -> -n`、`srun -> -n`、`jsrun -> -n`
- `launcher_args` 只承载非 process-count 的附加参数；如果其中重复传入 `-n` / `-np` / `--ntasks` 一类 process-count flag，executor 应直接拒绝，避免与 `process_count` 形成双重来源
- smoke baseline policy、richer diagnostics interpretation 与 scientific acceptance checks 再放到后续 phase
- advanced scheduler/resource semantics 当前仍不支持；例如 `srun`/`jsrun` 的 richer placement、allocation、resource-set contract 还没有进入当前执行面

---

## 4.4 executable name 与 CTest test name 必须分离

这是 JEDI extension 里必须反复守住的边界：

- `qg4DVar.x`、`qgLETKF.x`、`qgHofX4D.x` 是 **executable name**
- `qg_4dvar_rpcg` 这类是 **CTest test name**

extension 的运行面必须围绕 executable 建模，而不是错误复用 test name。

---

## 4.5 working directory 与 artifact layout

当前 Phase 0 已经有显式 preprocessor，因此需要固定 artifact layout 思路：

```text
runtime.storage_path / jedi_runs / <task_id> / <run_id>/
  |- config.yaml
  |- stdout.log
  |- stderr.log
  |- schema.json                       (optional)
  |- analysis.out / other outputs      (optional)
  |- departures.json / other diagnostics (optional)
  |- reference.json / other references (optional)
```

这样做的好处是：

- validator / CLI / agent 能消费稳定路径
- 后续增加 richer diagnostics interpretation 时不需要推翻布局
- evidence files 从第一天起就有一致归档方式

---

## 4.6 为什么不能让 executor 理解 YAML 结构

一旦 executor 开始根据 family-specific 字段分支命令逻辑，架构很快会失去可维护性。

正确分工是：

- compiler 负责 family-specific YAML 结构
- executor 只负责 mode-aware command construction 与 process execution
- validator 负责结果判定

executor 最多知道 `execution_mode`，不应该知道 `cost function` 或 `local ensemble DA` 的内部字段布局。