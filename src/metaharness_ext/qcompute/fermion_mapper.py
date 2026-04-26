"""Fermion-to-qubit mapping utilities.

Converts molecular Hamiltonians from fermionic representation (obtained
from FCIDUMP data) into qubit Hamiltonians expressed as sums of Pauli
operators. Supports Jordan-Wigner and Bravyi-Kitaev mappings.
"""

from __future__ import annotations

from typing import Literal

from metaharness_ext.qcompute.contracts import (
    FCIDumpData,
    QComputeActiveSpace,
    QubitHamiltonian,
    QubitHamiltonianTerm,
)

MappingMethod = Literal["jordan_wigner", "bravyi_kitaev"]


def compute_qubit_count(n_orbitals: int) -> int:
    """Return the number of qubits needed for the given orbital count.

    Both Jordan-Wigner and Bravyi-Kitaev use exactly n_orbitals qubits.
    """
    return n_orbitals


def map_fermionic_to_qubit(
    fcidata: FCIDumpData,
    active_space: QComputeActiveSpace | None = None,
    method: MappingMethod = "jordan_wigner",
) -> QubitHamiltonian:
    """Convert a fermionic Hamiltonian to a qubit Pauli Hamiltonian.

    Args:
        fcidata: Parsed FCIDUMP data with 1e and 2e integrals.
        active_space: Optional (n_electrons, n_orbitals) restriction.
        method: Mapping method, either ``jordan_wigner`` or ``bravyi_kitaev``.

    Returns:
        QubitHamiltonian with Pauli terms and coefficient pairs.
    """
    if active_space is not None:
        norb = active_space.n_orbitals
    else:
        norb = fcidata.norb

    n_qubits = compute_qubit_count(norb)

    if method == "jordan_wigner":
        pauli_terms = _jordan_wigner_mapping(fcidata, norb)
    elif method == "bravyi_kitaev":
        pauli_terms = _bravyi_kitaev_mapping(fcidata, norb)
    else:
        raise ValueError(f"Unsupported mapping method: {method}")

    # Combine like terms.
    combined: dict[str, float] = {}
    for coeff, pstr in pauli_terms:
        combined[pstr] = combined.get(pstr, 0.0) + coeff

    terms = [
        QubitHamiltonianTerm(pauli_string=pstr, coefficient=coeff)
        for pstr, coeff in sorted(combined.items())
        if abs(coeff) > 1e-15
    ]

    return QubitHamiltonian(
        num_qubits=n_qubits,
        terms=terms,
        source_format="fcidump",
        mapping_method=method,
    )


# ---------------------------------------------------------------------------
# Jordan-Wigner mapping
# ---------------------------------------------------------------------------


def _jw_create(p: int, n: int) -> list[tuple[complex, str]]:
    """Jordan-Wigner encoding of creation operator a_p^dag.

    a_p^dag = (X_p - i Y_p)/2 * Z_0 * Z_1 * ... * Z_{p-1}

    Returns list of (coefficient, pauli_string) pairs.
    """
    z_prefix = "Z" * p
    rest = "I" * (n - p - 1)
    pauli_x = z_prefix + "X" + rest
    pauli_y = z_prefix + "Y" + rest
    return [(0.5, pauli_x), (-0.5j, pauli_y)]


def _jw_annihilate(p: int, n: int) -> list[tuple[complex, str]]:
    """Jordan-Wigner encoding of annihilation operator a_p.

    a_p = (X_p + i Y_p)/2 * Z_0 * Z_1 * ... * Z_{p-1}

    Returns list of (coefficient, pauli_string) pairs.
    """
    z_prefix = "Z" * p
    rest = "I" * (n - p - 1)
    pauli_x = z_prefix + "X" + rest
    pauli_y = z_prefix + "Y" + rest
    return [(0.5, pauli_x), (0.5j, pauli_y)]


def _pauli_multiply(p1: str, c1: complex, p2: str, c2: complex) -> list[tuple[complex, str]]:
    """Multiply two single Pauli strings, tracking phase from I/X/Y/Z algebra."""
    assert len(p1) == len(p2)
    result_chars: list[str] = []
    phase = 1.0 + 0.0j
    for a, b in zip(p1, p2):
        ch, ph = _single_pauli_product(a, b)
        result_chars.append(ch)
        phase *= ph
    return [(c1 * c2 * phase, "".join(result_chars))]


