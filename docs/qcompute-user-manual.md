# QCompute User Manual

QCompute is the Meta-Harness Engine quantum-computing extension. Use it to run small quantum circuits, evaluate noisy simulator behavior, explore parameter studies, run H2 VQE demos, and collect governance-ready evidence.

This manual is intentionally user-facing. Architecture and long-form design details live in `docs/wiki/meta-harness-engineer/qcompute-engine-wiki/`.

## What You Can Do

| Goal | Entry Point | Default Backend | Output |
|---|---|---|---|
| Run a Bell-state baseline | `examples/qcompute/bell.py` | Qiskit Aer | counts, validation, policy, artifact snapshots |
| Compare noise mitigation | `examples/qcompute/noise_mitigation.py` | Qiskit Aer | noisy counts, ZNE/REM metadata |
| Sweep parameters | `examples/qcompute/study.py` | Qiskit Aer | trials, best trial, domain payload |
| Run H2 VQE | `examples/qcompute/vqe.py` | Qiskit Aer | energy, energy error, raw output |
| Try Quafu hardware | `examples/qcompute/bell.py` with hardware env vars | Quafu/Baihua | gated hardware smoke output |

Generated demo artifacts are written under `.demo-runs/qcompute/`.

## Install Dependencies

Required simulator path:

```bash
pip install qiskit qiskit-aer
```

Optional backends:

```bash
pip install pennylane      # PennyLane simulator path
pip install quarkstudio    # Quafu hardware path
```

For Quafu hardware, set the token in your shell or `.env`:

```bash
export Qcompute_Token="your_token_here"
```

Hardware is never used by default. You must opt in explicitly:

```bash
export QCOMPUTE_ENABLE_HARDWARE=1
export QCOMPUTE_QUAFU_CHIP=Baihua
```

## Quick Start

Run the Bell-state demo:

```bash
python examples/qcompute/bell.py
```

Expected simulator output includes:

```text
Backend: qiskit_aer
Mode: simulate
Run status: completed
Counts: {'00': ..., '11': ...}
Validation: converged
Policy decision: allow
Raw output: .demo-runs/qcompute/bell/...
Artifact snapshots: .demo-runs/qcompute/bell/artifact-snapshots.jsonl
```

If `Backend` is `quafu` and `Mode` is `run`, the demo is using the hardware path. If it still shows `qiskit_aer`, hardware was not enabled or prerequisites were missing.

## Runnable Examples

### Bell Baseline

```bash
python examples/qcompute/bell.py
```

Use this first. It exercises the full baseline pipeline:

1. environment probe
2. circuit compilation
3. execution
4. validation
5. evidence and policy reporting
6. optional ArtifactStore snapshots

### Noise Mitigation

```bash
python examples/qcompute/noise_mitigation.py
```

This runs a noisy Bell-style circuit with ZNE and REM enabled. Check the printed mitigation details:

- `zne.applied`
- `rem.applied`
- `overhead.total_executor_calls`
- corrected counts / probabilities

### Parameter Study

```bash
QCOMPUTE_STUDY_MAX_TRIALS=2 python examples/qcompute/study.py
```

Choose a strategy with:

```bash
QCOMPUTE_STUDY_STRATEGY=grid python examples/qcompute/study.py
QCOMPUTE_STUDY_STRATEGY=random python examples/qcompute/study.py
QCOMPUTE_STUDY_STRATEGY=agentic python examples/qcompute/study.py
```

The Study output includes a best trial and a `domain_payload`-compatible payload that can be passed back into MHE optimization flows.

### VQE / H2 Demo

```bash
python examples/qcompute/vqe.py
```

This creates a small FCIDUMP file, builds a Hamiltonian-driven VQE experiment, and prints:

- run status
- validation status
- best parameters
- computed energy
- reference energy
- energy error
- raw output path

## Quafu Hardware Smoke

Use hardware only when you intentionally want to submit to Quafu:

```bash
export QCOMPUTE_ENABLE_HARDWARE=1
export Qcompute_Token="your_token_here"
export QCOMPUTE_QUAFU_CHIP=Baihua
python examples/qcompute/bell.py
```

Optional knobs:

```bash
export QCOMPUTE_QUAFU_QUBITS=41
export QCOMPUTE_QUAFU_DAILY_QUOTA=10
```

Interpretation:

