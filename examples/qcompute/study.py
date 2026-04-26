from __future__ import annotations

import asyncio
import json
import os

from _shared import runtime_path

from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.qcompute import (
    QComputeBackendSpec,
    QComputeCircuitSpec,
    QComputeExperimentSpec,
    QComputeStudyAxis,
    QComputeStudyComponent,
    QComputeStudySpec,
)
from metaharness_ext.qcompute.study import trial_to_domain_payload

VALID_STRATEGIES = {"grid", "random", "agentic"}
PARAM_SWEEP_OPENQASM = 'OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; ry(0) q[0]; cx q[0],q[1];'


def build_study_spec(strategy: str) -> QComputeStudySpec:
    base_spec = QComputeExperimentSpec(
        task_id="qcompute-study-template",
        mode="simulate",
        backend=QComputeBackendSpec(platform="qiskit_aer", simulator=True, qubit_count=2),
        circuit=QComputeCircuitSpec(
            ansatz="custom",
            num_qubits=2,
            openqasm=PARAM_SWEEP_OPENQASM,
        ),
        shots=256,
    )
    if strategy == "agentic":
        axes = [
            QComputeStudyAxis(parameter_path="fidelity_threshold", range=(0.5, 0.95), step=0.15)
        ]
    else:
        axes = [QComputeStudyAxis(parameter_path="shots", values=[256, 512, 1024])]
    return QComputeStudySpec(
        study_id=f"qcompute-{strategy}-study",
        experiment_template=base_spec,
        axes=axes,
        strategy=strategy,
        max_trials=int(os.getenv("QCOMPUTE_STUDY_MAX_TRIALS", "6")),
        objective="fidelity",
    )


async def run_demo() -> None:
    strategy = os.getenv("QCOMPUTE_STUDY_STRATEGY", "grid")
    if strategy not in VALID_STRATEGIES:
        valid = ", ".join(sorted(VALID_STRATEGIES))
        raise SystemExit(
            f"Unsupported QCOMPUTE_STUDY_STRATEGY={strategy!r}. Choose one of: {valid}"
        )
    runtime_dir = runtime_path(f"study-{strategy}")
    study = QComputeStudyComponent()
    await study.activate(ComponentRuntime(storage_path=runtime_dir))
    try:
        spec = build_study_spec(strategy)
        report = study.run_study(spec)
        print(f"Strategy: {strategy}")
        print(f"Trial count: {len(report.trials)}")
        print(f"Best trial: {report.best_trial_id}")
        print(f"Pareto front: {report.pareto_front}")
        if report.best_trial_id is not None:
            best_trial = next(
                trial for trial in report.trials if trial.trial_id == report.best_trial_id
            )
            print("Best trial payload:")
            print(json.dumps(trial_to_domain_payload(best_trial), indent=2, sort_keys=True))
    finally:
        await study.deactivate()


def main() -> None:
    asyncio.run(run_demo())


if __name__ == "__main__":
    main()
