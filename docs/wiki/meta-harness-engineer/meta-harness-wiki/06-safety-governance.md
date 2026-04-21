# 06. 安全控制与治理

本章把 Meta-Harness 的安全体系落到可实现的治理平面上。目标不是给系统外挂一层"审查器"，而是把**四级安全链路、宪法层策略、沙箱分级、不变量模板库、间接攻击防护、治理 hooks** 固化成 staged lifecycle 的一部分。当 Optimizer 获得修改组件配置的能力时，必须建立多层纵深防御机制，确保系统的行为始终处于可控、可解释、可恢复的安全边界之内。

为与前文保持一致，本文统一使用：

- **9 core components + Optimizer**：系统的基础组件与元层优化器
- **slot/capability system**：位点与能力约束系统
- **pending mutations**：待提交变更集合
- **candidate graph / active graph version / rollback target**：图版本切换对象
- **Policy / Governance**：控制面治理组件，默认属于 protected components
- **Guard / Mutate / Reduce hooks**：治理层的三类关键钩子语义

---

## 6.1 治理目标与边界

Meta-Harness 的安全问题不只是"如何阻止恶意代码"，还包括"如何阻止一个看似正常的优化动作把系统推入不可控状态"。因此治理层必须同时回答四个问题：

| 目标 | 说明 | 直接机制 |
| --- | --- | --- |
| 阻断危险执行 | 不可信代码、工具调用、外部连接不能越界 | sandbox ladder + policy guard |
| 约束非法变更 | Optimizer 不能绕过治理直接修改关键路径 | constitutional layer + protected components |
| 保证系统不变量 | 新图必须满足契约、预算、身份和审计要求 | invariant library + validation pipeline |
| 支持失败恢复 | 错误变更要能回滚、熔断、留下证据 | observation window + rollback target + audit chain |

治理层的边界也必须清晰：

- `Optimizer` 只能生成 `mutation proposal`，不能直接写 `active graph version`
- `Policy / Governance` 可以 veto、annotate、reduce，但不能偷偷改活动图
- `ConnectionEngine` 只消费已批准且已提交的 graph snapshot
- `policy.primary` 默认是 `protected component`，不能被普通自动优化覆盖

---

## 6.2 四级安全链路

Meta-Harness 推荐把安全控制做成固定的四级链路。四级并不是简单叠加，而是对同一变更从不同角度做筛选：

```
mutation proposal
  -> Level 1 sandbox validation
  -> Level 2 shadow / A-B validation
  -> Level 3 policy constitutional review
  -> Level 4 rollback readiness and live observation
```

| 安全链路层级 | 核心工程目标 | 关键指标 | 失败处理 |
|---|---|---|---|
| 第一级：沙箱验证 | 阻断恶性代码与资源逃逸 | 启动延迟 (<150ms)、回归通过率 | 直接拒绝，负向奖励信号 |
| 第二级：A/B 影子测试 | 验证新逻辑的实际增量价值 | 指标漂移、Token 消耗比、成功率 | 终止上线，记录差异 |
| 第三级：Policy 宪法否决 | 确保自修改不偏离核心原则 | 语义一致性、不可变规则冲突 | 立即否决，强惩罚信号 |
| 第四级：自动回滚 | 故障后的瞬时状态恢复 | RTO（恢复时间目标）、状态连续性 | 回滚至 Checkpoint |

### 6.2.1 第一级：沙箱验证

第一层负责回答"候选逻辑能否在隔离环境中安全执行"。它主要拦截：

- 非法系统调用
- 越权文件访问
- 未授权网络出站
- 无界资源占用
- 隐式依赖宿主环境的代码路径

输入通常是：

- 候选组件实现或局部补丁
- 组件 manifest 的 `safety` 声明
- 运行所需的最小输入样本
- 资源与权限配置

输出通常是：

