# 05. 安全与治理

## 5.1 安全模型

Octave extension 必须把"运行脚本"视为高风险边界，而不是普通函数调用。

### 5.1.1 首版安全策略

- 默认只允许在 extension-managed workspace 内读写
- 输入资产必须显式声明
- output files 必须显式声明或匹配受限 pattern
- 安全依赖 OS 级隔离（MHE SandboxTier）；静态脚本扫描作为 v2 defense-in-depth
- 不允许未声明网络访问
- 不在 extension 内保存 credentials
- `OctaveValidatorComponent` 建议设为 protected
- manifest 中显式声明 sandbox、credentials 和 workspace-write policy
- 所有 run artifact 都要能追溯到 plan、script hash、input asset hash 与 output hash

### 5.1.2 安全模型演进

| 维度 | v1 | v2 |
|------|-----|-----|
| 脚本执行 | wrapper-first，workspace allowlist | 同左 + static script scanner（编译期检测） |
| 文件系统 | `.runs/` 隔离 | 同左 + 集群共享文件系统权限 |
| 网络 | 默认禁止 | 同左；scheduler adapter 需集群 API 通信（白名单） |
| 状态传递 | 无跨 run 状态 | workspace_ref 仅限同 session / 显式授权 |

## 5.2 Static Script Scanner（v2）

v2 在 compiler 中集成静态脚本扫描器，作为 defense-in-depth 不替代 OS sandbox：

```python
class OctaveSecurityScanner:
    DANGEROUS_PATTERNS = [
        (r'\bsystem\s*\(', "shell_execution"),
        (r'\bunix\s*\(', "shell_execution"),
        (r'!\w', "shell_execution"),
        (r'\burlread\b', "network_access"),
        (r'\burlwrite\b', "network_access"),
        (r'\bweb\b', "network_access"),
        (r'\bpkg\s+install\b', "package_install"),
    ]

    def scan(self, script_content: str) -> SecurityScanReport:
        """Return list of SecurityFinding(code, line, severity, message)."""
```

发现 dangerous patterns 时产出 `ValidationIssue(category=SAFETY, blocks_promotion=True)`。v1 阶段安全仅依赖 OS 级隔离。

## 5.3 MHE 平台集成点

Octave extension 通过以下 MHE 平台服务接入治理体系：

- 使用 `ComponentRuntime.storage_path` 定位 `.runs`
- 使用 `RuntimeServices.artifact_store` 记录 run/validation/evidence snapshot
- 使用 `audit_log` 和 `provenance_graph` 连接 task、plan、artifact、validation
- 对长时间执行或 HPC 后端，后续对齐 `ExecutionLifecycleService`
- 对 resource-sensitive 任务，后续接入 `resource_quota`

## 5.4 Governance Adapter（v2）

v2 实现完整的 `OctaveGovernanceAdapter`，遵循 DeepMD/QCompute pattern：

```python
class OctaveGovernanceAdapter:
    def __init__(self, *, session_id: str | None = None, actor: str = "octave_governance"):
        self.session_id = session_id
        self.actor = actor

    def build_core_validation_report(self, validation, policy) -> ValidationReport:
        """Merge validation.issues + policy gate issues. Aggregate blocks_promotion."""

    def build_candidate_record(self, bundle, policy, *, snapshot=None) -> CandidateRecord:
        """Build candidate record for graph promotion."""

    def build_session_events(self, bundle, policy) -> list[SessionEvent]:
        """Emit CANDIDATE_VALIDATED, SAFETY_GATE_EVALUATED, CANDIDATE_REJECTED events."""

    def emit_runtime_evidence(self, bundle, policy, *, session_store, audit_log, provenance_graph) -> dict:
        """Full provenance + audit recording via runtime services."""

    def record_with_artifact_store(self, bundle, policy, *, session_store, audit_log, provenance_graph, artifact_store) -> dict:
        """Record evidence + artifact snapshot via ExecutionEvidenceRecorder."""
```

## 5.5 治理事件总线集成

MHE EventBus 提供 4 个事件常量。Octave 扩展在以下阶段对接：

| 阶段 | 事件 | 触发条件 |
|------|------|----------|
| validation 完成 | `BEFORE_COMMIT_GRAPH` | evidence bundle 完整，等待 governance gate |
| graph 提交 | `AFTER_COMMIT_GRAPH` | candidate graph 通过验证并提交 |
| candidate 被拒 | `CANDIDATE_REJECTED` | validation 或 policy 判定 blocked |
| candidate 搁置 | `CANDIDATE_DEFERRED` | evidence 不完整或 warning suspicious |

## 5.6 Protected Component

`OctaveValidator` 设为 protected component：
- slot `octave_validator.primary` 不能被未授权实现覆盖
- validator 是 evidence pipeline 的关键节点，其判定直接影响 promotion
- manifest 中 `safety.protected = true`

## 5.7 Sandbox Tier

所有 Octave 组件默认运行在 `standard` sandbox tier：
- 文件系统访问限制在 workspace 目录
- 网络访问默认禁止
- 进程创建受限于 `octave-cli` subprocess
- 后续可配置为 `strict` tier（额外限制 resource quota）
