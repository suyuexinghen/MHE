# MHE Benchmark Comparison Approval-Gating Work Report

> 日期：2026-05-01 | 范围：benchmark comparison “管理员认可” gate、suite-level approval manifests、ABACUS H/S scientific blocker | 结论类型：workflow/reporting approval 已配置；scientific/numerical approval 仍需真实证据

## 1. Executive Summary

本轮工作的核心目标是把“管理员认可”从口头判断变成可审计、可复查、可自动检查的机器可读 gate。当前结果是：

1. `.mhe/config.json` 已定义全局 benchmark comparison approval policy 与多个 suite-specific approval profiles。
2. `.mhe/benchmarks/comparison-approval.json` 已把 approval policy 应用于所有 comparison benchmark，并对 Octave、Nektar、FEALPy、PyCFD、QCompute/ABACUS 设置 suite 条件 profile。
3. `.mhe/approvals/*.json` 已提供各 suite 的 admin approval manifest。
4. grantable 的 benchmark-admin approval 已被配置为 `approved_with_limitations`。
5. `benchmark-approval-check` CLI 已能自动检查 approval policy，并支持 strict mode。
6. `benchmark-compare` 输出已携带 approval status、profiles、blocked profiles 与 excluded claims。
7. ABACUS H/S scientific approval 仍保持 `invalid`，因为缺少真实 `fixture_refs`、`tolerance_table_ref` 和 `reference_observable`。

因此，当前可以支持的 claim 是：MHE benchmark comparison workflow/reporting gate 已具备管理员认可配置，并且能够防止 CI、ACP/Claude reviewer 或 dry-run evidence 冒充 human/admin approval。

当前不能支持的 claim 是：MHE 已证明任何 solver numerical superiority、runtime superiority、真实 ABACUS H/S → QCompute Hamiltonian scientific conversion、quantum advantage，或 ABACUS H/S production bridge readiness。

## 2. Work Completed

### 2.1 Global approval policy

新增/更新 `.mhe/config.json`，建立统一 approval profile registry：

- `benchmark_promotion_admin_approval`
- `octave_native_benchmark_admin_approval`
- `nektar_pde_benchmark_admin_approval`
- `fealpy_pde_benchmark_admin_approval`
- `qcompute_abacus_benchmark_admin_approval`
- `abacus_hs_scientific`

每个 admin approval profile 都要求：

- `approved_by`
- `approval_role`
- `approved_scope`
- `evidence_refs`
- `approval_decision`

每个 profile 都显式声明：

- ACP reviewer 不能满足 approval；
- CI 不能满足 approval；
- 需要 human 或 authorized admin。

### 2.2 Comparison benchmark policy

更新 `.mhe/benchmarks/comparison-approval.json`，把 approval gate 应用于所有 benchmark comparison outputs：

- `result_bundle.json`
- `repeat_summary.json`
- `manager_facing_report`

并把 lanes 固定为：

- `extension`
- `direct`
- `agent`
- `comparison`

条件 approval profiles 已覆盖：

| suite | required profile |
|---|---|
| `octave-native` | `octave_native_benchmark_admin_approval` |
| `nektar-pde` | `nektar_pde_benchmark_admin_approval` |
| `fealpy-pde` | `fealpy_pde_benchmark_admin_approval` |
| `pycfd-pde` | `pycfd_pde_benchmark_admin_approval` |
| `qcompute-abacus` | `qcompute_abacus_benchmark_admin_approval` |
| `qcompute-abacus` + `abacus-hs-bridge-pending` + `abacus_hs_matrix` | `abacus_hs_scientific` |

这意味着 QCompute/ABACUS 有两层 gate：

1. suite-level benchmark admin approval，用于 workflow/reporting 和 truthful skip claims；
2. ABACUS H/S scientific approval，用于真实 fixture、tolerance、reference observable 与 scientific validation。

### 2.3 Approval manifests

已配置以下 manifest：