- `sandbox_status`
- 资源画像（CPU / memory / I/O / syscall）
- 出站连接画像
- 失败原因与风险标签

### 6.2.2 第二级：影子验证与 A/B

第二层负责回答"这次变更在真实任务分布下是否有正增益，且不会在关键指标上回归"。

它的特点是：

- 候选组件进入 `candidate graph`
- 接收与当前 `active graph version` 相同的输入
- 输出只写入 Observability，不触发生产副作用
- 对质量、延迟、成本、失败率做并排比较

第二层是防止"安全但无效"或"局部有效但整体退化"的关键环节。

### 6.2.3 第三级：宪法层策略审查

第三级负责回答"即便技术上可行，这次修改是否违反系统的根本原则"。

这层不是简单的 if/else 规则集合，而是 **constitutional layer**：

- 处理 protected components 的变更请求
- 解释 mutation proposal 的意图与影响面
- 对 capability、slot rebinding、budget、身份、隐私与审计要求做统一判断
- 对高风险动作要求人类审批、签名或更高等级执行环境

这层是治理平面的"主权边界"。如果没有宪法层，Optimizer 可以逐步侵蚀自身的约束条件。

### 6.2.4 第四级：观察窗口与自动回滚

第四级负责回答"上线后如果出现退化，系统能否及时发现并恢复"。

这一层与前三层不同，它面对的是 **真实运行态**：

- 候选图切流后进入 `observation window`
- 监控 `performance_vector`、错误率、资源尖峰、审计异常
- 若退化超阈值，则回滚到 `rollback target`
- 若同类提案连续失败，则写入 dead-end 记忆，降低重复尝试概率

### 6.2.5 四级链路总表

| 层级 | 关注问题 | 主要输入 | 主要输出 |
| --- | --- | --- | --- |
| L1 沙箱验证 | 能否安全执行 | 代码/补丁、权限配置 | `sandbox_status`, risk tags |
| L2 影子验证 | 是否带来增益 | candidate graph, shadow traffic | metric delta, regression report |
| L3 宪法审查 | 是否允许上线 | mutation proposal, invariants | allow / deny / escalate |
| L4 观察回滚 | 上线后是否稳定 | live metrics, audit events | stable / rollback / dead-end |

---

## 6.3 沙箱分层与当前实现边界

针对 Agent 生成并执行代码的场景，文档中的三级沙箱架构（V8/WASM → gVisor → Firecracker）仍然是**目标架构**。当前 MHE 已落地的是 `sandbox_tiers.py`、`sandbox_validator.py` 等分层与门控抽象，可表达 tier、风险与验证顺序，但尚未实现完整的容器 / 微虚机运行时编排平台。

### 6.3.1 三级沙箱对比

| 维度 | 第一层：V8/WASM | 第二层：gVisor | 第三层：Firecracker |
|---|---|---|---|
| **隔离强度** | Capability-based 细粒度权限 | 用户态内核（Sentry）拦截 syscall | 基于 KVM 的极简虚拟机 |
| **启动延迟** | < 1ms | ~50ms | 30-150ms（pre-warmed 可降至 30ms） |
| **资源占用** | 几 MB | ~100MB | ~128MB 起步 |
| **攻击面** | 极小（仅 Host Function） | 中（~200 syscall 实现） | 极小（仅 5 个虚拟设备） |
| **适用场景** | 简单逻辑变更、元数据处理、XML 配置校验 | Python 脚本执行、数据处理任务 | 网络请求、第三方二进制包、长期运行任务 |
| **I/O 控制** | 仅允许通过指定 Host Function | 挂载只读 Python 标准库镜像 | 默认 `--network=none`，CoW 文件系统 |
| **语言支持** | WASM 编译目标语言 | Python（无复杂 C 扩展）、Go | 完整 Linux 运行时 |

### 6.3.2 第一层：快速筛选（V8 Isolates / WASM）

