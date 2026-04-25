from __future__ import annotations

from typing import Any

import pytest
from qiskit import QuantumCircuit

from metaharness_ext.qcompute.mitigation import (
    apply_readout_mitigation,
    fold_circuit,
    mitigate_result,
    zne_extrapolate,
)


class TestZneExtrapolate:
    def test_zne_extrapolate_single_point(self) -> None:
        result = zne_extrapolate([(1.0, 0.85)])
        assert result == pytest.approx(0.85)

    def test_zne_extrapolate_linear(self) -> None:
        # Two points: (1, 0.9) and (3, 0.7) => slope = (0.7 - 0.9) / (3 - 1) = -0.1
        # Extrapolate to x=0: 0.9 - (-0.1)*1 = 0.9 + 0.1 = 1.0
        result = zne_extrapolate([(1.0, 0.9), (3.0, 0.7)])
        assert result == pytest.approx(1.0)

    def test_zne_extrapolate_linear_negative_slope(self) -> None:
        # (1, 0.8) and (5, 0.4) => slope = (0.4-0.8)/(5-1) = -0.1
        # Extrapolate: 0.8 - (-0.1)*1 = 0.9
        result = zne_extrapolate([(1.0, 0.8), (5.0, 0.4)])
        assert result == pytest.approx(0.9)

    def test_zne_extrapolate_richardson(self) -> None:
        # For a linear function y = 1.0 - 0.1*x, Richardson should return 1.0
        # Using three points that lie exactly on this line
        points = [(1.0, 0.9), (3.0, 0.7), (5.0, 0.5)]
        result = zne_extrapolate(points)
        assert result == pytest.approx(1.0, abs=1e-10)

    def test_zne_extrapolate_richardson_quadratic(self) -> None:
        # Points on y = 1.0 - 0.1*x + 0.01*x^2
        # x=1: 1.0 - 0.1 + 0.01 = 0.91
        # x=3: 1.0 - 0.3 + 0.09 = 0.79
        # x=5: 1.0 - 0.5 + 0.25 = 0.75
        # Richardson with degree-2 poly should recover y(0)=1.0
        points = [(1.0, 0.91), (3.0, 0.79), (5.0, 0.75)]
        result = zne_extrapolate(points)
        assert result == pytest.approx(1.0, abs=1e-10)

    def test_zne_extrapolate_empty(self) -> None:
        assert zne_extrapolate([]) == 0.0


class TestFoldCircuit:
    def _make_bell_circuit(self) -> QuantumCircuit:
        qc = QuantumCircuit(2)
        qc.h(0)
        qc.cx(0, 1)
        return qc

    def test_fold_circuit_scale_one(self) -> None:
        qc = self._make_bell_circuit()
        folded = fold_circuit(qc, 1.0)
        assert folded is qc

    def test_circuit_scale_below_one(self) -> None:
        qc = self._make_bell_circuit()
        folded = fold_circuit(qc, 0.5)
        assert folded is qc

    def test_fold_circuit_scale_three(self) -> None:
        qc = self._make_bell_circuit()
        original_depth = qc.depth()
        folded = fold_circuit(qc, 3.0)
        # Scale factor 3: (3-1)/2 = 1 fold = original + inverse + original
        assert folded.depth() > original_depth
        # Should be approx 3x the original depth
        assert folded.depth() >= original_depth * 2

    def test_fold_circuit_scale_five(self) -> None:
        qc = self._make_bell_circuit()
        original_depth = qc.depth()
        folded = fold_circuit(qc, 5.0)
        # Scale factor 5: (5-1)/2 = 2 folds
        assert folded.depth() > original_depth
        # Should be roughly 5x the depth
        assert folded.depth() >= original_depth * 3

    def test_fold_circuit_preserves_num_qubits(self) -> None:
        qc = QuantumCircuit(3)
        qc.h(0)
        qc.cx(0, 1)
        qc.cx(1, 2)
        folded = fold_circuit(qc, 3.0)
        assert folded.num_qubits == qc.num_qubits

    def test_fold_circuit_non_integer_returns_original(self) -> None:
        qc = self._make_bell_circuit()
        # scale_factor=2.0 => (2-1)/2 = 0 folds
        folded = fold_circuit(qc, 2.0)
        assert folded is qc


