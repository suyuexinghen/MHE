from __future__ import annotations

from typing import Any

import numpy as np


def zne_extrapolate(scale_results: list[tuple[float, float]]) -> float:
    """Extrapolate to zero-noise using Richardson extrapolation.

    Args:
        scale_results: List of (scale_factor, expectation_value) pairs.

    Returns:
        Estimated zero-noise expectation value.
    """
    if len(scale_results) == 0:
        return 0.0
    if len(scale_results) == 1:
        return float(scale_results[0][1])

    scale_factors = np.array([r[0] for r in scale_results], dtype=float)
    expectations = np.array([r[1] for r in scale_results], dtype=float)

    if len(scale_results) == 2:
        # Linear extrapolation: fit line through two points, evaluate at x=0
        x1, x2 = scale_factors
        y1, y2 = expectations
        if abs(x2 - x1) < 1e-12:
            return float(y1)
        slope = (y2 - y1) / (x2 - x1)
        return float(y1 - slope * x1)

    # Richardson extrapolation: polynomial fit, evaluate at x=0
    # Vandermonde matrix for polynomial of degree len-1
    degree = len(scale_results) - 1
    vand = np.vander(scale_factors, N=degree + 1, increasing=True)
    coeffs = np.linalg.solve(vand, expectations)
    # Evaluate at scale_factor=0 => only the constant term survives
    return float(coeffs[0])


def fold_circuit(circuit: Any, scale_factor: float) -> Any:
    """Apply unitary folding to amplify noise in a circuit.

    For integer scale factors 1, 3, 5: fold all gates (scale-1)/2 times.
    For scale_factor=1.0, returns the circuit unchanged.

    Measurements are stripped before folding and re-appended at the end,
    since ``inverse()`` does not support measure operations.

    Args:
        circuit: A Qiskit QuantumCircuit.
        scale_factor: Noise amplification factor (supports 1, 3, 5).

    Returns:
        A new QuantumCircuit with amplified noise.
    """
    if scale_factor <= 1.0:
        return circuit

    num_folds = int((scale_factor - 1.0) / 2.0)
    if num_folds < 1:
        return circuit

    from qiskit import ClassicalRegister, QuantumCircuit
    from qiskit.circuit.library import Measure

    # Separate measurements from the unitary part
    measurements = [
        (inst.operation, inst.qubits, inst.clbits)
        for inst in circuit.data
        if isinstance(inst.operation, Measure)
    ]
    num_clbits = circuit.num_clbits

    # Build a clean gate-only circuit (no measurements, no clbits)
    gate_circuit = QuantumCircuit(circuit.num_qubits)
    for inst in circuit.data:
        if not isinstance(inst.operation, Measure):
            gate_circuit.append(inst.operation, inst.qubits, inst.clbits)

    all_qubits = list(range(circuit.num_qubits))
    folded = gate_circuit.copy()

    for _ in range(num_folds):
        # Append inverse then original for each gate
        dag = gate_circuit.copy()
        dag = dag.inverse()
        folded = folded.compose(dag, qubits=all_qubits)
        folded = folded.compose(gate_circuit, qubits=all_qubits)

    # Re-add measurements if there were any
    if measurements and num_clbits > 0:
        creg = ClassicalRegister(num_clbits, name="meas")
        folded.add_register(creg)
        for op, qubits, clbits in measurements:
            folded.append(op, qubits, clbits)

    return folded