```yaml
# V8/WASM 沙箱配置示例
sandbox:
  tier: fast_filter
  runtime: wasmtime    # 或 v8_isolates
  limits:
    heap_memory: 128MB
    execution_timeout: 5s
    max_syscalls: none  # 禁用所有非必要 syscall
  host_functions:
    - log_output         # 允许日志输出
    - read_config_param  # 允许读取配置参数
  disallowed:
    - network_access
    - filesystem_write
    - subprocess_spawn
```

### 6.3.3 第二层：通用隔离（gVisor / Kata Containers）

```yaml
# gVisor 沙箱配置示例
sandbox:
  tier: general_isolation
  runtime: runsc        # gVisor 运行时
  image: python:3.12-slim-readonly
  limits:
    memory: 512MB
    cpu_quota: 0.5      # 50% CPU
    execution_timeout: 60s
  filesystem:
    python_stdlib: readonly
    working_dir: tmpfs   # 临时文件系统，执行完毕即消失
  network:
    policy: whitelist
    allowed_endpoints:
      - api.internal-service:443
```

### 6.3.4 第三层：深度隔离（Firecracker MicroVMs）

```yaml
# Firecracker 沙箱配置示例
sandbox:
  tier: deep_isolation
  runtime: firecracker
  vm:
    vcpu_count: 1
    mem_size_mib: 512
  boot:
    mode: pre_warmed_snapshot  # 预热快照，启动 ~30ms
  network:
    mode: none                 # 默认无网络
    proxy:
      enabled: true
      allowed_hosts:
        - api.trusted-endpoint.com
  disk:
    type: cow                  # 写时复制
    base_image: /snapshots/base-python-3.12
    max_size_mib: 256
    cleanup: immediate         # 执行完毕立即擦除
  devices:
    - console
    # 仅 5 个虚拟设备：console, network, block, vsock, rtc
```

### 6.3.5 沙箱层级选择策略

```python
def select_sandbox_tier(task: SandboxTask) -> str:
    """根据任务特征自动选择沙箱隔离层级。"""
    if task.code_complexity == "trivial" and not task.requires_network:
        if task.estimated_runtime_ms < 5000:
            return "fast_filter"       # V8/WASM
    if task.requires_c_extensions or task.requires_stdlib:
        if not task.requires_network and not task.installs_packages:
            return "general_isolation" # gVisor
    return "deep_isolation"            # Firecracker

    # 高风险标记直接使用最深层级
    if task.risk_flags & (RISK_NETWORK | RISK_INSTALL | RISK_LONG_RUNNING):
        return "deep_isolation"
```

### 6.3.6 分层隔离原则

| 原则 | 说明 |
| --- | --- |
| 低风险优先轻量隔离 | 降低验证延迟，提高样本效率 |
| 高风险强制深隔离 | 涉及网络、依赖安装、长时执行必须升档 |
| 默认 deny by default | 网络、写文件、进程派生默认拒绝 |
| 与 manifest 对齐 | 组件 `safety.sandbox_level` 必须可审计 |

---

## 6.4 宪法层：Policy Constitutional Layer

Policy 组件作为系统的"宪法层"，是独立于 Optimizer 的策略评估支柱。其核心设计原则：**Policy 的安全等级必须高于 Optimizer**。如果 Optimizer 能够修改 Policy，治理机制将彻底崩溃。

### 6.4.1 独立运行时推荐

> **实现对齐说明（当前 MHE）**：当前 `policy` 能力主要以 reviewer、gate、hooks 的库级机制存在，尚未以独立进程 / Git 锁定仓 / HSM 签名的完整独立控制面形态落地。