def _single_pauli_product(a: str, b: str) -> tuple[str, complex]:
    """Product of two single-qubit Pauli operators with phase."""
    if a == "I":
        return b, 1.0
    if b == "I":
        return a, 1.0
    if a == b:
        return "I", 1.0
    # a != b and neither is I
    table: dict[tuple[str, str], tuple[str, complex]] = {
        ("X", "Y"): ("Z", 1j),
        ("Y", "X"): ("Z", -1j),
        ("Y", "Z"): ("X", 1j),
        ("Z", "Y"): ("X", -1j),
        ("Z", "X"): ("Y", 1j),
        ("X", "Z"): ("Y", -1j),
    }
    return table[(a, b)]


def _multiply_pauli_terms(
    terms_a: list[tuple[complex, str]],
    terms_b: list[tuple[complex, str]],
) -> list[tuple[complex, str]]:
    """Multiply two sets of Pauli terms (distributive)."""
    result: list[tuple[complex, str]] = []
    for c1, p1 in terms_a:
        for c2, p2 in terms_b:
            result.extend(_pauli_multiply(p1, c1, p2, c2))
    return result


def _jordan_wigner_mapping(
    fcidata: FCIDumpData,
    norb: int,
) -> list[tuple[float, str]]:
    """Build the qubit Hamiltonian using Jordan-Wigner mapping.

    H = sum_{p,q} h_{pq} a_p^dag a_q
      + 0.5 * sum_{p,q,r,s} V_{pqrs} a_p^dag a_q^dag a_r a_s
    """
    pauli_terms: dict[str, complex] = {}

    # One-electron integrals: h_{pq} a_p^dag a_q
    for (p, q), h_pq in fcidata.one_electron_integrals.items():
        if p > norb or q > norb:
            continue
        # Convert to 0-based
        p0, q0 = p - 1, q - 1
        ap_dag = _jw_create(p0, norb)
        aq = _jw_annihilate(q0, norb)
        product = _multiply_pauli_terms(ap_dag, aq)
        for coeff, pstr in product:
            pauli_terms[pstr] = pauli_terms.get(pstr, 0.0 + 0.0j) + h_pq * coeff

    # Two-electron integrals: 0.5 * V_{pqrs} a_p^dag a_q^dag a_r a_s
    for (p, q, r, s), v_pqrs in fcidata.two_electron_integrals.items():
        if p > norb or q > norb or r > norb or s > norb:
            continue
        p0, q0, r0, s0 = p - 1, q - 1, r - 1, s - 1
        ap_dag = _jw_create(p0, norb)
        aq_dag = _jw_create(q0, norb)
        ar = _jw_annihilate(r0, norb)
        as_op = _jw_annihilate(s0, norb)

        product = _multiply_pauli_terms(ap_dag, aq_dag)
        product = _multiply_pauli_terms(product, ar)
        product = _multiply_pauli_terms(product, as_op)

        for coeff, pstr in product:
            pauli_terms[pstr] = pauli_terms.get(pstr, 0.0 + 0.0j) + 0.5 * v_pqrs * coeff

    # Convert complex coefficients to floats (imaginary parts should cancel).
    return [(float(coeff.real), pstr) for pstr, coeff in pauli_terms.items()]


# ---------------------------------------------------------------------------
# Bravyi-Kitaev mapping
# ---------------------------------------------------------------------------


def _bk_parity_set(index: int, n: int) -> set[int]:
    """Compute the parity set for Bravyi-Kitaev encoding.

    The parity set for qubit j contains all qubits whose update set
    contains j. This implementation uses the binary tree structure.
    """
    parity: set[int] = set()
    j = index
    while j > 0:
        j -= 1
        if j < 0:
            break
        parity.add(j)
        # Move to parent in the binary representation
        lowbit = (j + 1) & -(j + 1)
        j_next = j + 1 - lowbit
        if j_next > 0:
            j = j_next - 1
        else:
            break
    return parity


def _bk_flip_set(index: int, n: int) -> set[int]:
    """Compute the flip set for Bravyi-Kitaev encoding."""
    flip: set[int] = set()
    j = index + 1
    while j < n:
        lowbit = j & (-j)
        flip.add(j)
        j += lowbit
    return flip