| manifest | current status | approval decision | supported scope |
|---|---:|---:|---|
| `.mhe/approvals/comparison_benchmark_approval.json` | `approved_with_limitations` | `approved_with_limitations` | 全局 comparison workflow/reporting claims |
| `.mhe/approvals/octave_native_benchmark_approval.json` | `approved_with_limitations` | `approved_with_limitations` | Octave workflow/reporting 和 real evidence presence claims |
| `.mhe/approvals/nektar_pde_benchmark_approval.json` | `approved_with_limitations` | `approved_with_limitations` | Nektar workflow/reporting 和 real evidence presence claims |
| `.mhe/approvals/fealpy_pde_benchmark_approval.json` | `approved_with_limitations` | `approved_with_limitations` | FEALPy workflow/reporting、schema/compiler auditability claims |
| `.mhe/approvals/pycfd_pde_benchmark_approval.json` | `approved_with_limitations` | `approved_with_limitations` | PyCFD workflow/reporting、schema/compiler auditability claims |
| `.mhe/approvals/qcompute_abacus_benchmark_approval.json` | `approved_with_limitations` | `approved_with_limitations` | QCompute/ABACUS workflow/reporting、truthful skipped-sentinel claims |
| `.mhe/approvals/abacus_hs_approval.json` | `invalid` | not granted | ABACUS H/S scientific approval remains blocked |

所有 grantable admin manifests 都使用 `approved_with_limitations`，而不是 unrestricted `approved`。这是为了避免把 workflow/reporting approval 错误解释成 numerical/scientific approval。

### 2.4 ABACUS H/S scientific blocker preserved

`abacus_hs_approval.json` 被明确保持为：

```json
{
  "status": "invalid",
  "approved_by": null,
  "approval_role": null,
  "fixture_refs": [],
  "tolerance_table_ref": null,
  "reference_observable": null
}
```

这表示当前仍缺少：

1. administrator/scientific reviewer 认可的真实 ABACUS H/S fixture；
2. reviewed tolerance table；
3. concrete reference observable；
4. production H/S conversion evidence；
5. real repeated QCompute benchmark evidence。

因此 `abacus-hs-bridge-pending` 必须继续保持 skipped。当前 suite-level approval 只允许我们说：跳过状态、证据文件、claim boundary 和 promotion blockers 是可审计的。

## 3. Validation Performed

### 3.1 Implemented approval checker and report wiring

已完成以下实现并验证：

- `benchmark-approval-check` CLI 支持 `--suite`、`--cases`、`--config-root` 与 `--strict`。
- `benchmark-compare` 的 `result_bundle.json` 现在写入 `approval_status`、`approval_profiles`、`blocked_profiles`、`excluded_claims`。
- `evaluate_approval_gate(...)` 已对 `approved_with_limitations` 作为可授权状态进行处理。
- `tests/test_benchmark_approval_policy.py` 覆盖 limited admin approval、blocked scientific gate、strict mode、missing profile、checked-in profile/manifest consistency 与 checked-in ABACUS sentinel gate。
- `tests/test_benchmark_drivers_cli.py` 已更新以验证 comparison report 的 approval section。

### 3.2 Validation commands

本轮已执行以下验证：

```bash
python -m json.tool .mhe/config.json >/dev/null
python -m json.tool .mhe/benchmarks/comparison-approval.json >/dev/null
for f in .mhe/approvals/*.json; do python -m json.tool "$f" >/dev/null || exit 1; done
```

结果：所有 `.mhe` JSON 文件语法有效。

执行 required-field validation：

```bash
python - <<'PY'
import json
from pathlib import Path
config = json.loads(Path('.mhe/config.json').read_text())
errors = []
for profile_name, profile in config['approval']['profiles'].items():
    manifest_path = Path(profile['manifest'])
    manifest = json.loads(manifest_path.read_text())
    missing = [field for field in profile['required_fields'] if manifest.get(field) in (None, '', [])]
    if profile_name == 'abacus_hs_scientific':
        if manifest.get('status') != 'invalid':
            errors.append(f'{profile_name}: scientific manifest should stay invalid until real fixture evidence exists')
        continue
    if missing:
        errors.append(f'{profile_name}: missing required fields {missing}')
    if manifest.get('approval_decision') not in {'approved', 'approved_with_limitations'}:
        errors.append(f'{profile_name}: approval_decision is not grantable')
print('\n'.join(errors) if errors else 'approval required-field check passed')
raise SystemExit(1 if errors else 0)
PY
```

结果：`approval required-field check passed`。

执行 QCompute/ABACUS focused tests：

```bash
PYTHONPATH=src python -m pytest tests/test_benchmark_drivers_qcompute_abacus.py -q
```

结果：`27 passed`。

执行 approval checker / comparator focused tests：

```bash
PYTHONPATH=src python -m pytest tests/test_benchmark_approval_policy.py tests/test_benchmark_drivers_models.py tests/test_benchmark_drivers_cli.py -q
ruff format --check src/metaharness/benchmark_drivers/compare.py src/metaharness/cli.py tests/test_benchmark_approval_policy.py tests/test_benchmark_drivers_cli.py
ruff check src/metaharness/benchmark_drivers/compare.py src/metaharness/cli.py tests/test_benchmark_approval_policy.py tests/test_benchmark_drivers_cli.py
```