| 设计维度 | 推荐方案 | 理由 |
|---|---|---|
| **进程隔离** | Policy 不与 Task-Agent 共享 Pod 或进程空间 | 防止 Agent 进程级别的逃逸影响 Policy |
| **存储隔离** | Policy 的 XML 配置存储在具备版本锁定的 Git 仓库中 | 防止 Optimizer 直接篡改配置文件 |
| **签名保护** | Policy 配置变更需经过 HSM 背书的签名验证 | 密码学级别的不可伪造性 |
| **访问控制** | 任何对 Policy 的修改必须经过人工"跳板机"审核 | 禁止 Agent 自动修改 Policy |
| **独立审计** | Observability 维护与 Memory 隔离的审计日志 | 审计日志对 Optimizer 不可写 |

```yaml
# Policy 独立运行时配置示例
policy_runtime:
  process:
    isolation: dedicated_pod
    read_only_root_fs: true
  storage:
    type: git_repo
    branch: policy-lock
    signing:
      algorithm: ed25519
      require_multisig: true    # 至少 2 人签名
      hsm_backed: true
  audit:
    log_path: /var/log/policy-audit/
    optimizer_writable: false
    retention: permanent
```

### 6.4.2 宪法层的核心责任

| 责任 | 说明 |
| --- | --- |
| 保护受保护组件 | `policy.primary`、身份根、关键 `evaluation.loop_guard` 默认不可自动覆盖 |
| 审查结构性变更 | slot rebinding、capability 替换、graph cutover 必须先过宪法层 |
| 控制危险权限 | 文件删除、网络出站、敏感工具调用需要高等级授权 |
| 保持审计连续性 | 未产生日志证据的变更不得提交 |
| 决定升级路径 | 普通 allow / deny 之外，还要支持 escalate to human |

### 6.4.3 宪法层判断顺序

```
proposal received
  -> classify risk
  -> check protected components
  -> evaluate invariants
  -> verify evidence prerequisites
  -> emit allow / deny / escalate / allow-with-constraints
```

### 6.4.4 决策语义建议

| 决策 | 含义 |
| --- | --- |
| `allow` | 允许进入后续 staged lifecycle |
| `allow_with_constraints` | 允许，但收紧预算、沙箱级别或观察窗口 |
| `deny` | 拒绝本次提案 |
| `escalate` | 需人工审批或签名 |
| `freeze_path` | 将某优化路径临时冻结，防止连续探测 |

---

## 6.5 治理不变量模板库

安全治理不能只依赖自由文本规则。Meta-Harness 需要一个可执行的 **invariant library**，用于静态校验、动态监控和回滚判断。

### 6.5.1 不变量分类

| 类别 | 作用 |
| --- | --- |
| 结构不变量 | 保证组件图、contracts、slot 绑定的基本一致性 |
| 资源不变量 | 保证 CPU、memory、latency、budget 不越界 |
| 安全不变量 | 保证 secret、网络、文件、权限边界不被突破 |
| 治理不变量 | 保证 protected components、审计链和审批链有效 |
| 领域不变量 | 针对科研、金融等特定任务增加额外约束 |

### 6.5.2 推荐最小不变量集

| ID | 不变量 | 说明 |
| --- | --- | --- |
| `I-01` | required inputs complete | 所有 `required` 输入必须被满足 |
| `I-02` | protected slot immutable-by-default | `policy.primary` 等受保护位点不可自动重绑 |
| `I-03` | audit before commit | 没有 evidence object 不得提交 graph cutover |
| `I-04` | budget hard ceiling | 单轮自增长不可突破预算上限 |
| `I-05` | egress deny by default | 未声明网络权限即禁止出站 |
| `I-06` | secret non-exfiltration | 不得把 secrets、env vars、token 输出到日志或外部工具 |
| `I-07` | rollback target required | 每次提交前必须存在可恢复版本 |
| `I-08` | loop guard continuity | `evaluation.loop_guard` 的语义不能在未审查下被改变 |

### 6.5.3 不变量的执行位置

