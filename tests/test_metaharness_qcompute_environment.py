from metaharness_ext.qcompute.contracts import (
    QComputeBackendSpec,
    QComputeExperimentSpec,
    QComputeNoiseSpec,
)
from metaharness_ext.qcompute.environment import QComputeEnvironmentProbeComponent


def _build_spec(**overrides) -> QComputeExperimentSpec:
    data = {
        "task_id": "qcompute-env-1",
        "mode": "simulate",
        "backend": QComputeBackendSpec(platform="qiskit_aer", simulator=True, qubit_count=4),
        "circuit": {
            "ansatz": "custom",
            "num_qubits": 2,
            "openqasm": ('OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; h q[0]; cx q[0],q[1];'),
        },
        "noise": QComputeNoiseSpec(model="none"),
    }
    data.update(overrides)
    return QComputeExperimentSpec(**data)


def test_qcompute_environment_reports_aer_ready() -> None:
    report = QComputeEnvironmentProbeComponent().probe(_build_spec())

    assert report.available is True
    assert report.status == "online"
    assert report.qubit_count_available == 4
    assert report.queue_depth == 0
    assert report.estimated_wait_seconds == 0
    assert report.prerequisite_errors == []


def test_qcompute_environment_rejects_unsupported_platform() -> None:
    report = QComputeEnvironmentProbeComponent().probe(
        _build_spec(backend=QComputeBackendSpec(platform="ibm_quantum", simulator=False))
    )

    assert report.available is False
    assert report.status == "unsupported_platform"
    assert report.blocks_promotion is True
    assert any("Unsupported backend platform" in message for message in report.prerequisite_errors)


def test_qcompute_environment_rejects_qubit_overcommit() -> None:
    report = QComputeEnvironmentProbeComponent().probe(
        _build_spec(
            backend=QComputeBackendSpec(platform="qiskit_aer", simulator=True, qubit_count=1)
        )
    )

    assert report.available is False
    assert report.status == "insufficient_qubits"
    assert any("more qubits" in message for message in report.prerequisite_errors)


def test_qcompute_environment_rejects_real_noise_without_calibration_support() -> None:
    report = QComputeEnvironmentProbeComponent().probe(
        _build_spec(noise=QComputeNoiseSpec(model="real", calibration_ref="cal-1"))
    )

    assert report.available is False
    assert report.calibration_fresh is False
    assert report.status == "calibration_unavailable"
    assert any("calibration-backed noise data" in message for message in report.prerequisite_errors)
