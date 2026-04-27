# 08. 测试与评审

## 8.1 测试策略总览

当前用户向使用入口见 `docs/qcompute-user-manual.md`；能力真实性以本目录的 `qcompute-tested-support-matrix.md` 为准。日常验收优先运行 `examples/qcompute/*.py`，再按支持矩阵选择 focused pytest 或 Quafu gated smoke。

量子计算的测试面临独特的挑战：

1. **真机不可控**：硬件噪声、排队延迟、校准漂移无法在测试中稳定复现
2. **模拟器确定但有限**：无噪声模拟器可以精确断言，但无法覆盖噪声场景
3. **外部依赖真实存在**：pyQuafu 需要有效 token 才能访问真机

因此，QCompute 采用 **分层测试策略**：

```
Layer 1: 单元测试（纯 Python，无外部依赖）
  ├─ contracts 模型序列化/反序列化
  ├─ 验证逻辑（mock artifact → validation report）
  ├─ 策略评估（mock evidence → allow/reject/defer）
  └─ Study 调度逻辑（mock gateway → trial 调度）

Layer 2: 集成测试（Qiskit Aer 模拟器，本地运行）
  ├─ Gateway → ConfigCompiler → Executor(Aer) → Validator 端到端
  ├─ 噪声模型集成测试
  └─ Study 网格搜索（小规模）

Layer 3: 真机冒烟测试（Quafu，需 token，可选）
  ├─ 最小 VQE 电路真机验证
  ├─ 环境探测 + 校准数据读取
  └─ 配额感知调度验证
```

## 8.2 单元测试

### 8.2.1 Contracts 序列化测试

```python
# tests/test_metaharness_qcompute_contracts.py

class TestQComputeContracts:
    def test_experiment_spec_roundtrip(self) -> None:
        spec = QComputeExperimentSpec(
            task_id="test-001",
            mode="simulate",
            backend=QComputeBackendSpec(platform="qiskit_aer", simulator=True),
            circuit=QComputeCircuitSpec(ansatz="vqe", num_qubits=4),
            shots=1024,
        )
        dumped = spec.model_dump_json()
        loaded = QComputeExperimentSpec.model_validate_json(dumped)
        assert loaded.task_id == spec.task_id

    def test_validation_report_issues(self) -> None:
        report = QComputeValidationReport(
            task_id="test-001",
            plan_ref="plan-001",
            artifact_ref="art-001",
            passed=False,
            status=QComputeValidationStatus.BELOW_FIDELITY_THRESHOLD,
            metrics=QComputeValidationMetrics(fidelity=0.85),
        )
        assert not report.passed
        assert report.status == QComputeValidationStatus.BELOW_FIDELITY_THRESHOLD
```

### 8.2.2 Validator 逻辑测试（mock artifact）

```python
class TestQComputeValidator:
    @pytest.fixture
    def validator(self) -> QComputeValidatorComponent:
        return QComputeValidatorComponent()

    def test_validate_completed_run(self, validator, sample_artifact, sample_plan) -> None:
        report = validator.validate(sample_artifact, sample_plan, environment_report=None)
        assert report.passed
        assert report.status == QComputeValidationStatus.VALIDATED

    def test_validate_failed_run(self, validator) -> None:
        artifact = QComputeRunArtifact(
            artifact_id="art-fail",
            plan_ref="plan-001",
            backend_actual="qiskit_aer",
            status="failed",
            error_message="Backend timeout",
        )
        report = validator.validate(artifact, sample_plan(), environment_report=None)
        assert not report.passed
        assert report.status == QComputeValidationStatus.EXECUTION_FAILED
```

### 8.2.3 Policy 门控测试

```python
class TestQComputePolicy:
    def test_allow_when_fidelity_above_threshold(self, policy_engine) -> None:
        evidence = sample_evidence(fidelity=0.99, threshold=0.95)
        decision = policy_engine.evaluate(evidence)
        assert decision.decision == "allow"

    def test_reject_when_precondition_failed(self, policy_engine) -> None:
        evidence = sample_evidence(
            status=QComputeValidationStatus.ENVIRONMENT_INVALID
        )
        decision = policy_engine.evaluate(evidence)
        assert decision.decision == "reject"

    def test_defer_when_noise_impact_high(self, policy_engine) -> None:
        evidence = sample_evidence(noise_impact_score=0.8)
        decision = policy_engine.evaluate(evidence)
        assert decision.decision == "defer"
```