| 位置 | 适合执行的不变量 |
| --- | --- |
| 静态验证 | 结构、contract、protected slot、manifest 声明 |
| 沙箱验证 | 文件、网络、syscall、资源约束 |
| 影子验证 | 质量/延迟/成本回归 |
| 观察窗口 | live regression、异常尖峰、熔断条件 |
| 审计查询 | 证据完整性与责任追踪 |

### 6.5.4 通用治理规则

元 Harness 推荐 8 条核心治理规则，分为通用规则（C-01 至 C-05）和科研场景特定规则（R-01 至 R-03）。

| 规则 ID | 规则名称 | 核心逻辑 | 拦截阶段 | 违规后果 |
|---|---|---|---|---|
| **C-01** | 资源硬顶约束 | 单个组件的 CPU 占用率不得连续 5 秒超过 80% 配额 | 运行时 | 强制终止组件并回滚 |
| **C-02** | 影子验证一致性 | 新配置在 A/B 影子测试中的回归通过率必须达到 100% | 链接时（测试后） | 禁止上线 |
| **C-03** | 关键路径不可篡改 | 禁止任何针对 Runtime 和 Policy 模块源码的修改操作 | 预编译 | 立即否决 |
| **C-04** | Token 预算熔断 | 单次自修改循环消耗的 API 成本不得超过预设阈值（默认 $0.50） | 运行时 | 强制终止本轮优化 |
| **C-05** | 隐私泄露阻断 | 严禁 Agent 将沙箱内的环境变量或硬编码 Secret 输出至日志 | 运行时 | 立即否决 + 安全告警 |

### 6.5.5 科研场景特定规则

| 规则 ID | 规则名称 | 核心逻辑 | 拦截阶段 | 违规后果 |
|---|---|---|---|---|
| **R-01** | 数据溯源强制 | 每一个生成的科学模型必须包含指向原始数据集的 PROV-O ID | 预编译 | 禁止注册 |
| **R-02** | 不可重现性警报 | 若自修改导致之前的实验结果无法在 5% 误差内重现，则强制回滚 | 运行时（观察窗口） | 自动回滚 |
| **R-03** | 同行评审模拟 | 新逻辑必须通过"评审 Agent"的模拟批判，得分低于 0.7 则拒绝上线 | 链接时 | 禁止上线 |

### 6.5.6 规则实现骨架

```python
class GovernanceRule(ABC):
    """治理不变量规则的基类。"""

    rule_id: str
    rule_name: str
    rule_type: str  # "universal" 或 "research"
    intercept_phase: str  # "pre_compilation" / "link_time" / "runtime"

    @abstractmethod
    def evaluate(self, context: GovernanceContext) -> RuleResult:
        """评估规则是否被违反。"""
        ...

    @abstractmethod
    def get_veto_signal(self) -> VetoSignal:
        """返回违规时的否决信号。"""
        ...


class ResourceHardCap(GovernanceRule):
    """C-01: 资源硬顶约束。"""

    rule_id = "C-01"
    rule_name = "资源硬顶约束"
    rule_type = "universal"
    intercept_phase = "runtime"

    def __init__(self, cpu_threshold: float = 0.8, duration_sec: float = 5.0):
        self.cpu_threshold = cpu_threshold
        self.duration_sec = duration_sec

    def evaluate(self, context: GovernanceContext) -> RuleResult:
        metrics = context.component_metrics
        over_threshold_duration = metrics.cpu_over_threshold_duration(
            threshold=self.cpu_threshold
        )
        violated = over_threshold_duration > self.duration_sec
        return RuleResult(
            rule_id=self.rule_id,
            passed=not violated,
            details=f"CPU 超过 {self.cpu_threshold*100}% 持续 "
                    f"{over_threshold_duration:.1f}s（阈值 {self.duration_sec}s）"
        )
```

---

## 6.6 间接攻击向量与对策

对 Meta-Harness 来说，最危险的往往不是显式的恶意代码，而是 **indirect attack vectors**：攻击者借助输入、工具、上下文、记忆或优化器行为，诱导系统完成危险变更。

