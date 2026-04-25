import base64
import io

import pytest

from metaharness_ext.qcompute.config_compiler import QComputeConfigCompilerComponent
from metaharness_ext.qcompute.contracts import (
    QComputeBackendSpec,
    QComputeEnvironmentReport,
    QComputeExperimentSpec,
    QComputeNoiseSpec,
)


def _build_spec(**overrides) -> QComputeExperimentSpec:
    data = {
        "task_id": "qcompute-compile-1",
        "mode": "simulate",
        "backend": QComputeBackendSpec(platform="qiskit_aer", simulator=True, qubit_count=4),
        "circuit": {
            "ansatz": "custom",
            "num_qubits": 2,
            "openqasm": ('OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; h q[0]; cx q[0],q[1];'),
        },
        "noise": QComputeNoiseSpec(model="depolarizing", depolarizing_prob=0.001),
        "shots": 2048,
        "error_mitigation": ["zne"],
    }
    data.update(overrides)
    return QComputeExperimentSpec(**data)


def test_qcompute_compiler_builds_plan_from_openqasm() -> None:
    plan = QComputeConfigCompilerComponent().build_plan(_build_spec())

    assert plan.plan_id.startswith("qcompute-compile-1-")
    assert plan.target_backend.platform == "qiskit_aer"
    assert plan.execution_params.shots == 2048
    assert plan.execution_params.error_mitigation == ["zne"]
    assert plan.noise is not None
    assert plan.compilation_metadata["source_kind"] == "openqasm"
    assert plan.compilation_metadata["operation_counts"]["measure"] == 2
    assert "measure q[0]" in plan.circuit_openqasm
    assert plan.estimated_depth is not None
    assert plan.estimated_fidelity is not None


def test_qcompute_compiler_builds_template_vqe_plan() -> None:
    spec = _build_spec(
        task_id="qcompute-template",
        circuit={
            "ansatz": "vqe",
            "num_qubits": 3,
            "repetitions": 2,
            "entanglement": "linear",
            "parameters": {"theta": 0.2},
        },
        noise=None,
    )

    plan = QComputeConfigCompilerComponent().build_plan(spec)

    assert plan.compilation_metadata["source_kind"] == "vqe"
    assert plan.compilation_metadata["num_qubits"] == 3
    assert plan.estimated_swap_count == 0
    assert plan.execution_params.shots == 2048


def test_qcompute_compiler_loads_qpy_payload() -> None:
    from qiskit import QuantumCircuit, qpy

    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.cx(0, 1)
    buffer = io.BytesIO()
    qpy.dump(circuit, buffer)
    payload = base64.b64encode(buffer.getvalue()).decode()

    spec = _build_spec(
        task_id="qcompute-qpy",
        circuit={"ansatz": "custom", "num_qubits": 2, "qiskit_circuit_b64": payload},
        noise=None,
    )

    plan = QComputeConfigCompilerComponent().build_plan(spec)

    assert plan.compilation_metadata["source_kind"] == "qpy"
    assert "measure q[1]" in plan.circuit_openqasm


def test_qcompute_compiler_rejects_unavailable_environment() -> None:
    environment_report = QComputeEnvironmentReport(
        task_id="qcompute-compile-1",
        backend=QComputeBackendSpec(platform="qiskit_aer", simulator=True, qubit_count=4),
        available=False,
        status="dependency_missing",
    )

    with pytest.raises(ValueError, match="environment is not available"):
        QComputeConfigCompilerComponent().build_plan(_build_spec(), environment_report)