def apply_readout_mitigation(counts: dict[str, int], readout_error: float) -> dict[str, int]:
    """Correct measurement counts using a readout confusion matrix.

    Builds a 2^n x 2^n confusion matrix from a uniform readout error
    probability, inverts it, and applies the correction to the count vector.

    Args:
        counts: Raw measurement counts as {bitstring: count}.
        readout_error: Per-qubit probability of flipping a measurement outcome.

    Returns:
        Corrected counts with negatives clamped to 0, renormalized to total shots.
    """
    if not counts:
        return counts

    keys = sorted(counts.keys())
    n = len(keys[0])
    dim = 2**n
    total_shots = sum(counts.values())

    if total_shots == 0:
        return counts

    # Build confusion matrix
    p = readout_error
    confusion = _build_confusion_matrix(n, p)

    # Invert the confusion matrix
    try:
        correction = np.linalg.inv(confusion)
    except np.linalg.LinAlgError:
        return counts

    # Build count vector in standard bitstring order
    count_vector = np.zeros(dim, dtype=float)
    for i, key in enumerate(keys):
        count_vector[i] = counts.get(key, 0)

    # Apply correction
    corrected = correction @ count_vector

    # Clamp negatives to 0
    corrected = np.maximum(corrected, 0.0)

    # Renormalize to total shots
    corrected_sum = corrected.sum()
    if corrected_sum > 0:
        corrected = corrected * (total_shots / corrected_sum)

    # Round to integers
    corrected_ints = np.round(corrected).astype(int)

    # Adjust rounding to preserve total shots
    diff = total_shots - corrected_ints.sum()
    if diff != 0:
        # Distribute rounding difference to largest bins
        indices = np.argsort(-corrected_ints)
        for i in range(abs(diff)):
            idx = indices[i % len(indices)]
            corrected_ints[idx] += 1 if diff > 0 else -1
            if corrected_ints[idx] < 0:
                corrected_ints[idx] = 0

    return {key: int(corrected_ints[i]) for i, key in enumerate(keys)}


def _build_confusion_matrix(n: int, p: float) -> np.ndarray:
    """Build 2^n x 2^n confusion matrix for n qubits with error prob p.

    Each qubit independently flips with probability p.
    """
    dim = 2**n
    confusion = np.zeros((dim, dim), dtype=float)

    for i in range(dim):
        for j in range(dim):
            prob = 1.0
            for qubit in range(n):
                bit_i = (i >> qubit) & 1
                bit_j = (j >> qubit) & 1
                if bit_i == bit_j:
                    prob *= 1.0 - p
                else:
                    prob *= p
            confusion[i][j] = prob

    return confusion


def mitigate_result(
    backend: Any,
    circuit: Any,
    shots: int,
    noise: Any,
    strategies: list[str],
) -> dict[str, Any] | None:
    """Run error mitigation strategies on a quantum circuit execution.

    Args:
        backend: Quantum backend with a run() method.
        circuit: Qiskit QuantumCircuit to execute.
        shots: Number of shots per execution.
        noise: QComputeNoiseSpec (or None).
        strategies: List of strategies to apply (e.g. ["zne", "rem"]).

    Returns:
        Dict with mitigation metadata, or None if no strategies provided.
    """
    if not strategies:
        return None

    result: dict[str, Any] = {"overhead": {}}
    total_calls = 0

    if "zne" in strategies:
        zne_result = _run_zne(backend, circuit, shots, noise)
        result["zne"] = zne_result
        total_calls += zne_result["executor_calls"]

    if "rem" in strategies:
        rem_result = _run_rem(backend, circuit, shots, noise)
        result["rem"] = rem_result
        total_calls += rem_result["executor_calls"]

    result["overhead"]["total_executor_calls"] = total_calls
    return result


def _compute_zero_expectation(counts: dict[str, int]) -> float:
    """Compute expectation of the all-zeros state from counts."""
    total = sum(counts.values())
    if total == 0:
        return 0.0
    zero_count = counts.get("0" * len(next(iter(counts))), 0)
    return zero_count / total


def _run_zne(backend: Any, circuit: Any, shots: int, noise: Any) -> dict[str, Any]:
    """Run Zero-Noise Extrapolation at scale factors 1, 3, 5."""
    scale_factors = [1, 3, 5]
    scale_results: list[tuple[float, float]] = []
    executor_calls = 0

    for sf in scale_factors:
        folded = fold_circuit(circuit, float(sf))
        run_result = backend.run(circuit=folded, shots=shots, noise=noise)
        executor_calls += 1
        expectation = _compute_zero_expectation(run_result["counts"])
        scale_results.append((float(sf), expectation))

    extrapolated = zne_extrapolate(scale_results)

    return {
        "applied": True,
        "expectation_zero": extrapolated,
        "scale_factors": scale_factors,
        "scale_expectations": {str(sf): exp for sf, exp in scale_results},
        "executor_calls": executor_calls,
    }


def _run_rem(backend: Any, circuit: Any, shots: int, noise: Any) -> dict[str, Any]:
    """Run Readout Error Mitigation."""
    readout_error = noise.readout_error if noise is not None else None

    run_result = backend.run(circuit=circuit, shots=shots, noise=noise)
    executor_calls = 1

    if readout_error is not None and readout_error > 0:
        corrected_counts = apply_readout_mitigation(run_result["counts"], readout_error)
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
