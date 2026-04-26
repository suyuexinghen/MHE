from __future__ import annotations

import random
import time
from typing import Any

from metaharness_ext.qcompute.contracts import QComputeNoiseSpec


class PennyLaneBackend:
    """PennyLane-based quantum backend using default.qubit or default.mixed device."""

    def run(
        self,
        *,
        circuit: Any,
        shots: int,
        noise: QComputeNoiseSpec | None = None,
    ) -> dict[str, Any]:
        import pennylane as qml

        stripped = self._strip_measurements(circuit)
        num_qubits = stripped.num_qubits
        qfunc = qml.from_qiskit(stripped)
        use_noise = noise is not None and noise.model not in {"none", "real"}

        if use_noise:
            dev = qml.device("default.mixed", wires=num_qubits, shots=shots)
            depol_prob = noise.depolarizing_prob if noise else None

            @qml.qnode(dev)
            def noisy_circuit() -> Any:
                qfunc()
                if depol_prob and depol_prob > 0:
                    for wire in range(num_qubits):
                        qml.DepolarizingChannel(depol_prob, wires=wire)
                return qml.counts(wires=range(num_qubits))

            t0 = time.perf_counter()
            raw_counts = noisy_circuit()
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
        else:
            dev = qml.device("default.qubit", wires=num_qubits, shots=shots)

            @qml.qnode(dev)
            def clean_circuit() -> Any:
                qfunc()
                return qml.counts()

            t0 = time.perf_counter()
            raw_counts = clean_circuit()
            elapsed_ms = (time.perf_counter() - t0) * 1000.0

        counts = {str(key): int(value) for key, value in raw_counts.items()}

        if use_noise and noise is not None and noise.readout_error and noise.readout_error > 0:
            counts = self._apply_readout_error(counts, noise.readout_error)

        total_shots = sum(counts.values())
        probabilities = {bs: cnt / total_shots for bs, cnt in counts.items()} if total_shots else {}
        return {
            "counts": counts,
            "probabilities": probabilities,
            "execution_time_ms": elapsed_ms,
            "metadata": {"backend": "pennylane"},
            "shots_completed": total_shots,
        }

    def _strip_measurements(self, circuit: Any) -> Any:
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

    def _apply_readout_error(self, counts: dict[str, int], readout_error: float) -> dict[str, int]:
        if readout_error <= 0 or not counts:
            return counts
        n_bits = len(next(iter(counts)))
        rng = random.Random()
        new_counts: dict[str, int] = {}
        for bitstring, count in counts.items():
            for _ in range(count):
                flipped = list(bitstring)
                for i in range(n_bits):
                    if rng.random() < readout_error:
                        flipped[i] = "1" if flipped[i] == "0" else "0"
                key = "".join(flipped)
                new_counts[key] = new_counts.get(key, 0) + 1
        return new_counts