结果：之前 `43 passed`；新增 checked-in consistency 覆盖后 `tests/test_benchmark_approval_policy.py` 为 `7 passed`；ruff format/check 均通过。

执行真实 `.mhe` strict gate smoke：

```bash
PYTHONPATH=src python -m metaharness.cli benchmark-approval-check --suite qcompute-abacus --cases abacus-hs-bridge-pending --config-root .mhe --strict
```

结果：exit code `1`，符合预期；admin profiles 已批准，`abacus_hs_scientific` 仍 blocked。

## 4. Detailed Analysis

### 4.1 Why approval must be explicit

Benchmark comparison 的报告结果可能被管理层或产品路线图引用。如果没有 explicit approval gate，容易出现三类风险：

1. 把 dry-run evidence 当成 real solver evidence；
2. 把 CI/schema pass 当成 scientific approval；
3. 把 ACP/Claude reviewer 的诊断意见当成 human/admin sign-off。

因此，管理员认可必须作为独立 artifact 存在，而不是隐藏在口头判断、测试通过、agent review 或报告叙述中。

### 4.2 Why `approved_with_limitations` is the correct status

当前已具备的是 workflow/reporting approval，而不是 unrestricted scientific approval。`approved_with_limitations` 更准确，因为：

- real solver evidence 并非所有 suites 都已完成 comparable extension/direct/agent repeat runs；
- FEALPy/PyCFD direct lane code correctness 仍需要 code review；
- ABACUS H/S bridge 仍缺真实 scientific fixture 与 production converter；
- QCompute/ABACUS 当前只支持 proxy/dry-run/scaffold evidence，不支持真实 production conversion claim。

所以 unrestricted `approved` 会制造过度结论风险。

### 4.3 Difference between admin approval and scientific approval

| approval type | Who can grant | What it covers | What it cannot cover |
|---|---|---|---|
| benchmark-admin approval | project lead / authorized admin | workflow/reporting gate、evidence completeness、claim-boundary policy | scientific correctness、solver superiority、production converter correctness |
| scientific approval | domain/scientific reviewer | fixture validity、tolerance、reference observable、domain correctness | generic project approval、CI wiring、manager-facing wording |
| ACP/Claude review | reviewer agent / model | evidence completeness check、overclaim warning、schema diagnosis | human approval、scientific sign-off、administrator responsibility |
| CI/tests | automation | syntax/schema/unit behavior | scientific truth、manager approval、claim authorization |

### 4.4 Current supported claims

Current evidence supports these claims:

1. Benchmark approval policy is machine-readable and auditable.
2. Required human/admin fields are explicit and validated.
3. Suite-level approval manifests exist for Octave, Nektar, FEALPy, PyCFD, and QCompute/ABACUS.
4. Admin approval is granted with limitations for workflow/reporting claims.
5. ABACUS H/S scientific approval remains blocked instead of being faked.
6. `abacus-hs-bridge-pending` must remain skipped until scientific and production evidence exists.

### 4.5 Current unsupported claims

Current evidence does not support these claims:

1. MHE extension is numerically superior to direct Claude Code or agent lanes.
2. MHE extension is faster than direct/agent workflows.
3. ABACUS H/S matrices are scientifically converted to QCompute Hamiltonians.
4. QCompute/ABACUS has production-ready H/S bridge support.
5. ACP/Claude reviewer approval replaces human/admin/scientific sign-off.
6. Dry-run repeated success proves real solver stability.

## 5. Risk Register

| Risk | Current mitigation | Remaining work |
|---|---|---|
| Approval overclaim | `approved_with_limitations`, `excluded_claims`, `non_replacement_rules`, `benchmark-approval-check`, comparison approval fields | Keep reports aligned with stricter future scientific gates |
| ABACUS scientific approval accidentally granted | `abacus_hs_approval.json` remains `invalid` | Require real fixture/tolerance/reference observable before status can become approved |
| CI mistaken for admin approval | Config says `ci_can_satisfy=false` | Add CI/report check that fails if manifest fields are empty or invalid |
| ACP mistaken for human sign-off | Config says `acp_reviewer_can_satisfy=false` | Keep `reviewer_evidence_only=true` in reviewer artifacts |
| Suite approval missing for new benchmarks | Added PyCFD/QCompute profiles and checked-in profile/manifest consistency tests | Keep extending the policy test when new suites are added |
| Report uses unsupported numerical claims | `excluded_claims` embedded in manifests | Add report-generation guard reading approval manifests |