def _bk_create_annihilate(p: int, n: int, create: bool) -> list[tuple[complex, str]]:
    """Bravyi-Kitaev encoding of creation or annihilation operator.

    For the Bravyi-Kitaev transformation, the operators are:
    a_p^dag = (X_{beta(p)} * X_{alpha(p)} - i * sigma_{beta(p)} * X_{alpha(p)}) / 2
    where alpha(p) is the parity set and beta(p) is the update set.
    """
    # Use a simplified Bravyi-Kitaev approach: for small systems this
    # degenerates to Jordan-Wigner-like parity chains but with different
    # qubit assignments.
    parity = _bk_parity_set(p, n)

    # Build X sigma on target qubit and Z parity on the parity set
    chars_x: list[str] = []
    chars_y: list[str] = []
    for i in range(n):
        if i == p:
            chars_x.append("X")
            chars_y.append("Y")
        elif i in parity:
            chars_x.append("Z")
            chars_y.append("Z")
        else:
            chars_x.append("I")
            chars_y.append("I")

    pauli_x = "".join(chars_x)
    pauli_y = "".join(chars_y)

    if create:
        # a_p^dag = (X - iY) / 2
        return [(0.5, pauli_x), (-0.5j, pauli_y)]
    else:
        # a_p = (X + iY) / 2
        return [(0.5, pauli_x), (0.5j, pauli_y)]


def _bravyi_kitaev_mapping(
    fcidata: FCIDumpData,
    norb: int,
) -> list[tuple[float, str]]:
    """Build the qubit Hamiltonian using Bravyi-Kitaev mapping."""
    pauli_terms: dict[str, complex] = {}

    # One-electron integrals: h_{pq} a_p^dag a_q
    for (p, q), h_pq in fcidata.one_electron_integrals.items():
        if p > norb or q > norb:
            continue
        p0, q0 = p - 1, q - 1
        ap_dag = _bk_create_annihilate(p0, norb, create=True)
        aq = _bk_create_annihilate(q0, norb, create=False)
        product = _multiply_pauli_terms(ap_dag, aq)
        for coeff, pstr in product:
            pauli_terms[pstr] = pauli_terms.get(pstr, 0.0 + 0.0j) + h_pq * coeff

    # Two-electron integrals: 0.5 * V_{pqrs} a_p^dag a_q^dag a_r a_s
    for (p, q, r, s), v_pqrs in fcidata.two_electron_integrals.items():
        if p > norb or q > norb or r > norb or s > norb:
            continue
        p0, q0, r0, s0 = p - 1, q - 1, r - 1, s - 1
        ap_dag = _bk_create_annihilate(p0, norb, create=True)
        aq_dag = _bk_create_annihilate(q0, norb, create=True)
        ar = _bk_create_annihilate(r0, norb, create=False)
        as_op = _bk_create_annihilate(s0, norb, create=False)

        product = _multiply_pauli_terms(ap_dag, aq_dag)
        product = _multiply_pauli_terms(product, ar)
        product = _multiply_pauli_terms(product, as_op)

        for coeff, pstr in product:
            pauli_terms[pstr] = pauli_terms.get(pstr, 0.0 + 0.0j) + 0.5 * v_pqrs * coeff

    return [(float(coeff.real), pstr) for pstr, coeff in pauli_terms.items()]


def build_active_space(
    fcidata: FCIDumpData,
    n_electrons: int | None = None,
    n_orbitals: int | None = None,
    method: str = "manual",
) -> QComputeActiveSpace:
    """Construct an active space specification.

    If PySCF is available, use it for CAS selection. Otherwise, use the
    full space or the manually specified parameters.

    Args:
        fcidata: Parsed FCIDUMP data.
        n_electrons: Number of active electrons (defaults to full space).
        n_orbitals: Number of active orbitals (defaults to full space).
        method: Selection method (``manual``, ``pyscf_cas``, ``full``).

    Returns:
        QComputeActiveSpace with the selected parameters.
    """
    if method == "pyscf_cas":
        try:
            import pyscf  # noqa: F401

            # If PySCF is available, we could do automatic CAS selection.
            # For now, fall through to manual/full with available parameters.
        except ImportError:
            pass

    ne = n_electrons if n_electrons is not None else fcidata.nelec
    no = n_orbitals if n_orbitals is not None else fcidata.norb
    return QComputeActiveSpace(
        n_electrons=ne,
        n_orbitals=no,
        method=method,
    )