### 8.2.4 校准时效性测试

```python
class TestCalibrationFreshness:
    def test_fresh_calibration_accepted(self) -> None:
        calib = QComputeCalibrationData(
            timestamp=datetime.now(timezone.utc) - timedelta(minutes=30),
            t1_us_avg=50.0, t2_us_avg=30.0,
            single_qubit_gate_fidelity_avg=0.999,
            two_qubit_gate_fidelity_avg=0.99,
            readout_fidelity_avg=0.98,
        )
        assert _check_calibration_freshness(calib) == []  # No issues

    def test_stale_calibration_warns(self) -> None:
        calib = QComputeCalibrationData(
            timestamp=datetime.now(timezone.utc) - timedelta(hours=5),
            t1_us_avg=50.0, t2_us_avg=30.0,
            single_qubit_gate_fidelity_avg=0.999,
            two_qubit_gate_fidelity_avg=0.99,
            readout_fidelity_avg=0.98,
        )
        issues = _check_calibration_freshness(calib)
        assert any("STALE_WARN" in i for i in issues)

    def test_very_stale_calibration_blocks(self) -> None:
        calib = QComputeCalibrationData(
            timestamp=datetime.now(timezone.utc) - timedelta(hours=25),
            t1_us_avg=50.0, t2_us_avg=30.0,
            single_qubit_gate_fidelity_avg=0.999,
            two_qubit_gate_fidelity_avg=0.99,
            readout_fidelity_avg=0.98,
        )
        issues = _check_calibration_freshness(calib)
        assert any("STALE" in i and "STALE_WARN" not in i for i in issues)
```

## 8.3 集成测试（Aer 模拟器）

### 8.3.1 端到端 Bell 态

```python
class TestQComputeEndToEnd:
    @pytest.mark.integration
    async def test_bell_state_simulate(self, gateway: QComputeGatewayComponent) -> None:
        spec = QComputeExperimentSpec(
            task_id="e2e-bell",
            mode="simulate",
            backend=QComputeBackendSpec(platform="qiskit_aer", simulator=True),
            circuit=QComputeCircuitSpec(
                ansatz="custom",
                num_qubits=2,
                openqasm="""
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0], q[1];
measure q -> c;
""",
            ),
            shots=1024,
        )
        bundle = await gateway.run_baseline(spec)
        assert bundle.validation_report.passed
        # Bell 态测量结果应只有 |00⟩ 和 |11⟩
        counts = bundle.run_artifact.counts
        assert counts is not None
        assert set(counts.keys()).issubset({"00", "11"})
```

### 8.3.2 VQE 最小闭环

```python
@pytest.mark.integration
async def test_vqe_h2_minimal(self, gateway: QComputeGatewayComponent) -> None:
    """H2 分子最小基组 VQE 能量计算"""
    spec = QComputeExperimentSpec(
        task_id="vqe-h2",
        mode="simulate",
        backend=QComputeBackendSpec(platform="qiskit_aer", simulator=True),
        circuit=QComputeCircuitSpec(
            ansatz="vqe",
            num_qubits=2,
            repetitions=1,
        ),
        energy_target=-1.137,  # H2 精确基态能量 (Hartree)
        fidelity_threshold=0.95,
        max_iterations=100,
    )
    bundle = await gateway.run_baseline(spec)
    assert bundle.validation_report.passed
    assert bundle.validation_report.metrics.energy is not None
    assert abs(bundle.validation_report.metrics.energy_error) < 0.1
```

### 8.3.3 Quafu Cup 基准测试

Quafu 杯的评估标准（综合考虑保真度、门数量、运行时间）是自动化量子 Agent
的理想基准。以下测试用例参照 Quafu 杯赛题设计：