| Output | Meaning |
|---|---|
| `Backend: qiskit_aer` | Safe simulator fallback; hardware gate is not fully enabled |
| `Backend: quafu` | Hardware path selected |
| `Validation: ...` | Whether returned counts passed QCompute validation |
| `Policy decision: allow/defer/reject` | Governance decision for the evidence bundle |
| `Raw output` | JSON artifact containing execution result |
| `Artifact snapshots` | JSONL snapshot chain for run, validation, evidence |

Do not treat a gated Quafu run as a simulator failure. Missing token, disabled hardware env var, offline chip, quota exhaustion, and stale calibration are hardware-readiness states.

## Minimal Python API

```python
import asyncio
from pathlib import Path

from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.qcompute import (
    QComputeBackendSpec,
    QComputeCircuitSpec,
    QComputeExperimentSpec,
    QComputeGatewayComponent,
)

spec = QComputeExperimentSpec(
    task_id="bell-state-demo",
    mode="simulate",
    backend=QComputeBackendSpec(platform="qiskit_aer", simulator=True, qubit_count=2),
    circuit=QComputeCircuitSpec(
        ansatz="custom",
        num_qubits=2,
        openqasm=(
            'OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; creg c[2]; '
            'h q[0]; cx q[0],q[1]; measure q[0]->c[0]; measure q[1]->c[1];'
        ),
    ),
    shots=1024,
)

gateway = QComputeGatewayComponent()
asyncio.run(gateway.activate(ComponentRuntime(storage_path=Path(".demo-runs/manual"))))
try:
    result = gateway.run_baseline_full(spec)
    bundle = result.bundle
    print(bundle.run_artifact.status)
    print(bundle.run_artifact.counts)
    print(bundle.validation_report.status.value)
    print(result.policy.decision if result.policy else "unknown")
finally:
    asyncio.run(gateway.deactivate())
```

## Test What You Use

For user-facing validation, prefer examples first:

```bash
python examples/qcompute/bell.py
python examples/qcompute/noise_mitigation.py
QCOMPUTE_STUDY_MAX_TRIALS=2 python examples/qcompute/study.py
python examples/qcompute/vqe.py
```

For focused automated checks:

```bash
python -m pytest tests/test_metaharness_qcompute_quafu.py -q
python -m pytest tests/test_metaharness_qcompute_study.py -q
python -m pytest tests/test_metaharness_qcompute_validator.py -q
```

For full QCompute regression:

```bash
python -m pytest tests/test_metaharness_qcompute_*.py --tb=short -q
```

The support matrix is maintained at `docs/wiki/meta-harness-engineer/qcompute-engine-wiki/qcompute-tested-support-matrix.md`.

## Reflection Checklist

After running examples or hardware smoke, review the result before changing code:

1. Did `Backend` and `Mode` match the intended path?
2. Did `Run status`, `Validation`, and `Policy decision` all pass?
3. Are Bell counts concentrated on `00` and `11`?
4. Did noise mitigation print real ZNE/REM metadata?
5. Does Study produce reproducible parameters and a useful best-trial payload?
6. Is VQE `Energy error` explainable for the chosen ansatz and active space?
7. If Quafu is gated, is the reason token, SDK, chip state, quota, or calibration?

Map findings into four backlog categories:

- API integrity: exposed strategy or field is not implemented
- Result quality: fidelity, energy error, or mitigation evidence is weak
- Hardware reliability: token, calibration, queue, retry, or quota issue
- Study usability: invalid parameter types, poor search coverage, or slow trials

## Common Problems

| Symptom | Likely Cause | Fix |
|---|---|---|
| `Backend: qiskit_aer` when expecting Quafu | Hardware gate not enabled | Set `QCOMPUTE_ENABLE_HARDWARE=1` and `Qcompute_Token` |
| `missing_api_token` | Token env var absent | Export `Qcompute_Token` |
| `unsupported_platform` | Backend not implemented | Use `qiskit_aer`, `pennylane_aer`, or `quafu` |
| `insufficient_qubits` | Circuit exceeds backend capacity | Lower circuit qubits or choose a larger backend |
| validation `below_fidelity` | Measured distribution missed threshold | Inspect counts, noise, mitigation, and threshold |
| VQE energy error large | Ansatz/search too limited | Increase iterations or review Hamiltonian/active space |

## Where To Read More

- Architecture wiki: `docs/wiki/meta-harness-engineer/qcompute-engine-wiki/README.md`
- Testing and review: `docs/wiki/meta-harness-engineer/qcompute-engine-wiki/08-testing-and-review.md`
- Support matrix: `docs/wiki/meta-harness-engineer/qcompute-engine-wiki/qcompute-tested-support-matrix.md`
- Examples: `examples/qcompute/`