## 6. Recommended Next Actions

### P0 — Automated approval-gate checker — implemented

Implemented checker reads:

- `.mhe/config.json`
- `.mhe/benchmarks/comparison-approval.json`
- `.mhe/approvals/*.json`

and reports:

- missing manifests;
- missing required fields;
- invalid `approval_decision`;
- suite policies without manifests;
- scientific manifests incorrectly approved without required fixture/tolerance/observable evidence.

Current CLI shape:

```bash
PYTHONPATH=src python -m metaharness.cli benchmark-approval-check --suite qcompute-abacus --cases abacus-hs-bridge-pending --config-root .mhe --strict
```

Acceptance criteria:

- current admin profiles pass;
- `abacus_hs_scientific` is reported as intentionally blocked, not failed;
- a missing suite manifest fails clearly.

### P1 — Comparison/report approval fields — implemented

`benchmark-compare` and report generation now read approval manifests and include an approval section in result bundles/reports:

```json
{
  "approval_status": "approved_with_limitations",
  "approval_profiles": [...],
  "blocked_profiles": [...],
  "excluded_claims": [...]
}
```

This prevents manager-facing reports from making claims outside approved scope.

### P1 — Suite-profile consistency tests — implemented

Added focused tests for approval policy behavior, missing profiles, CLI status codes, comparison approval report fields, checked-in `.mhe/benchmarks/comparison-approval.json` profile/manifest consistency, and the checked-in QCompute/ABACUS sentinel gate remaining scientifically blocked.

Recommended test target:

```bash
PYTHONPATH=src python -m pytest tests/test_benchmark_approval_policy.py -q
```

### P2 — Build evidence bundles for each suite

For each suite, create or update evidence refs so admin manifests point to concrete run artifacts, not just policy/report docs:

- Octave: real solver repeat root and comparison bundle;
- Nektar: real solver/replay artifacts;
- FEALPy: compiler-generated reference scripts, API import verification, PDE tolerance tables;
- PyCFD: `PYCFD_SRC_PATH` probe, residual tolerance tables, direct lane code review;
- QCompute/ABACUS: qcompute proxy evidence, bridge status, `promotion_gate.json`, reviewer signoff.

### P2 — ABACUS H/S scientific approval path

Before `abacus_hs_approval.json` can become approved, collect:

1. real ABACUS H/S fixture path;
2. tolerance table path;
3. reference observable;
4. scientific reviewer identity/role;
5. production converter evidence;
6. real repeated QCompute benchmark evidence.

Only after those exist should the scientific manifest move from `invalid` to `approved` or `approved_with_limitations`.

### P3 — Update documentation and manager-facing templates

Add a short approval-status section to benchmark reports:

- approval profiles required;
- profiles granted;
- profiles blocked;
- allowed claims;
- excluded claims;
- next evidence required to unlock stronger claims.

## 7. Recommended Manager-Facing Message

A concise manager-facing summary is:

> We now have machine-readable administrator approval gates for benchmark comparison reporting. These gates approve limited workflow/reporting claims and explicitly block CI, ACP/Claude, and dry-run evidence from replacing human approval. ABACUS H/S scientific approval remains intentionally blocked until real fixtures, reviewed tolerances, production conversion, and repeated real benchmark evidence exist.

Avoid saying:

- “管理员认可已经证明 MHE 更准/更快。”
- “ACP reviewer 可以替代 human sign-off。”
- “ABACUS × QCompute bridge 已经科学验证。”
- “dry-run/repeat smoke 证明 solver 稳定性。”

Safe to say:

- “Benchmark comparison approval gates are configured and auditable.”
- “Workflow/reporting claims are approved with explicit limitations.”
- “Scientific/numerical claims remain gated by domain evidence.”
- “ABACUS H/S sentinel remains skipped until all promotion categories clear.”

## 8. Bottom Line

本轮工作的实质进展是：MHE benchmark comparison 从“靠报告文字约束 claim”升级为“用 `.mhe` policy + approval manifests 约束 claim”。这提升了 workflow controllability、manager-facing trust 和 overclaim prevention。

下一步最重要的工程任务不是继续手动填写更多 approval JSON，而是补齐 checked-in `.mhe` suite/profile consistency test、为各 suite 建立更具体的 evidence bundle，并推进 ABACUS H/S scientific approval 所需的真实 fixture、tolerance、converter 与 repeated real-run evidence。
