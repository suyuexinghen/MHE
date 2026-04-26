"""Tests for the ABACUS integration pipeline (FCIDUMP -> compile -> execute -> validate)."""

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
from metaharness_ext.qcompute.validator import QComputeValidatorComponent

H2_FCIDUMP = """ &FCI NORB=2,NELEC=2,MS2=0,
   ORBSYM=1,1,
   ISYM=1,
 &END
  1.834752942932  1  1  0  0
  0.715403888080  2  1  0  0
  0.663476275792  2  2  0  0
  0.181293137885  1  1  1  1
  0.663476275792  2  2  2  2
  0.715403888080  1  2  0  0
  0.181293137885  2  2  1  1
  0.120365812741  2  1  2  1
  0.120365812741  1  2  1  2
  0.675710775216  2  2  2  1
  0.675710775216  2  1  2  2
  0.000000000000  0  0  0  0
"""


def _write_h2_fcidump(tmp_path: Path) -> str:
    """Write H2 FCIDUMP data to a temp file and return the path string."""
    fcidump_path = tmp_path / "h2_sto3g.fcidump"
    fcidump_path.write_text(H2_FCIDUMP)
    return str(fcidump_path)


def _build_hamiltonian_spec(hamiltonian_file: str, **overrides) -> QComputeExperimentSpec:
    data = {
        "task_id": "abacus-h2-1",
        "mode": "simulate",
        "backend": QComputeBackendSpec(platform="qiskit_aer", simulator=True, qubit_count=4),
        "circuit": {
            "ansatz": "custom",
            "num_qubits": 2,
            "openqasm": ('OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; h q[0]; cx q[0],q[1];'),
        },
        "noise": QComputeNoiseSpec(model="none"),
        "shots": 256,
        "hamiltonian_file": hamiltonian_file,
        "hamiltonian_format": "fcidump",
        "fermion_mapping": "jordan_wigner",
    }
    data.update(overrides)
    return QComputeExperimentSpec(**data)


def _build_environment_report(
    plan,
    *,
    available: bool = True,
    status: str = "ready",
) -> QComputeEnvironmentReport:
    return QComputeEnvironmentReport(
        task_id=plan.experiment_ref,
        backend=plan.target_backend,
        available=available,
        status=status,
    )


class TestHamiltonianFileThroughPipeline:
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_hamiltonian_file_through_pipeline(self, tmp_path: Path) -> None:
        hamiltonian_file = _write_h2_fcidump(tmp_path)
        spec = _build_hamiltonian_spec(hamiltonian_file)

        compiler = QComputeConfigCompilerComponent()
        plan = compiler.build_plan_from_hamiltonian(spec)

        # Verify hamiltonian metadata was injected.
        assert "hamiltonian" in plan.compilation_metadata
        assert "hamiltonian_file" in plan.compilation_metadata
        assert plan.compilation_metadata["hamiltonian_file"] == hamiltonian_file

        # Hamiltonian metadata should contain num_qubits and terms.
        ham_meta = plan.compilation_metadata["hamiltonian"]
        assert ham_meta["num_qubits"] == 2
        assert len(ham_meta["terms"]) > 0
        assert ham_meta["mapping_method"] == "jordan_wigner"

        # Execute the plan.
        executor = QComputeExecutorComponent()
        await executor.activate(ComponentRuntime(storage_path=tmp_path))
        artifact = executor.execute_plan(plan)
        assert artifact.status == "completed"

        # Validate.
        env_report = _build_environment_report(plan)
        validator = QComputeValidatorComponent()
        await validator.activate(ComponentRuntime(storage_path=tmp_path))
        validation = validator.validate_run(artifact, plan, env_report)
        assert validation.passed


class TestProvenanceRefsIncludeAbacus:
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_provenance_refs_include_abacus(self, tmp_path: Path) -> None:
        hamiltonian_file = _write_h2_fcidump(tmp_path)
        spec = _build_hamiltonian_spec(hamiltonian_file)

        compiler = QComputeConfigCompilerComponent()
        plan = compiler.build_plan_from_hamiltonian(spec)

        # Provenance refs should contain the hamiltonian file reference.
        abacus_refs = [r for r in plan.provenance_refs if "abacus://hamiltonian/" in r]
        assert len(abacus_refs) == 1
        assert hamiltonian_file in abacus_refs[0]


class TestEnergyComparisonWithReference:
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_energy_comparison_with_reference(self, tmp_path: Path) -> None:
        hamiltonian_file = _write_h2_fcidump(tmp_path)
        reference_energy = -1.137
        spec = _build_hamiltonian_spec(
            hamiltonian_file,
            circuit={
                "ansatz": "vqe",
                "num_qubits": 2,
                "repetitions": 1,
                "entanglement": "linear",
            },
            max_iterations=5,
            reference_energy=reference_energy,
        )

        compiler = QComputeConfigCompilerComponent()
        plan = compiler.build_plan_from_hamiltonian(spec)

        optimization = plan.compilation_metadata["vqe_optimization"]
        assert optimization["method"] == "deterministic_grid"
        assert optimization["iterations"] == 5
        assert plan.compilation_metadata["computed_energy"] == optimization["best_energy"]
        assert plan.compilation_metadata["hamiltonian"]["reference_energy"] == reference_energy
        assert "theta" in optimization["best_parameters"]

        executor = QComputeExecutorComponent()
        await executor.activate(ComponentRuntime(storage_path=tmp_path))
        artifact = executor.execute_plan(plan)

        env_report = _build_environment_report(plan)
        validator = QComputeValidatorComponent()
        await validator.activate(ComponentRuntime(storage_path=tmp_path))
        validation = validator.validate_run(artifact, plan, env_report)

        assert validation.metrics.energy == optimization["best_energy"]
        assert validation.metrics.convergence_iterations == 5
        expected_error = abs(optimization["best_energy"] - reference_energy)
        assert validation.metrics.energy_error == expected_error
        assert any("abacus://hamiltonian/" in ref for ref in validation.provenance_refs)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_no_energy_error_without_reference(self, tmp_path: Path) -> None:
        hamiltonian_file = _write_h2_fcidump(tmp_path)
        spec = _build_hamiltonian_spec(hamiltonian_file)

        compiler = QComputeConfigCompilerComponent()
        plan = compiler.build_plan_from_hamiltonian(spec)

        executor = QComputeExecutorComponent()
        await executor.activate(ComponentRuntime(storage_path=tmp_path))
        artifact = executor.execute_plan(plan)

        env_report = _build_environment_report(plan)
        validator = QComputeValidatorComponent()
        await validator.activate(ComponentRuntime(storage_path=tmp_path))
        validation = validator.validate_run(artifact, plan, env_report)

        # Without reference energy, energy_error should be None.
        assert validation.metrics.energy_error is None
