from __future__ import annotations

from typing import Any

from metaharness.benchmark_drivers.models import BenchmarkCaseSpec, MetricReference

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

ABACUS_H2_SOURCE_REFS = [
    "/home/linden/Obsidian Vault/AI4S-Agent-Book/downloads/ABACUS-agent-tools/tests/integrate_test/abacus_inputs_dirs/H2/INPUT",
    "/home/linden/Obsidian Vault/AI4S-Agent-Book/downloads/ABACUS-agent-tools/tests/integrate_test/abacus_inputs_dirs/H2/STRU_relaxed",
    "/home/linden/Obsidian Vault/AI4S-Agent-Book/downloads/abacus-develop/tests/01_PW/083_PW_sol_H2/INPUT",
    "/home/linden/Obsidian Vault/AI4S-Agent-Book/downloads/abacus-develop/tests/01_PW/083_PW_sol_H2/STRU",
]

ABACUS_HS_SOURCE_REFS = [
    "/home/linden/Obsidian Vault/AI4S-Agent-Book/downloads/abacus-develop/examples/10_hs_matrix/out_hs_multik/INPUT",
    "/home/linden/Obsidian Vault/AI4S-Agent-Book/downloads/abacus-develop/examples/10_hs_matrix/out_hs2_multik/INPUT",
    "/home/linden/Obsidian Vault/AI4S-Agent-Book/downloads/abacus-develop/tests/02_NAO_Gamma/scf_out_hk/INPUT",
    "/home/linden/Obsidian Vault/AI4S-Agent-Book/downloads/abacus-develop/tests/03_NAO_multik/scf_out_hsk/INPUT",
    "/home/linden/Obsidian Vault/AI4S-Agent-Book/downloads/abacus-develop/tests/03_NAO_multik/scf_out_hsr/INPUT",
]

COMMON_H2_PROBLEM: dict[str, Any] = {
    "backend": "qiskit_aer",
    "simulator": True,
    "hamiltonian_format": "fcidump",
    "ansatz": "vqe",
    "num_qubits": 2,
    "backend_qubit_count": 4,
    "shots": 256,
    "active_space": [2, 2],
    "reference_energy": -1.137,
    "max_iterations": 5,
}


def qcompute_abacus_case_catalog() -> dict[str, BenchmarkCaseSpec]:
    cases = [
        BenchmarkCaseSpec(
            case_id="h2-fcidump-vqe-proxy",
            suite="qcompute-abacus",
            task_family="qcompute_abacus_hamiltonian_proxy",
            description=(
                "H2 FCIDUMP Hamiltonian proxy compiled through QCompute VQE with ABACUS "
                "input provenance."
            ),
            required_capabilities=["qiskit_aer", "qcompute_hamiltonian_compile"],
            source_reference={
                "abacus_source_refs": ABACUS_H2_SOURCE_REFS,
                "hamiltonian_fixture": "embedded_h2_sto3g_fcidump",
            },
            expected_metrics=[
                "energy",
                "energy_error",
                "convergence_iterations",
                "num_qubits",
                "term_count",
                "shots_completed",
                "elapsed_seconds",
            ],
            reference_metrics={
                "energy_error": MetricReference(value=0.0, tolerance=10.0),
                "convergence_iterations": MetricReference(value=5.0, tolerance=0.0),
                "num_qubits": MetricReference(value=2.0, tolerance=0.0),
            },
            problem_definition={**COMMON_H2_PROBLEM, "fermion_mapping": "jordan_wigner"},
            metadata={"proxy": True, "molecule": "H2", "basis": "STO-3G"},
        ),
        BenchmarkCaseSpec(
            case_id="h2-fcidump-jw-vs-bk",
            suite="qcompute-abacus",
            task_family="qcompute_abacus_mapping_comparison",
            description="Compare Jordan-Wigner and Bravyi-Kitaev metadata for the H2 FCIDUMP proxy.",
            required_capabilities=["qcompute_hamiltonian_compile"],
            source_reference={
                "abacus_source_refs": ABACUS_H2_SOURCE_REFS,
                "hamiltonian_fixture": "embedded_h2_sto3g_fcidump",
            },
            expected_metrics=[
                "jw_num_qubits",
                "jw_term_count",
                "bk_num_qubits",
                "bk_term_count",
                "elapsed_seconds",
            ],
            reference_metrics={
                "jw_num_qubits": MetricReference(value=2.0, tolerance=0.0),
                "bk_num_qubits": MetricReference(value=2.0, tolerance=0.0),
            },
            problem_definition={**COMMON_H2_PROBLEM, "fermion_mapping": "jordan_wigner"},
            metadata={"proxy": True, "comparison": "fermion_mapping"},
        ),
        BenchmarkCaseSpec(
            case_id="abacus-hs-bridge-pending",
            suite="qcompute-abacus",
            task_family="qcompute_abacus_hs_bridge",
            description="ABACUS H/S matrix source refs kept as an explicit unsupported bridge sentinel.",
            required_capabilities=["abacus_hs_to_fcidump_bridge"],
            source_reference={"abacus_hs_source_refs": ABACUS_HS_SOURCE_REFS},
            expected_metrics=["elapsed_seconds"],
            problem_definition={
                "source_format": "abacus_hs_matrix",
                "target_format": "fcidump_or_qubit_hamiltonian",
                "status": "unsupported_source_format",
            },
            metadata={
                "bridge_status": "converter_missing",
                "source_format": "abacus_hs_matrix",
                "promotion_requirements": [
                    "parse ABACUS out_mat_hs/out_mat_hs2 fixtures",
                    "convert H/S metadata to FCIDUMP or QCompute Pauli dictionary",
                    "validate converted Hamiltonian against a scientific reference",
                ],
                "unsupported_reason": "ABACUS H/S-to-FCIDUMP or qubit-Hamiltonian bridge is not implemented.",
            },
            capability_gated=True,
        ),
    ]
    return {case.case_id: case for case in cases}


def get_qcompute_abacus_cases(case_ids: list[str] | None = None) -> list[BenchmarkCaseSpec]:
    catalog = qcompute_abacus_case_catalog()
    if not case_ids:
        return list(catalog.values())
    return [catalog[case_id] for case_id in case_ids]
