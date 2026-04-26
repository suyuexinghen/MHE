from __future__ import annotations

import base64
import io
import uuid
from typing import Any

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.qcompute.capabilities import (
    CAP_QCOMPUTE_CASE_COMPILE,
    CAP_QCOMPUTE_CIRCUIT_COMPILE,
)
from metaharness_ext.qcompute.contracts import (
    QComputeEnvironmentReport,
    QComputeExecutionParams,
    QComputeExperimentSpec,
    QComputeRunPlan,
)
from metaharness_ext.qcompute.slots import QCOMPUTE_CONFIG_COMPILER_SLOT


class QComputeConfigCompilerComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(QCOMPUTE_CONFIG_COMPILER_SLOT)
        api.declare_input("task", "QComputeExperimentSpec")
        api.declare_input("environment", "QComputeEnvironmentReport", required=False)
        api.declare_output("plan", "QComputeRunPlan", mode="sync")
        api.provide_capability(CAP_QCOMPUTE_CASE_COMPILE)
        api.provide_capability(CAP_QCOMPUTE_CIRCUIT_COMPILE)

    def build_plan(
        self,
        spec: QComputeExperimentSpec,
        environment_report: QComputeEnvironmentReport | None = None,
    ) -> QComputeRunPlan:
        if environment_report is not None and not environment_report.available:
            raise ValueError("QCompute environment is not available for compilation")
        if (
            spec.backend.qubit_count is not None
            and spec.circuit.num_qubits > spec.backend.qubit_count
        ):
            raise ValueError("Circuit exceeds declared backend qubit_count")

        circuit, source_kind = self._load_source_circuit(spec)
        circuit = self._ensure_measurements(circuit)
        compiled_circuit = self._compile_circuit(circuit, spec)
        qasm_text = self._dump_openqasm(compiled_circuit)
        operation_counts = {
            str(name): int(count) for name, count in compiled_circuit.count_ops().items()
        }
        estimated_depth = compiled_circuit.depth()
        estimated_swap_count = operation_counts.get("swap", 0)
        compilation_metadata = {
            "source_kind": source_kind,
            "num_qubits": compiled_circuit.num_qubits,
            "num_clbits": compiled_circuit.num_clbits,
            "operation_counts": operation_counts,
            "fidelity_threshold": spec.fidelity_threshold,
        }
        if environment_report is not None:
            compilation_metadata["environment_status"] = environment_report.status

        return QComputeRunPlan(
            plan_id=f"{spec.task_id}-{uuid.uuid4().hex[:8]}",
            experiment_ref=spec.task_id,
            circuit_openqasm=qasm_text,
            target_backend=spec.backend,
            compilation_strategy=self._compilation_strategy(spec),
            compilation_metadata=compilation_metadata,
            estimated_depth=estimated_depth,
            estimated_swap_count=estimated_swap_count,
            estimated_fidelity=self._estimate_fidelity(spec, operation_counts),
            execution_params=QComputeExecutionParams(
                shots=spec.shots,
                error_mitigation=list(spec.error_mitigation),
                retry_on_failure=spec.execution_policy.max_retry,
            ),
            graph_metadata=dict(spec.graph_metadata),
            candidate_identity=spec.candidate_identity.model_copy(deep=True),
            promotion_metadata=spec.promotion_metadata.model_copy(deep=True),
            checkpoint_refs=list(spec.checkpoint_refs),
            provenance_refs=list(spec.provenance_refs),
            trace_refs=list(spec.trace_refs),
            execution_policy=spec.execution_policy.model_copy(deep=True),
            noise=spec.noise.model_copy(deep=True) if spec.noise is not None else None,
        )

    def _load_source_circuit(self, spec: QComputeExperimentSpec) -> tuple[Any, str]:
        quantum_circuit_cls, qpy, _, _ = self._qiskit_modules()
        circuit_spec = spec.circuit
        if circuit_spec.openqasm:
            return quantum_circuit_cls.from_qasm_str(circuit_spec.openqasm), "openqasm"
        if circuit_spec.qiskit_circuit_b64:
            payload = base64.b64decode(circuit_spec.qiskit_circuit_b64)
            loaded = qpy.load(io.BytesIO(payload))
            return loaded[0], "qpy"
        return self._build_template_circuit(spec), circuit_spec.ansatz

    def _build_template_circuit(self, spec: QComputeExperimentSpec) -> Any:
        quantum_circuit_cls, _, _, _ = self._qiskit_modules()
        circuit_spec = spec.circuit
        circuit = quantum_circuit_cls(circuit_spec.num_qubits)
        theta = circuit_spec.parameters.get("theta", 0.5)
        phi = circuit_spec.parameters.get("phi", 0.25)
        if circuit_spec.ansatz == "vqe":
            for _ in range(circuit_spec.repetitions):
                for qubit in range(circuit_spec.num_qubits):
                    circuit.ry(theta, qubit)
                self._apply_entanglement(circuit, circuit_spec.entanglement)
        elif circuit_spec.ansatz == "qaoa":
            for qubit in range(circuit_spec.num_qubits):
                circuit.h(qubit)
            for _ in range(circuit_spec.repetitions):
                self._apply_entanglement(circuit, circuit_spec.entanglement, include_rz=phi)
                for qubit in range(circuit_spec.num_qubits):
                    circuit.rx(theta, qubit)
        elif circuit_spec.ansatz == "qpe":
            if circuit_spec.num_qubits < 2:
                raise ValueError("qpe ansatz requires at least 2 qubits")
            for qubit in range(circuit_spec.num_qubits - 1):
                circuit.h(qubit)
                circuit.cx(qubit, circuit_spec.num_qubits - 1)
            circuit.h(circuit_spec.num_qubits - 1)
        else:
            raise ValueError("custom ansatz requires openqasm or qiskit_circuit_b64")
        return circuit

    def _apply_entanglement(
        self,
        circuit: Any,
        entanglement: str,
        *,
        include_rz: float | None = None,
    ) -> None:
        qubit_count = circuit.num_qubits
        if qubit_count < 2:
            return
        edges: list[tuple[int, int]]
        if entanglement == "linear":
            edges = [(index, index + 1) for index in range(qubit_count - 1)]
        elif entanglement == "circular":
            edges = [(index, index + 1) for index in range(qubit_count - 1)] + [
                (qubit_count - 1, 0)
            ]
        else:
            edges = [
                (control, target)
                for control in range(qubit_count)
                for target in range(control + 1, qubit_count)
            ]
        for control, target in edges:
            circuit.cx(control, target)
            if include_rz is not None:
                circuit.rz(include_rz, target)
                circuit.cx(control, target)

    def _ensure_measurements(self, circuit: Any) -> Any:
        measured_circuit = circuit.copy()
        if measured_circuit.num_clbits == 0:
            measured_circuit.measure_all()
        return measured_circuit

    def _compile_circuit(self, circuit: Any, spec: QComputeExperimentSpec) -> Any:
        _, _, _, generate_preset_pass_manager = self._qiskit_modules()
        backend = None
        if spec.backend.platform == "qiskit_aer":
            from qiskit_aer import AerSimulator

            backend = AerSimulator()
        pass_manager = generate_preset_pass_manager(
            optimization_level=spec.circuit.transpiler_level,
            backend=backend,
        )
        return pass_manager.run(circuit)

    def _dump_openqasm(self, circuit: Any) -> str:
        _, _, qasm2, _ = self._qiskit_modules()
        return qasm2.dumps(circuit)

    def _compilation_strategy(self, spec: QComputeExperimentSpec) -> str:
        if spec.circuit.transpiler_level >= 2:
            return "sabre"
        return "baseline"

    def _estimate_fidelity(
        self, spec: QComputeExperimentSpec, operation_counts: dict[str, int]
    ) -> float | None:
        if spec.noise is None:
            return 1.0
        if spec.noise.model == "depolarizing" and spec.noise.depolarizing_prob is not None:
            probability = max(0.0, min(1.0, spec.noise.depolarizing_prob))
            effective_ops = sum(operation_counts.values())
            return max(0.0, (1.0 - probability) ** effective_ops)
        if spec.fidelity_threshold is not None:
            return spec.fidelity_threshold
        return None

    def build_plan_from_hamiltonian(
        self,
        spec: QComputeExperimentSpec,
        environment_report: QComputeEnvironmentReport | None = None,
    ) -> QComputeRunPlan:
        """Build a run plan starting from a Hamiltonian file (FCIDUMP).

        Parses the Hamiltonian, optionally applies active-space selection,
        maps fermionic operators to qubit Pauli operators, then delegates
        to :meth:`build_plan` for circuit compilation.

        The resulting qubit Hamiltonian metadata is stored in
        ``plan.compilation_metadata["hamiltonian"]``.
        """
        if spec.hamiltonian_file is None:
            raise ValueError("spec.hamiltonian_file must be set for hamiltonian-based compilation")

        from metaharness_ext.qcompute.fcidump import parse_fcidump
        from metaharness_ext.qcompute.fermion_mapper import (
            build_active_space,
            map_fermionic_to_qubit,
        )

        fcidata = parse_fcidump(spec.hamiltonian_file)

        if spec.active_space is not None:
            n_elec, n_orb = spec.active_space
            active_space = build_active_space(
                fcidata, n_electrons=n_elec, n_orbitals=n_orb, method="manual"
            )
        else:
            active_space = build_active_space(fcidata, method="full")

        mapping_method = spec.fermion_mapping
        qubit_hamiltonian = map_fermionic_to_qubit(fcidata, active_space, method=mapping_method)

        plan = self.build_plan(spec, environment_report)

        # Inject hamiltonian metadata into the compilation metadata.
        plan.compilation_metadata["hamiltonian"] = qubit_hamiltonian.model_dump()
        plan.compilation_metadata["hamiltonian_file"] = spec.hamiltonian_file
        plan.compilation_metadata["active_space"] = active_space.model_dump()
        plan.compilation_metadata["mapping_method"] = mapping_method

        # Add hamiltonian file to provenance refs if not already present.
        hamiltonian_ref = f"abacus://hamiltonian/{spec.hamiltonian_file}"
        if hamiltonian_ref not in plan.provenance_refs:
            plan.provenance_refs.append(hamiltonian_ref)

        return plan

    def _qiskit_modules(self) -> tuple[Any, Any, Any, Any]:
        import qiskit.qasm2 as qasm2
        from qiskit import QuantumCircuit, qpy
        from qiskit.transpiler import generate_preset_pass_manager

        return QuantumCircuit, qpy, qasm2, generate_preset_pass_manager
