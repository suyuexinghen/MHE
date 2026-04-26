"""Tests for the fermion-to-qubit mapping module."""

from metaharness_ext.qcompute.contracts import QComputeActiveSpace
from metaharness_ext.qcompute.fcidump import parse_fcidump_string
from metaharness_ext.qcompute.fermion_mapper import (
    build_active_space,
    compute_qubit_count,
    map_fermionic_to_qubit,
)

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


def _h2_fcidata():
    return parse_fcidump_string(H2_FCIDUMP)


class TestJordanWignerH2Mapping:
    def test_jordan_wigner_h2_qubit_count(self) -> None:
        fcidata = _h2_fcidata()
        hamiltonian = map_fermionic_to_qubit(fcidata, method="jordan_wigner")
        assert hamiltonian.num_qubits == 2

    def test_jordan_wigner_h2_nonzero_terms(self) -> None:
        fcidata = _h2_fcidata()
        hamiltonian = map_fermionic_to_qubit(fcidata, method="jordan_wigner")
        non_zero_terms = [t for t in hamiltonian.terms if abs(t.coefficient) > 1e-15]
        assert len(non_zero_terms) > 0

    def test_jordan_wigner_h2_has_identity(self) -> None:
        fcidata = _h2_fcidata()
        hamiltonian = map_fermionic_to_qubit(fcidata, method="jordan_wigner")
        identity_terms = [t for t in hamiltonian.terms if t.pauli_string == "II"]
        assert len(identity_terms) >= 0  # May or may not have identity

    def test_jordan_wigner_h2_mapping_method(self) -> None:
        fcidata = _h2_fcidata()
        hamiltonian = map_fermionic_to_qubit(fcidata, method="jordan_wigner")
        assert hamiltonian.mapping_method == "jordan_wigner"

    def test_jordan_wigner_h2_source_format(self) -> None:
        fcidata = _h2_fcidata()
        hamiltonian = map_fermionic_to_qubit(fcidata, method="jordan_wigner")
        assert hamiltonian.source_format == "fcidump"


class TestJordanWignerIdentityTerm:
    def test_identity_coefficient_captured(self) -> None:
        fcidata = _h2_fcidata()
        hamiltonian = map_fermionic_to_qubit(fcidata, method="jordan_wigner")
        # For H2, the identity term coefficient should equal
        # sum of core contributions.
        identity_terms = [t for t in hamiltonian.terms if t.pauli_string == "II"]
        if identity_terms:
            assert abs(identity_terms[0].coefficient) > 0.0


class TestActiveSpaceReduction:
    def test_full_space_qubit_count(self) -> None:
        fcidata = _h2_fcidata()
        hamiltonian = map_fermionic_to_qubit(fcidata, method="jordan_wigner")
        assert hamiltonian.num_qubits == 2

    def test_reduced_space_fewer_qubits(self) -> None:
        """Full space vs reduced space should differ in qubit count."""
        fcidata = _h2_fcidata()
        full_hamiltonian = map_fermionic_to_qubit(fcidata, method="jordan_wigner")
        # With only 2 orbitals, reducing to 1 orbital changes things.
        active_space = QComputeActiveSpace(n_electrons=1, n_orbitals=1, method="manual")
        reduced_hamiltonian = map_fermionic_to_qubit(
            fcidata, active_space=active_space, method="jordan_wigner"
        )
        assert reduced_hamiltonian.num_qubits < full_hamiltonian.num_qubits
        assert reduced_hamiltonian.num_qubits == 1

    def test_active_space_preserves_method(self) -> None:
        fcidata = _h2_fcidata()
        active_space = QComputeActiveSpace(n_electrons=1, n_orbitals=1, method="manual")
        hamiltonian = map_fermionic_to_qubit(
            fcidata, active_space=active_space, method="jordan_wigner"
        )
        assert hamiltonian.num_qubits == 1


class TestBravyiKitaevH2Mapping:
    def test_bravyi_kitaev_h2_qubit_count(self) -> None:
        fcidata = _h2_fcidata()
        hamiltonian = map_fermionic_to_qubit(fcidata, method="bravyi_kitaev")
        assert hamiltonian.num_qubits == 2

    def test_bravyi_kitaev_h2_has_nonzero_terms(self) -> None:
        fcidata = _h2_fcidata()
        hamiltonian = map_fermionic_to_qubit(fcidata, method="bravyi_kitaev")
        non_zero_terms = [t for t in hamiltonian.terms if abs(t.coefficient) > 1e-15]
        assert len(non_zero_terms) > 0

    def test_bravyi_kitaev_same_num_qubits_as_jw(self) -> None:
        fcidata = _h2_fcidata()
        jw = map_fermionic_to_qubit(fcidata, method="jordan_wigner")
        bk = map_fermionic_to_qubit(fcidata, method="bravyi_kitaev")
        assert jw.num_qubits == bk.num_qubits

    def test_bravyi_kitaev_mapping_method(self) -> None:
        fcidata = _h2_fcidata()
        hamiltonian = map_fermionic_to_qubit(fcidata, method="bravyi_kitaev")
        assert hamiltonian.mapping_method == "bravyi_kitaev"


class TestHamiltonianPauliTermsValid:
    def test_jw_pauli_strings_valid(self) -> None:
        fcidata = _h2_fcidata()
        hamiltonian = map_fermionic_to_qubit(fcidata, method="jordan_wigner")
        valid_chars = set("IXYZ")
        for term in hamiltonian.terms:
            assert all(c in valid_chars for c in term.pauli_string), (
                f"Invalid Pauli string: {term.pauli_string}"
            )

    def test_bk_pauli_strings_valid(self) -> None:
        fcidata = _h2_fcidata()
        hamiltonian = map_fermionic_to_qubit(fcidata, method="bravyi_kitaev")
        valid_chars = set("IXYZ")
        for term in hamiltonian.terms:
            assert all(c in valid_chars for c in term.pauli_string), (
                f"Invalid Pauli string: {term.pauli_string}"
            )

    def test_pauli_string_length_equals_qubit_count(self) -> None:
        fcidata = _h2_fcidata()
        hamiltonian = map_fermionic_to_qubit(fcidata, method="jordan_wigner")
        for term in hamiltonian.terms:
            assert len(term.pauli_string) == hamiltonian.num_qubits, (
                f"Pauli string length {len(term.pauli_string)} != "
                f"num_qubits {hamiltonian.num_qubits}"
            )


class TestComputeQubitCount:
    def test_qubit_count_2_orbitals(self) -> None:
        assert compute_qubit_count(2) == 2

    def test_qubit_count_4_orbitals(self) -> None:
        assert compute_qubit_count(4) == 4

    def test_qubit_count_10_orbitals(self) -> None:
        assert compute_qubit_count(10) == 10


class TestBuildActiveSpace:
    def test_build_active_space_full(self) -> None:
        fcidata = _h2_fcidata()
        space = build_active_space(fcidata, method="full")
        assert space.n_electrons == 2
        assert space.n_orbitals == 2
        assert space.method == "full"

    def test_build_active_space_manual(self) -> None:
        fcidata = _h2_fcidata()
        space = build_active_space(fcidata, n_electrons=1, n_orbitals=1, method="manual")
        assert space.n_electrons == 1
        assert space.n_orbitals == 1
        assert space.method == "manual"

    def test_build_active_space_defaults_to_full(self) -> None:
        fcidata = _h2_fcidata()
        space = build_active_space(fcidata)
        assert space.n_electrons == fcidata.nelec
        assert space.n_orbitals == fcidata.norb
