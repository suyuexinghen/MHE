from __future__ import annotations

from typing import Any


def mitigate_with_pennylane_transforms(
    *,
    circuit: Any,
    shots: int,
    noise: Any,
    strategies: list[str],
    num_qubits: int,
) -> dict[str, Any] | None:
    """Run error mitigation using PennyLane transforms.

    Args:
        circuit: A Qiskit QuantumCircuit to convert and execute.
        shots: Number of measurement shots per execution.
        noise: QComputeNoiseSpec (or None).
        strategies: List of mitigation strategy names (e.g. ``["zne", "rem"]``).
        num_qubits: Number of qubits in the circuit.

    Returns:
        Dict with mitigation metadata (same structure as ``mitigate_result``),
        or ``None`` when *strategies* is empty.
    """
    if not strategies:
        return None

    import pennylane as qml

    result: dict[str, Any] = {"overhead": {}}
    total_calls = 0

    # Strip Qiskit measurements before converting -- PennyLane handles
    # measurement via QNode return types, not in-circuit Measure ops.
    stripped = _strip_measurements(circuit)
    circuit_qfunc = qml.from_qiskit(stripped)
    device = qml.device("default.qubit", wires=num_qubits, shots=shots)

    if "zne" in strategies:
        zne_result = _run_pennylane_zne(
            circuit_qfunc=circuit_qfunc,
            device=device,
            shots=shots,
            num_qubits=num_qubits,
        )
        result["zne"] = zne_result
        total_calls += zne_result["executor_calls"]

    if "rem" in strategies:
        rem_result = _run_pennylane_rem(
            circuit_qfunc=circuit_qfunc,
            device=device,
            shots=shots,
            noise=noise,
            num_qubits=num_qubits,
        )
        result["rem"] = rem_result
        total_calls += rem_result["executor_calls"]

    result["overhead"]["total_executor_calls"] = total_calls
    return result


def _strip_measurements(circuit: Any) -> Any:
    """Return a copy of the Qiskit circuit without Measure operations."""
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import Measure

    has_measure = any(isinstance(inst.operation, Measure) for inst in circuit.data)
    if not has_measure:
        return circuit

    stripped = QuantumCircuit(circuit.num_qubits)
    for inst in circuit.data:
        if not isinstance(inst.operation, Measure):
            stripped.append(inst.operation, inst.qubits)
    return stripped


def _compute_zero_expectation(counts: dict[str, int]) -> float:
    """Compute expectation of the all-zeros state from measurement counts."""
    total = sum(counts.values())
    if total == 0:
        return 0.0
    zero_key = "0" * len(next(iter(counts)))
    return counts.get(zero_key, 0) / total


def _counts_from_qnode(qnode_result: dict[str, Any]) -> dict[str, int]:
    """Convert PennyLane counts dict to plain {bitstring: int}."""
    return {str(k): int(v) for k, v in qnode_result.items()}


def _run_pennylane_zne(
    *,
    circuit_qfunc: Any,
    device: Any,
    shots: int,
    num_qubits: int,
) -> dict[str, Any]:
    """Run Zero-Noise Extrapolation via PennyLane ``fold_global``."""
    import pennylane as qml

    from metaharness_ext.qcompute.mitigation import zne_extrapolate

    scale_factors = [1, 3, 5]
    scale_results: list[tuple[float, float]] = []
    executor_calls = 0

    for sf in scale_factors:
        # Build a scaled qfunc via global folding
        scaled_qfunc = qml.fold_global(circuit_qfunc, sf)

        @qml.qnode(device)
        def circuit_node() -> Any:
            scaled_qfunc()
            return qml.counts(all_outcomes=True)

        raw_counts = circuit_node()
        counts = _counts_from_qnode(raw_counts)
        expectation = _compute_zero_expectation(counts)
        scale_results.append((float(sf), expectation))
        executor_calls += 1

    extrapolated = zne_extrapolate(scale_results)

    return {
        "applied": True,
        "expectation_zero": extrapolated,
        "scale_factors": scale_factors,
        "scale_expectations": {str(sf): exp for sf, exp in scale_results},
        "executor_calls": executor_calls,
    }


def _run_pennylane_rem(
    *,
    circuit_qfunc: Any,
    device: Any,
    shots: int,
    noise: Any,
    num_qubits: int,
) -> dict[str, Any]:
    """Run Readout Error Mitigation using the NumPy confusion-matrix helper."""
    import pennylane as qml

    from metaharness_ext.qcompute.mitigation import apply_readout_mitigation

    @qml.qnode(device)
    def circuit_node() -> Any:
        circuit_qfunc()
        return qml.counts(all_outcomes=True)

    raw_counts = circuit_node()
    counts = _counts_from_qnode(raw_counts)
    executor_calls = 1

    readout_error = noise.readout_error if noise is not None else None

    if readout_error is not None and readout_error > 0:
        corrected_counts = apply_readout_mitigation(counts, readout_error)
        total = sum(corrected_counts.values())
        probabilities = {k: v / total for k, v in corrected_counts.items()} if total > 0 else {}
        return {
            "applied": True,
            "readout_error": readout_error,
            "corrected_counts": corrected_counts,
            "corrected_probabilities": probabilities,
            "executor_calls": executor_calls,
        }

    return {
        "applied": False,
        "reason": "no_readout_error",
        "executor_calls": executor_calls,
    }