### 6.6.1 主要间接攻击向量

| 攻击向量 | 描述 | 典型风险 |
| --- | --- | --- |
| 提示词/配置注入 | 通过任务输入诱导 Optimizer 或 Planner 修改安全边界 | 删除 guard、放宽限制 |
| 污染记忆 | 把伪造"经验"写入 Memory，影响后续 proposal | 错误归因、重复危险路径 |
| 工具输出污染 | 外部工具返回恶意 payload，诱导系统执行下一步危险操作 | 间接命令执行、错误 patch |
| 审计规避 | 试图让系统在不记录证据的情况下完成修改 | 无法追责与回滚 |
| 渐进式权限侵蚀 | 多轮小改动逐步削弱宪法层、sandbox 或预算规则 | 治理失效 |
| Shadow 污染 | 候选图在影子环境中读取了生产不该共享的副作用状态 | 验证结果失真 |

### 6.6.2 对策矩阵

| 攻击向量 | 主要对策 |
| --- | --- |
| 提示词/配置注入 | 输入归一化、proposal diff explain、constitutional review |
| 污染记忆 | memory provenance、只读证据区、失败路径降权 |
| 工具输出污染 | tool result schema、taint tags、二次 validation |
| 审计规避 | audit-before-commit invariant、Merkle audit chain |
| 渐进式权限侵蚀 | protected components、policy self-integrity check、human escalation |
| Shadow 污染 | 严格副作用隔离、shadow dataset snapshot、no-write shadow policy |

### 6.6.3 "间接攻击"为什么难

它难在：

- 单步动作看起来都"合理"
- 每一步都可能通过局部校验
- 风险在多轮优化后才显现
- 攻击路径可能藏在 Memory、Observability、ToolHub 或 Optimizer 的耦合处

因此治理系统不能只检查单次 proposal，还要检查 **路径级趋势**：例如连续多轮是否都在削弱 guard、放宽预算或回避审计。

### 6.6.4 完整性哈希与受保护组件

对 Policy、Evaluation 和 Identity 的核心代码维护不可变的校验和：

```python
PROTECTED_COMPONENTS = ["Policy", "Identity", "Evaluation"]

def compute_integrity_hash(component_id: str) -> str:
    """计算受保护组件的 SHA-256 完整性哈希。"""
    code_path = f"components/{component_id}/"
    hasher = hashlib.sha256()
    for file in sorted(Path(code_path).rglob("*.py")):
        hasher.update(file.read_bytes())
    return hasher.hexdigest()

def verify_integrity(component_id: str) -> bool:
    """验证组件代码是否被篡改。"""
    current = compute_integrity_hash(component_id)
    stored = load_stored_hash(component_id)  # 从签名服务加载
    if current != stored:
        alert_security(f"完整性校验失败: {component_id}")
        return False
    return True
```

---

## 6.7 Guard / Mutate / Reduce 三类治理 Hooks

前文已经建立 staged lifecycle，本章进一步把治理扩展点固定成三类关键 hook：`Guard`、`Mutate`、`Reduce`。这三类 hook 是 Policy / Governance 与其它 core components 的标准交互面。

### 6.7.1 Guard hooks

`Guard` 用于拦截、否决、升级。

适用节点：

- `BEFORE_REGISTER_COMPONENT`
- `BEFORE_ASSEMBLE_GRAPH`
- `BEFORE_ACTIVATE_CANDIDATE`
- `BEFORE_COMMIT_GRAPH`
- `BEFORE_TOOL_CALL`
- `BEFORE_STATE_MIGRATION`

`Guard` 的返回值应支持：

- allow
- deny
- escalate
- allow_with_constraints