```python
class TestQComputeQuafuCupBenchmarks:
    @pytest.mark.integration
    async def test_bell_state_fidelity_target(self, gateway: QComputeGatewayComponent) -> None:
        """参照 Quafu 杯：在限制深度内完成 Bell 态制备，保真度 >0.95"""
        spec = QComputeExperimentSpec(
            task_id="quafucup-bell",
            mode="simulate",
            backend=QComputeBackendSpec(platform="qiskit_aer", simulator=True),
            circuit=QComputeCircuitSpec(ansatz="custom", num_qubits=2,
                openqasm='OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\nh q[0];\ncx q[0],q[1];\nmeasure q -> c;\n'),
            shots=1024,
            fidelity_threshold=0.95,
        )
        bundle = await gateway.run_baseline(spec)
        assert bundle.validation_report.passed
        # Quafu Cup metric: depth × SWAP × (1 - fidelity) → lower is better
        score = (bundle.validation_report.metrics.circuit_depth_executed or 0) * \
                (bundle.validation_report.metrics.swap_count_executed or 0) * \
                (1 - (bundle.validation_report.metrics.fidelity or 0))
        assert score < expected_threshold  # Configurable

    @pytest.mark.integration
    async def test_vqe_energy_convergence(self, gateway: QComputeGatewayComponent) -> None:
        """参照 Quafu 杯量子化学赛道：H2 分子 VQE 能量收敛到化学精度"""
        spec = QComputeExperimentSpec(
            task_id="quafucup-vqe-h2",
            mode="simulate",
            backend=QComputeBackendSpec(platform="qiskit_aer", simulator=True),
            circuit=QComputeCircuitSpec(ansatz="vqe", num_qubits=2, repetitions=1),
            energy_target=-1.137,
            fidelity_threshold=0.98,
            max_iterations=100,
        )
        bundle = await gateway.run_baseline(spec)
        # 化学精度 ≤1.6 mHa ≈ 0.0016 Hartree
        assert abs(bundle.validation_report.metrics.energy_error or 999) < 0.01
```

### 8.3.4 Mitiq 错误缓解集成测试

```python
@pytest.mark.integration
async def test_zne_error_mitigation(self, gateway: QComputeGatewayComponent) -> None:
    """验证 ZNE 错误缓解能改善噪声下的能量估计"""
    spec = QComputeExperimentSpec(
        task_id="zne-test",
        mode="simulate",
        backend=QComputeBackendSpec(platform="qiskit_aer", simulator=True),
        circuit=QComputeCircuitSpec(ansatz="vqe", num_qubits=2, repetitions=1),
        noise=QComputeNoiseSpec(model="depolarizing", depolarizing_prob=0.01),
        error_mitigation=["zne"],
        energy_target=-1.137,
        fidelity_threshold=0.90,
    )
    bundle = await gateway.run_baseline(spec)
    # ZNE should improve the energy estimate compared to raw noisy result
    assert bundle.validation_report.metrics.noise_impact_score is not None
    assert bundle.validation_report.metrics.noise_impact_score < 0.5  # ZNE reduces noise impact
```

## 8.4 Mock 后端

为支持无外部依赖的测试，提供 mock 后端适配器：

```python
class MockQuantumBackend:
    """返回确定性结果的 mock 量子后端"""

    def __init__(self, deterministic_counts: dict[str, int]) -> None:
        self._counts = deterministic_counts

    def run(self, circuit, shots: int = 1024) -> dict[str, int]:
        return self._counts
```

Mock 后端用于：
- Validator 逻辑测试（注入特定结果模式）
- Policy 评估测试（控制 evidence 内容）
- Study 调度逻辑测试（快速验证 trial 调度）

## 8.5 Promotion-Readiness 测试

```python
class TestQComputePromotionReadiness:
    def test_validation_report_maps_to_governance(self) -> None:
        """验证 QComputeValidationReport 正确映射到 MHE ValidationIssue"""
        report = QComputeValidationReport(
            task_id="test",
            plan_ref="p-1",
            artifact_ref="a-1",
            passed=False,
            status=QComputeValidationStatus.BELOW_FIDELITY_THRESHOLD,
            metrics=QComputeValidationMetrics(fidelity=0.85),
        )
        issues = map_to_validation_issues(report, fidelity_threshold=0.95)
        assert any(i.blocks_promotion for i in issues)
        assert any(i.code == "QCOMPUTE_FIDELITY_BELOW_THRESHOLD" for i in issues)

    def test_evidence_bundle_provenance_linkage(self) -> None:
        """验证 evidence bundle 的 provenance_inputs 可被引用"""
        bundle = QComputeEvidenceBundle(
            bundle_id="b-1",
            experiment_ref="e-1",
            environment_report=sample_env_report(),
            run_artifact=sample_artifact(),
            validation_report=sample_validation_report(),
            provenance_inputs=["abacus_hamiltonian_art-001"],
        )
        assert "abacus_hamiltonian_art-001" in bundle.provenance_inputs
```