class TestApplyReadoutMitigation:
    def test_apply_readout_mitigation_no_error(self) -> None:
        counts = {"00": 60, "01": 20, "10": 15, "11": 5}
        total = sum(counts.values())
        corrected = apply_readout_mitigation(counts, 0.0)
        assert sum(corrected.values()) == total
        # With zero error, correction is identity
        for key in counts:
            assert corrected[key] == pytest.approx(counts[key], abs=1)

    def test_apply_readout_mitigation_with_error(self) -> None:
        # Heavily biased toward |00⟩ with readout error
        counts = {"00": 900, "01": 50, "10": 40, "11": 10}
        total = sum(counts.values())
        corrected = apply_readout_mitigation(counts, 0.1)
        assert sum(corrected.values()) == total
        # After correction, |00⟩ should be amplified and errors reduced
        assert corrected["00"] >= counts["00"]

    def test_apply_readout_mitigation_single_qubit(self) -> None:
        counts = {"0": 80, "1": 20}
        total = sum(counts.values())
        corrected = apply_readout_mitigation(counts, 0.05)
        assert sum(corrected.values()) == total
        # Correction should increase the dominant count
        assert corrected["0"] >= counts["0"]

    def test_apply_readout_mitigation_preserves_total(self) -> None:
        counts = {"0": 600, "1": 400}
        total = sum(counts.values())
        corrected = apply_readout_mitigation(counts, 0.15)
        assert corrected["0"] + corrected["1"] == total

    def test_apply_readout_mitigation_empty_counts(self) -> None:
        assert apply_readout_mitigation({}, 0.1) == {}

    def test_apply_readout_mitigation_no_negative_counts(self) -> None:
        counts = {"00": 990, "01": 5, "10": 3, "11": 2}
        corrected = apply_readout_mitigation(counts, 0.4)
        for key, val in corrected.items():
            assert val >= 0


class _FakeBackend:
    """Minimal backend for unit testing mitigation functions."""

    def __init__(self, counts: dict[str, int] | None = None) -> None:
        self._counts = counts or {"00": 256}

    def run(
        self,
        *,
        circuit: Any,
        shots: int,
        noise: Any = None,
    ) -> dict[str, Any]:
        total = sum(self._counts.values())
        probs = {k: v / total for k, v in self._counts.items()}
        return {
            "counts": dict(self._counts),
            "probabilities": probs,
            "execution_time_ms": 1.0,
            "metadata": {},
            "shots_completed": total,
        }


class TestMitigateResult:
    def test_mitigate_result_no_strategies(self) -> None:
        backend = _FakeBackend()
        circuit = QuantumCircuit(2)
        result = mitigate_result(backend, circuit, 256, None, [])
        assert result is None

    def test_mitigate_result_zne_only(self) -> None:
        backend = _FakeBackend(counts={"00": 200, "01": 30, "10": 20, "11": 6})
        circuit = QuantumCircuit(2)
        circuit.h(0)
        result = mitigate_result(backend, circuit, 256, None, ["zne"])
        assert result is not None
        assert result["zne"]["applied"] is True
        assert isinstance(result["zne"]["expectation_zero"], float)
        assert result["zne"]["scale_factors"] == [1, 3, 5]
        assert result["overhead"]["total_executor_calls"] == 3

    def test_mitigate_result_rem_only_with_readout_error(self) -> None:
        backend = _FakeBackend(counts={"00": 180, "01": 40, "10": 30, "11": 6})
        circuit = QuantumCircuit(2)

        class FakeNoise:
            readout_error = 0.05

        result = mitigate_result(backend, circuit, 256, FakeNoise(), ["rem"])
        assert result is not None
        assert result["rem"]["applied"] is True
        assert result["rem"]["readout_error"] == 0.05
        assert "corrected_counts" in result["rem"]
        assert result["overhead"]["total_executor_calls"] == 1

    def test_mitigate_result_rem_no_readout_error(self) -> None:
        backend = _FakeBackend()
        circuit = QuantumCircuit(2)

        class FakeNoise:
            readout_error = 0.0

        result = mitigate_result(backend, circuit, 256, FakeNoise(), ["rem"])
        assert result is not None
        assert result["rem"]["applied"] is False
        assert result["rem"]["reason"] == "no_readout_error"

    def test_mitigate_result_rem_no_noise_spec(self) -> None:
        backend = _FakeBackend()
        circuit = QuantumCircuit(2)
        result = mitigate_result(backend, circuit, 256, None, ["rem"])
        assert result is not None
        assert result["rem"]["applied"] is False
        assert result["rem"]["reason"] == "no_readout_error"

    def test_mitigate_result_zne_and_rem(self) -> None:
        backend = _FakeBackend(counts={"00": 200, "01": 30, "10": 20, "11": 6})
        circuit = QuantumCircuit(2)

        class FakeNoise:
            readout_error = 0.03

        result = mitigate_result(backend, circuit, 256, FakeNoise(), ["zne", "rem"])
        assert result is not None
        assert result["zne"]["applied"] is True
        assert result["rem"]["applied"] is True
        assert result["overhead"]["total_executor_calls"] == 4