```python
@policy_hook(event="pre_operation")
async def guard_sensitive_operation(operation: Operation) -> GuardResult:
    """在敏感操作执行前进行拦截检查。"""
    if operation.type in SENSITIVE_OPERATIONS:
        approval = await policy_layer.request_approval(operation)
        if not approval.granted:
            return GuardResult(blocked=True, reason=approval.reason)
    return GuardResult(blocked=False)
```

### 6.7.2 Mutate hooks

`Mutate` 用于在不改变主意图的前提下补充约束、标签或默认值。

典型用途：

- 自动把高风险 proposal 提升到更高沙箱级别
- 给 candidate graph 增加 `risk_tags`
- 给 observation window 增加更严格阈值
- 给 shadow 验证补充额外基线任务集

```python
@policy_hook(event="during_operation")
async def mutate_network_request(request: NetworkRequest) -> NetworkRequest:
    """在网络请求发送前动态修改其参数。"""
    request.headers["X-Harness-Audit-ID"] = generate_audit_id()
    if request.url.startswith("http://"):
        request.url = request.url.replace("http://", "https://")
    await rate_limiter.acquire(request.destination)
    return request
```

### 6.7.3 Reduce hooks

`Reduce` 用于聚合多路评估结果，把分散的证据收束成一个最终决策上下文。

典型输入包括：

- sandbox report
- shadow metric delta
- invariant violations
- human review signal
- rollback risk estimate

典型输出包括：

- final risk score
- commit recommendation
- required observation window
- dead-end probability

```python
@policy_hook(event="post_operation")
async def reduce_operation_result(result: OperationResult) -> None:
    """在操作完成后进行事后审计。"""
    audit_trail.record({
        "operation": result.operation_type,
        "component": result.component_id,
        "duration_ms": result.duration_ms,
        "success": result.success,
        "token_consumed": result.token_count,
    })
    if not result.success:
        circuit_breaker.record_failure(result.component_id)
        if circuit_breaker.is_open(result.component_id):
            await rollback_manager.trigger_rollback(
                component_id=result.component_id,
                reason="连续失败触发熔断"
            )
```

### 6.7.4 hooks 总表

| Hook 类型 | 输入 | 作用 | 输出 |
| --- | --- | --- | --- |
| `Guard` | proposal / event / action | veto、升级、约束 | allow / deny / escalate |
| `Mutate` | proposal context | 附加限制与标签 | enriched proposal |
| `Reduce` | multi-source reports | 汇聚证据 | final decision context |

### 6.7.5 钩子注册与执行顺序

```python
class PolicyHookDispatcher:
    """治理事件钩子分发器。"""

    def __init__(self):
        self._guards: list[GuardHook] = []
        self._mutators: list[MutateHook] = []
        self._reducers: list[ReduceHook] = []

    def register(self, hook_type: str, hook_fn: Callable) -> None:
        """注册治理钩子。"""
        match hook_type:
            case "guard":  self._guards.append(hook_fn)
            case "mutate": self._mutators.append(hook_fn)
            case "reduce": self._reducers.append(hook_fn)

    async def dispatch(self, event: GovernanceEvent) -> EventResult:
        """按顺序执行钩子链。"""
        # Phase 1: Guard - 前置拦截
        for guard in self._guards:
            result = await guard(event.operation)
            if result.blocked:
                return EventResult(blocked=True, reason=result.reason)

        # Phase 2: Mutate - 参数修改
        mutated_operation = event.operation
        for mutator in self._mutators:
            mutated_operation = await mutator(mutated_operation)

        # Phase 3: Execute - 执行操作
        result = await execute(mutated_operation)

        # Phase 4: Reduce - 事后审计
        for reducer in self._reducers:
            await reducer(result)

        return EventResult(blocked=False, result=result)
```

---

## 6.8 治理接入 staged lifecycle 的位置

治理层不能是图切换之后才出现的"补丁逻辑"，而应嵌入整个 staged lifecycle。

