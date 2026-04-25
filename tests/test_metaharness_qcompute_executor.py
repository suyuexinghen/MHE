import json
from pathlib import Path

import pytest

from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.qcompute.config_compiler import QComputeConfigCompilerComponent
from metaharness_ext.qcompute.contracts import (
    QComputeBackendSpec,
    QComputeEnvironmentReport,
    QComputeExperimentSpec,
    QComputeNoiseSpec,
)
from metaharness_ext.qcompute.executor import QComputeExecutorComponent


def _build_spec(**overrides) -> QComputeExperimentSpec:
    data = {
        "task_id": "qcompute-run-1",
        "mode": "simulate",
        "backend": QComputeBackendSpec(platform="qiskit_aer", simulator=True, qubit_count=4),
        "circuit": {
            "ansatz": "custom",
            "num_qubits": 2,
            "openqasm": ('OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; h q[0]; cx q[0],q[1];'),
        },
        "noise": QComputeNoiseSpec(model="none"),
        "shots": 256,
    }
    data.update(overrides)
    return QComputeExperimentSpec(**data)


@pytest.mark.asyncio
async def test_qcompute_executor_requires_runtime_storage_path() -> None:
    plan = QComputeConfigCompilerComponent().build_plan(_build_spec())
    executor = QComputeExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=None))

    with pytest.raises(RuntimeError, match="runtime.storage_path"):
        executor.execute_plan(plan)


@pytest.mark.asyncio
async def test_qcompute_executor_runs_aer_plan(tmp_path: Path) -> None:
    compiler = QComputeConfigCompilerComponent()
    plan = compiler.build_plan(_build_spec())
    executor = QComputeExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    artifact = executor.execute_plan(plan)

    assert artifact.status == "completed"
    assert artifact.backend_actual == "qiskit_aer"
    assert artifact.counts is not None
    assert sum(artifact.counts.values()) == 256
    assert artifact.probabilities is not None
    assert abs(sum(artifact.probabilities.values()) - 1.0) < 1e-9
    assert artifact.raw_output_path is not None
    payload = json.loads(Path(artifact.raw_output_path).read_text())
    assert payload["shots_completed"] == 256


@pytest.mark.asyncio
async def test_qcompute_executor_rejects_failed_environment(tmp_path: Path) -> None:
    compiler = QComputeConfigCompilerComponent()
    plan = compiler.build_plan(_build_spec())
    executor = QComputeExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))
    environment_report = QComputeEnvironmentReport(
        task_id=plan.experiment_ref,
        backend=plan.target_backend,
        available=False,
        status="dependency_missing",
    )

    artifact = executor.execute_plan(plan, environment_report)

    assert artifact.status == "failed"
    assert artifact.terminal_error_type == "environment_unavailable"
    assert artifact.error_message is not None
    assert "dependency_missing" in artifact.error_message


@pytest.mark.asyncio
async def test_qcompute_executor_uses_gate_error_map_noise(tmp_path: Path) -> None:
    compiler = QComputeConfigCompilerComponent()
    plan = compiler.build_plan(
        _build_spec(
            noise=QComputeNoiseSpec(
                model="depolarizing",
                depolarizing_prob=0.0,
                gate_error_map={"h": 0.2, "cx": 0.3},
            )
        )
    )
    executor = QComputeExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    artifact = executor.execute_plan(plan)

    assert artifact.status == "completed"
    assert artifact.raw_output_path is not None
    payload = json.loads(Path(artifact.raw_output_path).read_text())
    assert payload["shots_completed"] == 256
    assert payload["counts"]
