from __future__ import annotations

import json
from importlib.util import find_spec
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.qcompute.config_compiler import QComputeConfigCompilerComponent
from metaharness_ext.qcompute.contracts import (
    QComputeBackendSpec,
    QComputeExperimentSpec,
    QComputeNoiseSpec,
)
from metaharness_ext.qcompute.environment import QComputeEnvironmentProbeComponent
from metaharness_ext.qcompute.executor import QComputeExecutorComponent
from metaharness_ext.qcompute.validator import QComputeValidatorComponent

BELL_STATE_OPENQASM = 'OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; h q[0]; cx q[0],q[1];'


def _build_spec(**overrides: Any) -> QComputeExperimentSpec:
    data: dict[str, Any] = {
        "task_id": "pl-test-1",
        "mode": "simulate",
        "backend": QComputeBackendSpec(
            platform="pennylane_aer",
            simulator=True,
            qubit_count=4,
        ),
        "circuit": {
            "ansatz": "custom",
            "num_qubits": 2,
            "openqasm": BELL_STATE_OPENQASM,
        },
        "noise": QComputeNoiseSpec(model="none"),
        "shots": 256,
    }
    data.update(overrides)
    return QComputeExperimentSpec(**data)


@pytest.mark.asyncio
async def test_pennylane_backend_runs_bell_state(tmp_path: Path) -> None:
    compiler = QComputeConfigCompilerComponent()
    plan = compiler.build_plan(_build_spec())
    executor = QComputeExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    artifact = executor.execute_plan(plan)

    assert artifact.status == "completed"
    assert artifact.backend_actual == "pennylane_aer"
    assert artifact.counts is not None
    assert sum(artifact.counts.values()) == 256
    assert artifact.probabilities is not None
    assert abs(sum(artifact.probabilities.values()) - 1.0) < 1e-9
    assert artifact.raw_output_path is not None
    payload = json.loads(Path(artifact.raw_output_path).read_text())
    assert payload["shots_completed"] == 256


@pytest.mark.asyncio
async def test_pennylane_backend_noise_execution(tmp_path: Path) -> None:
    compiler = QComputeConfigCompilerComponent()
    plan = compiler.build_plan(
        _build_spec(
            noise=QComputeNoiseSpec(model="depolarizing", depolarizing_prob=0.05),
        )
    )
    executor = QComputeExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    artifact = executor.execute_plan(plan)

    assert artifact.status == "completed"
    assert artifact.counts is not None
    assert sum(artifact.counts.values()) == 256


@pytest.mark.asyncio
async def test_pennylane_environment_probe() -> None:
    probe = QComputeEnvironmentProbeComponent()
    spec = _build_spec()
    report = probe.probe(spec)

    assert report.available is True
    assert report.status == "online"
    assert not report.prerequisite_errors


@pytest.mark.asyncio
async def test_pennylane_environment_missing() -> None:
    probe = QComputeEnvironmentProbeComponent()

    def _fake_find_spec(name: str) -> Any:
        if name == "pennylane":
            return None
        return find_spec(name)

    with patch("metaharness_ext.qcompute.environment.find_spec", side_effect=_fake_find_spec):
        spec = _build_spec()
        report = probe.probe(spec)

    assert report.available is False
    assert report.status == "dependency_missing"
    assert any("pennylane" in e for e in report.prerequisite_errors)


@pytest.mark.asyncio
async def test_pennylane_mitigation_zne(tmp_path: Path) -> None:
    compiler = QComputeConfigCompilerComponent()
    plan = compiler.build_plan(
        _build_spec(
            error_mitigation=["zne"],
            noise=QComputeNoiseSpec(model="depolarizing", depolarizing_prob=0.05),
        )
    )
    executor = QComputeExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    artifact = executor.execute_plan(plan)

    assert artifact.status == "completed"
    mitigation = artifact.execution_policy.details["error_mitigation"]
    assert mitigation["zne"]["applied"] is True
    assert isinstance(mitigation["zne"]["expectation_zero"], float)
    assert 0.0 <= mitigation["zne"]["expectation_zero"] <= 1.0
    assert mitigation["zne"]["scale_factors"] == [1, 3, 5]
    assert mitigation["requested"] == ["zne"]
    assert mitigation["overhead"]["total_executor_calls"] == 3


@pytest.mark.asyncio
async def test_pennylane_executor_full_pipeline(tmp_path: Path) -> None:
    """Compile -> execute -> validate with pennylane_aer platform."""
    compiler = QComputeConfigCompilerComponent()
    spec = _build_spec()
    plan = compiler.build_plan(spec)

    executor = QComputeExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))
    artifact = executor.execute_plan(plan)
    assert artifact.status == "completed"

    probe = QComputeEnvironmentProbeComponent()
    environment = probe.probe(spec)
    assert environment.available is True

    validator = QComputeValidatorComponent()
    await validator.activate(ComponentRuntime(storage_path=tmp_path))
    validation = validator.validate_run(artifact, plan, environment)
    assert validation.passed is True