```
discover
  -> validate static
  -> guard(register)
  -> assemble candidate graph
  -> mutate(candidate policy/sandbox tags)
  -> sandbox validation
  -> shadow validation
  -> reduce(reports)
  -> guard(commit)
  -> activate candidate
  -> observe live window
  -> rollback or stabilize
```

### 6.8.1 关键事件建议

| 事件 | 说明 |
| --- | --- |
| `BEFORE_REGISTER_COMPONENT` | 对 manifest 与来源做最早期审查 |
| `AFTER_STATIC_VALIDATE` | 补充风险标签和默认治理策略 |
| `BEFORE_SANDBOX_EXECUTE` | 根据风险选择隔离层 |
| `AFTER_SHADOW_VALIDATE` | 聚合影子结果并决定是否进入 commit |
| `BEFORE_COMMIT_GRAPH` | 最后 veto 点 |
| `AFTER_COMMIT_GRAPH` | 写审计与观察窗口配置 |
| `ROLLBACK_TRIGGERED` | 记录失败原因并更新 dead-end memory |

---

## 6.9 protected components 与权限边界

没有 protected components，治理几乎不可能稳定。建议默认把以下对象纳入 protected set：

| 对象 | 原因 |
| --- | --- |
| `policy.primary` | 决定允许什么变更 |
| 身份/授权根能力 | 决定谁能发起、批准、执行变更 |
| `evaluation.loop_guard` 核心逻辑 | 决定何时停止或回滚 |
| 审计链完整性模块 | 决定是否还有可信证据 |

对 protected components 的建议规则：

- 不能由普通 `Optimizer` 直接重绑
- 必须要求人工审批、签名或独立治理通道
- 任何 related diff 都应强制进入更长 `observation window`
- 必须生成更细粒度 evidence object

---

## 6.10 与其它核心组件的接口关系

安全治理不是孤立模块，它必须与前几章定义的组件清晰协作。

| 组件 | 交互方式 |
| --- | --- |
| `Optimizer` | 接收 proposal，返回 allow/deny/escalate 与约束 |
| `ConnectionEngine` | 在 graph cutover 前提供最终 veto |
| `Observability` | 写入审计记录、风险标签、回滚原因 |
| `Memory` | 记录 dead-end 路径、已知危险模板、审批历史 |
| `Evaluation` | 获取 loop guard 和 regression 指标 |
| `ToolHub` | 对敏感工具调用执行 runtime guard |

---

## 6.11 小结

本章系统阐述了元 Harness 的安全控制与治理体系：

1. **四级安全链路** 提供递进式防护，从隔离验证到事后回滚形成完整的安全闭环
2. **三级沙箱架构** 根据风险等级自动选择隔离深度，在安全性与性能之间取得平衡
3. **Policy 宪法层** 通过独立运行时、多点拦截和治理不变量模板库，确保 Optimizer 的自我修改不偏离核心原则
4. **间接攻击防护** 通过完整性哈希、独立审计轨迹和受保护组件标记，应对 Optimizer 可能的间接绕过行为
5. **Guard / Mutate / Reduce 钩子** 提供灵活的事件驱动治理机制
6. **治理 hooks 嵌入 staged lifecycle**，使安全审查与图切换无缝结合

一句话概括：**Meta-Harness 的安全控制不是单点"审批器"，而是由四级安全链路、宪法层策略、不变量库、分级沙箱与治理 hooks 共同构成的控制平面。**

---

## 6.12 落地建议

按实施顺序，治理层最值得先做的是以下六件事：

| 优先级 | 建议 |
| --- | --- |
| P0 | 固定四级安全链路与关键事件 |
| P0 | 实现 `policy.primary` 的 protected 机制 |
| P0 | 冻结最小 invariant library（I-01 至 I-08） |
| P1 | 实现 sandbox ladder 与风险映射规则 |
| P1 | 实现 `Guard / Mutate / Reduce` hooks |
| P2 | 增加路径级趋势分析，防御渐进式权限侵蚀 |
