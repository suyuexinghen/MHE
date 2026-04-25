from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from metaharness_ext.qcompute.contracts import QComputeNoiseSpec


class QiskitAerBackend:
    def run(
        self,
        *,
        circuit: Any,
        shots: int,
        noise: QComputeNoiseSpec | None = None,
    ) -> dict[str, Any]:
        from qiskit_aer import AerSimulator

        simulator = AerSimulator(noise_model=self._build_noise_model(noise))
        result = simulator.run(circuit, shots=shots).result()
        counts = {str(key): int(value) for key, value in result.get_counts().items()}
        total_shots = sum(counts.values())
        probabilities = (
            {bitstring: value / total_shots for bitstring, value in counts.items()}
            if total_shots
            else {}
        )
        metadata = result.to_dict()
        execution_time_ms = self._extract_execution_time_ms(metadata)
        return {
            "counts": counts,
            "probabilities": probabilities,
            "execution_time_ms": execution_time_ms,
            "metadata": metadata,
            "shots_completed": total_shots,
        }

    def _build_noise_model(self, noise: QComputeNoiseSpec | None) -> Any | None:
        if noise is None or noise.model in {"none", "real"}:
            return None

        from qiskit_aer.noise import (
            NoiseModel,
            ReadoutError,
            depolarizing_error,
            thermal_relaxation_error,
        )

        noise_model = NoiseModel()
        gate_error_map = noise.gate_error_map or {}
        if noise.model == "depolarizing":
            probability = noise.depolarizing_prob or 0.0
            if probability > 0:
                noise_model.add_all_qubit_quantum_error(
                    depolarizing_error(probability, 1),
                    ["h", "rx", "ry", "rz", "sx", "x"],
                )
                noise_model.add_all_qubit_quantum_error(
                    depolarizing_error(probability, 2),
                    ["cx"],
                )
        elif noise.model == "thermal_relaxation":
            t1 = (noise.t1_us or 100.0) * 1e-6
            t2 = (noise.t2_us or 80.0) * 1e-6
            single_qubit_error = thermal_relaxation_error(t1, t2, 50e-9)
            two_qubit_error = single_qubit_error.tensor(single_qubit_error)
            noise_model.add_all_qubit_quantum_error(
                single_qubit_error,
                ["h", "rx", "ry", "rz", "sx", "x"],
            )
            noise_model.add_all_qubit_quantum_error(two_qubit_error, ["cx"])

        for gate_name, probability in gate_error_map.items():
            if probability <= 0:
                continue
            if gate_name == "cx":
                noise_model.add_all_qubit_quantum_error(
                    depolarizing_error(probability, 2), [gate_name]
                )
            else:
                noise_model.add_all_qubit_quantum_error(
                    depolarizing_error(probability, 1), [gate_name]
                )

        if noise.readout_error:
            readout_probability = noise.readout_error
            noise_model.add_all_qubit_readout_error(
                ReadoutError(
                    [
                        [1 - readout_probability, readout_probability],
                        [readout_probability, 1 - readout_probability],
                    ]
                )
            )
        return noise_model

    def _extract_execution_time_ms(self, metadata: Mapping[str, Any]) -> float | None:
        results = metadata.get("results")
        if isinstance(results, list) and results:
            result_entry = results[0]
            if isinstance(result_entry, dict):
                time_taken = result_entry.get("time_taken")
                if isinstance(time_taken, int | float):
                    return float(time_taken) * 1000.0
        time_taken = metadata.get("time_taken")
        if isinstance(time_taken, int | float):
            return float(time_taken) * 1000.0
        return None