## 8.6 测试覆盖矩阵

| 覆盖维度 | 单元测试 | 集成测试 | 真机烟雾 |
|---------|---------|---------|---------|
| Contracts 序列化 | ✅ | — | — |
| Validator 逻辑 | ✅ | ✅ | ✅ |
| Policy 门控 | ✅ | ✅ | — |
| Study 调度 | ✅ | ✅ | — |
| Gateway 流水线 | — | ✅ | ✅ |
| Aer 模拟器执行 | — | ✅ | — |
| 噪声模型 | — | ✅ | — |
| Quafu 环境探测 | — | — | ✅ |
| Quafu 真机执行 | — | — | ✅ |
| Promotion readiness | ✅ | ✅ | — |
| Governance 适配 | ✅ | ✅ | — |
| 配额感知调度 | ✅ | — | ✅ |
| 校准时效性检查 | ✅ | — | ✅ |
| Mitiq ZNE 集成 | — | ✅ | — |
| Quafu Cup 基准 | — | ✅ | ✅ |
| 轨迹级评分 | ✅ | — | — |
| 配额超限处理 | ✅ | — | — |

## 8.7 示例运行后的反思清单

每次运行 `examples/qcompute/*.py` 或 Quafu gated smoke 后，把终端输出、`Raw output` 和 ArtifactStore JSONL 一起复盘：

- `Backend` / `Mode` 是否符合预期；如果真机检查仍显示 `qiskit_aer` / `simulate`，先确认 `QCOMPUTE_ENABLE_HARDWARE=1`、`Qcompute_Token`、`QCOMPUTE_QUAFU_CHIP` 与配额。
- `Run status`、`Validation`、`Policy decision` 是否同时通过；若为 `defer` / `reject`，先看环境探测、配额快照、保真度阈值与噪声配置。
- Bell counts 是否主要集中在 `00` / `11`；噪声示例是否输出 ZNE / REM details，且 corrected probabilities 合理。
- Study 的 `Best trial payload` 是否只包含可复现实验参数，尤其确认 `shots` 等整数参数未被 agentic 扰动成 float。
- VQE 的 `Energy error` 是否可解释；误差偏大时优先检查 ansatz、active space、mapping、迭代次数和 reference energy。
- Quafu 若被 gated、排队、维护或缺校准，应归类为硬件能力门控，而不是模拟器失败。

这些结论应回写到 backlog：API 诚信、结果质量、硬件可靠性、Study 可用性或文档/示例缺口。

## 8.8 评审检查清单

QCompute 实现的评审应覆盖以下项目：

### 安全性
- [ ] API token 不硬编码在代码或 manifest 中（通过环境变量注入）
- [ ] Validator 不执行外部二进制文件
- [ ] Executor 的 `workspace-write` sandbox 范围仅限 `raw_output_path`
- [ ] 真机配额用尽后不静默降级为模拟器（需显式策略配置）

### 正确性
- [ ] OpenQASM 生成语法合法（通过 Qiskit parser 验证）
- [ ] Transpilation 后的电路保真度不低于原始电路的 90%（有噪声时）
- [ ] `ValidationReport.promotion_ready` 与 `blocks_promotion` 的逻辑一致
- [ ] Study 结果的 Pareto 前沿计算正确

### Governance
- [ ] Validator manifest 的 `safety.protected = true` 已设置
- [ ] `QComputeValidationReport` 正确映射到 MHE `ValidationIssue`
- [ ] `blocks_promotion` 的触发条件覆盖所有不可恢复的失败模式
- [ ] Evidence bundle 的 `provenance_inputs` 完整引用上游 artifact
- [ ] 校准数据超过 24h 是否正确触发 `blocks_promotion=True`

### 可靠性
- [ ] 配额耗尽时的错误消息包含剩余配额和重置时间
- [ ] 真机超时后自动重试机制有上限（防止无限 retry）
- [ ] 环境探测缓存过期时间合理（校准数据 <1h，芯片状态 <5min）
- [ ] Mitiq ZNE 的 `AdaExpFactory` 自适应步数是否合理（默认 steps=5）
- [ ] QSteed VQPU 选择失败时是否正确 fallback 到标准 transpilation
- [ ] 斐波那契轮询是否在最大等待时间后正确超时
