from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from metaharness_ext.qcompute.contracts import QubitHamiltonian, QubitHamiltonianTerm

HS_OUTPUT_KEYS = {"out_mat_hs", "out_mat_hs2", "out_mat_hsR", "out_mat_t", "out_mat_r"}
HS_ARTIFACT_PATTERNS = ("*.csr", "*.csr.ref", "*.txt", "*.txt.ref")
INPUT_METADATA_KEYS = {
    "basis_type",
    "calculation",
    "ecutwfc",
    "gamma_only",
    "ks_solver",
    "nbands",
    "out_mat_hs",
    "out_mat_hs2",
    "out_mat_hsR",
    "out_mat_r",
    "out_mat_t",
    "scf_nmax",
    "scf_thr",
    "suffix",
    "symmetry",
}


class AbacusHSMatrixMetadata(BaseModel):
    path: str
    exists: bool
    kind: Literal["abacus_hs_matrix"] = "abacus_hs_matrix"
    format_family: str = "unknown"
    matrix_role: str = "unknown"
    conversion_status: Literal["unsupported"] = "unsupported"
    parse_status: Literal["artifact_missing", "metadata_only", "header_parsed"] = "artifact_missing"
    artifact_name: str | None = None
    suffix: str | None = None
    is_sparse: bool = False
    bytes: int | None = None
    line_count: int | None = None
    nonempty_line_count: int | None = None
    shape: list[int] | None = None
    nnz: int | None = None
    parser_contract_status: Literal["blocked", "metadata_only", "header_parsed"] = "blocked"
    validation_blockers: list[str] = Field(default_factory=list)


class AbacusHSReadinessGate(BaseModel):
    stage: Literal[
        "R1_parser", "R2_conversion", "R3_scientific_validation", "R4_benchmark_promotion"
    ]
    status: Literal["blocked", "metadata_only", "not_started"]
    required_evidence: list[str] = Field(default_factory=list)
    claim_boundary: str


class AbacusHSConversionResult(BaseModel):
    status: Literal["unsupported", "converted"]
    target_format: Literal["fcidump", "qcompute_pauli_dict"] = "fcidump"
    fcidump_text: str | None = None
    qubit_hamiltonian: QubitHamiltonian | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    unsupported_reason: str | None = None


class AbacusHSEigenproblemValidation(BaseModel):
    status: Literal["blocked", "reference_passed", "reference_failed"] = "blocked"
    validation_kind: str = "small_dense_hs_eigenproblem"
    source_ref: str | None = None
    reference_fixture: bool = False
    reference_validated: bool = False
    scientifically_validated: bool = False
    promotion_ready: bool = False
    matrix_dimension: int | None = None
    eigenvalues: list[float] = Field(default_factory=list)
    reference_eigenvalues: list[float] = Field(default_factory=list)
    tolerance: float | None = None
    max_eigenvalue_error: float | None = None
    residual_norms: list[float] = Field(default_factory=list)
    max_residual_norm: float | None = None
    blockers: list[str] = Field(default_factory=list)
    claim_boundary: str = (
        "Small dense H/S reference validation tests the validator contract only; "
        "it does not validate production ABACUS H/S conversion or quantum advantage."
    )


class AbacusHSConversionPlan(BaseModel):
    source_format: str = "abacus_hs_matrix"
    target_format: Literal["fcidump", "qcompute_pauli_dict"] = "qcompute_pauli_dict"
    status: Literal["unsupported", "metadata_only", "ready"] = "unsupported"
    accepted_artifacts: list[str] = Field(
        default_factory=lambda: ["INPUT", "out_mat_hs", "out_mat_hs2"]
    )
    required_metadata: list[str] = Field(
        default_factory=lambda: ["basis_type", "gamma_only", "ks_solver", "hs_output_keys"]
    )
    validation_requirements: list[str] = Field(
        default_factory=lambda: [
            "matrix shape and sparsity parsed",
            "basis/k-point/spin metadata attached",
            "Hermiticity or documented non-Hermitian handling checked",
            "converted operator validated by QCompute parser",
            "reference energy or spectrum comparison recorded",
        ]
    )
    unsupported_reason: str = (
        "Only validated proxy conversion is implemented; scientific conversion is blocked."
    )


class AbacusHSApprovalManifest(BaseModel):
    status: Literal["missing", "approved", "invalid"] = "missing"
    approved_by: str | None = None
    approval_role: str | None = None
    fixture_refs: list[str] = Field(default_factory=list)
    tolerance_table_ref: str | None = None
    reference_observable: str | None = None
    notes: list[str] = Field(default_factory=list)


class AbacusHSPromotionGate(BaseModel):
    status: Literal["blocked", "ready"] = "blocked"
    promotion_ready: bool = False
    required_artifacts: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    missing_evidence_by_category: dict[str, list[str]] = Field(default_factory=dict)
    claim_boundary_ok: bool = True
    sentinel_must_remain_skipped: bool = True


class AbacusHSReviewSignoff(BaseModel):
    reviewer_backend: str = "deterministic_policy"
    decision: Literal["approve", "block", "defer"] = "block"
    claim_boundary_ok: bool = True
    reviewer_evidence_only: bool = True
    replaces_human_scientific_signoff: bool = False
    sentinel_must_remain_skipped: bool = True
    accepted_evidence: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class AbacusHSBridgeStatus(BaseModel):
    case_id: str
    source_format: str = "abacus_hs_matrix"
    target_format: str = "fcidump_or_qubit_hamiltonian"
    status: Literal[
        "source_refs_recorded",
        "fixture_missing",
        "metadata_parsed",
        "converter_missing",
        "validated_conversion_available",
    ] = "converter_missing"
    source_refs: list[str] = Field(default_factory=list)
    parsed_metadata: dict[str, Any] = Field(default_factory=dict)
    matrix_metadata: list[dict[str, Any]] = Field(default_factory=list)
    conversion_plan: AbacusHSConversionPlan = Field(default_factory=AbacusHSConversionPlan)
    readiness_gates: list[AbacusHSReadinessGate] = Field(default_factory=list)
    promotion_ready: bool = False
    missing_capabilities: list[str] = Field(
        default_factory=lambda: ["abacus_hs_parser", "abacus_hs_to_fcidump_converter"]
    )
    failure_code: str = "converter_missing"
    skip_reason: str = "ABACUS H/S-to-FCIDUMP or qubit-Hamiltonian bridge is not implemented."
    reason: str = "ABACUS H/S-to-FCIDUMP or qubit-Hamiltonian bridge is not implemented."


def build_abacus_hs_bridge_status(
    *,
    case_id: str,
    source_reference: str | dict[str, Any],
    reason: str | None = None,
) -> AbacusHSBridgeStatus:
    source_refs = _source_refs(source_reference)
    parsed_metadata = parse_abacus_input_refs(source_refs)
    discovered_matrix_refs = discover_abacus_hs_matrix_refs(parsed_metadata)
    matrix_metadata = parse_abacus_hs_matrix_refs(source_refs + discovered_matrix_refs)
    metadata_available = any(
        ref.get("exists") and ref.get("hs_output_keys") for ref in parsed_metadata
    )
    skip_reason = reason or AbacusHSBridgeStatus.model_fields["reason"].default
    return AbacusHSBridgeStatus(
        case_id=case_id,
        status="converter_missing" if metadata_available else "fixture_missing",
        source_refs=source_refs,
        parsed_metadata={"input_refs": parsed_metadata},
        matrix_metadata=matrix_metadata,
        conversion_plan=build_abacus_hs_conversion_plan(metadata_available=metadata_available),
        readiness_gates=build_abacus_hs_readiness_gates(metadata_available=metadata_available),
        missing_capabilities=["abacus_hs_to_fcidump_converter"],
        failure_code="converter_missing" if metadata_available else "fixture_missing",
        skip_reason=skip_reason,
        reason=skip_reason,
    )


def build_abacus_hs_conversion_plan(*, metadata_available: bool) -> AbacusHSConversionPlan:
    return AbacusHSConversionPlan(status="ready" if metadata_available else "unsupported")


def build_abacus_hs_readiness_gates(*, metadata_available: bool) -> list[AbacusHSReadinessGate]:
    parser_status = "metadata_only" if metadata_available else "blocked"
    conversion_status = "metadata_only" if metadata_available else "blocked"
    return [
        AbacusHSReadinessGate(
            stage="R1_parser",
            status=parser_status,
            required_evidence=[
                "shape and nnz parsed from real ABACUS H/S artifact",
                "spin/k-point/basis metadata attached",
                "parser failure taxonomy covered by tests",
            ],
            claim_boundary="H/S artifacts may be inventoried, but real matrix parsing is not complete.",
        ),
        AbacusHSReadinessGate(
            stage="R2_conversion",
            status=conversion_status,
            required_evidence=[
                "QCompute pauli_dict proxy target contract",
                "real artifact proxy conversion tests",
                "unsupported states preserved for unrecognized formats",
            ],
            claim_boundary="Only proxy conversion is available; scientific ABACUS H/S conversion remains unvalidated.",
        ),
        AbacusHSReadinessGate(
            stage="R3_scientific_validation",
            status="not_started",
            required_evidence=[
                "administrator-approved reference fixture",
                "tolerance table",
                "scientific reviewer sign-off",
            ],
            claim_boundary="No scientific numerical correctness claim is allowed.",
        ),
        AbacusHSReadinessGate(
            stage="R4_benchmark_promotion",
            status="blocked",
            required_evidence=[
                "real-mode executable bridge summary",
                "comparison bundle with repeated-run stability",
                "non-dry-run QCompute validation artifacts",
            ],
            claim_boundary="The sentinel must remain capability-skipped until R2 and R3 pass.",
        ),
    ]


def convert_toy_abacus_hs_fixture_to_fcidump(text: str) -> AbacusHSConversionResult:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines or lines[0] != "ABACUS_HS_TOY":
        return AbacusHSConversionResult(
            status="unsupported",
            unsupported_reason="Only ABACUS_HS_TOY fixture conversion is implemented.",
        )
    try:
        norb = _toy_header_int(lines, "norb")
        nelec = _toy_header_int(lines, "nelec")
        matrix = _toy_matrix(lines, norb)
    except ValueError as exc:
        return AbacusHSConversionResult(status="unsupported", unsupported_reason=str(exc))
    fcidump_lines = [
        f" &FCI NORB={norb},NELEC={nelec},MS2=0,",
        "   ORBSYM=" + ",".join("1" for _ in range(norb)) + ",",
        "   ISYM=1,",
        " &END",
    ]
    for row_index, row in enumerate(matrix, start=1):
        for column_index, value in enumerate(row, start=1):
            if value != 0.0:
                fcidump_lines.append(f" {value:.12f}  {row_index}  {column_index}  0  0")
    fcidump_lines.append(" 0.000000000000  0  0  0  0")
    return AbacusHSConversionResult(
        status="converted",
        fcidump_text="\n".join(fcidump_lines) + "\n",
        metadata={
            "fixture_format": "ABACUS_HS_TOY",
            "norb": norb,
            "nelec": nelec,
            "two_electron_terms": 0,
            "scientifically_validated": False,
        },
    )


def parse_abacus_input_refs(source_refs: list[str]) -> list[dict[str, Any]]:
    return [parse_abacus_input_ref(source_ref) for source_ref in source_refs]


def validate_abacus_hs_small_dense_eigenproblem(source_ref: str) -> AbacusHSEigenproblemValidation:
    path = Path(source_ref)
    if not path.exists():
        return AbacusHSEigenproblemValidation(
            source_ref=source_ref,
            blockers=["reference_fixture_missing"],
        )
    try:
        fixture = _parse_small_dense_hs_reference_fixture(path.read_text())
        eigenvalues, residual_norms = _solve_two_by_two_generalized_eigenproblem(
            fixture["h_matrix"], fixture["s_matrix"]
        )
    except ValueError as exc:
        return AbacusHSEigenproblemValidation(
            source_ref=source_ref,
            blockers=[str(exc), "scientific_reviewer_signoff_missing"],
        )
    reference = fixture["reference_eigenvalues"]
    tolerance = fixture["tolerance"]
    errors = [abs(value - expected) for value, expected in zip(eigenvalues, reference, strict=True)]
    max_error = max(errors) if errors else None
    max_residual = max(residual_norms) if residual_norms else None
    passed = max_error is not None and max_error <= tolerance
    blockers = ["scientific_reviewer_signoff_missing", "production_converter_missing"]
    if not passed:
        blockers.insert(0, "reference_eigenvalue_tolerance_failed")
    return AbacusHSEigenproblemValidation(
        status="reference_passed" if passed else "reference_failed",
        source_ref=source_ref,
        reference_fixture=True,
        reference_validated=passed,
        scientifically_validated=False,
        promotion_ready=False,
        matrix_dimension=2,
        eigenvalues=eigenvalues,
        reference_eigenvalues=reference,
        tolerance=tolerance,
        max_eigenvalue_error=max_error,
        residual_norms=residual_norms,
        max_residual_norm=max_residual,
        blockers=blockers,
    )


def build_abacus_hs_bridge_validation(
    source_reference: str | dict[str, Any],
) -> AbacusHSEigenproblemValidation:
    for source_ref in _source_refs(source_reference):
        path = Path(source_ref)
        if path.exists() and path.name.endswith(".hsref"):
            return validate_abacus_hs_small_dense_eigenproblem(source_ref)
    return AbacusHSEigenproblemValidation(
        blockers=[
            "administrator_approved_reference_fixture_missing",
            "tolerance_table_missing",
            "scientific_reviewer_signoff_missing",
            "production_converter_missing",
        ]
    )


def build_abacus_hs_approval_manifest(
    source_reference: str | dict[str, Any],
) -> AbacusHSApprovalManifest:
    for source_ref in _source_refs(source_reference):
        path = Path(source_ref)
        if path.exists() and path.name == "abacus_hs_approval.json":
            return _parse_abacus_hs_approval_manifest(path)
    return AbacusHSApprovalManifest(
        notes=["No abacus_hs_approval.json approval manifest was provided."]
    )


def build_abacus_hs_review_signoff(
    *,
    bridge_status: AbacusHSBridgeStatus,
    bridge_validation: AbacusHSEigenproblemValidation,
    reviewer_backend: str = "deterministic_policy",
) -> AbacusHSReviewSignoff:
    accepted_evidence = ["bridge_status.json", "bridge_validation.json"]
    missing_evidence = list(
        dict.fromkeys([*bridge_validation.blockers, *bridge_status.missing_capabilities])
    )
    decision: Literal["approve", "block", "defer"] = "block" if missing_evidence else "defer"
    return AbacusHSReviewSignoff(
        reviewer_backend=reviewer_backend,
        decision=decision,
        claim_boundary_ok=True,
        reviewer_evidence_only=True,
        replaces_human_scientific_signoff=False,
        sentinel_must_remain_skipped=True,
        accepted_evidence=accepted_evidence,
        missing_evidence=missing_evidence,
        notes=[
            "Reviewer signoff is evidence-review only and does not replace human scientific approval.",
            "ACP-connected Claude Code may populate this schema after JSON diagnostic passes.",
            "Production ABACUS H/S conversion remains blocked until missing evidence is resolved.",
        ],
    )


def build_abacus_hs_promotion_gate(
    *,
    bridge_status: AbacusHSBridgeStatus,
    bridge_validation: AbacusHSEigenproblemValidation,
    review_signoff: AbacusHSReviewSignoff,
    approval_manifest: AbacusHSApprovalManifest,
) -> AbacusHSPromotionGate:
    required_artifacts = [
        "bridge_status.json",
        "bridge_validation.json",
        "review_signoff.json",
        "abacus_hs_approval.json",
        "production_converter_evidence",
        "real_mode_repeat_summary",
    ]
    missing_evidence_by_category = {
        "human_approval": [],
        "scientific_validation": [],
        "production_converter": [],
        "real_repeat_evidence": ["real_mode_repeat_summary_missing"],
    }
    if approval_manifest.status != "approved":
        missing_evidence_by_category["human_approval"].append(
            "human_scientific_approval_manifest_missing"
        )
    for blocker in [*bridge_validation.blockers, *review_signoff.missing_evidence]:
        if blocker in {
            "administrator_approved_reference_fixture_missing",
            "tolerance_table_missing",
            "scientific_reviewer_signoff_missing",
        }:
            missing_evidence_by_category["scientific_validation"].append(blocker)
        if blocker in {"production_converter_missing", "abacus_hs_to_fcidump_converter"}:
            missing_evidence_by_category["production_converter"].append(blocker)
    for capability in bridge_status.missing_capabilities:
        missing_evidence_by_category["production_converter"].append(capability)
    missing_evidence_by_category = {
        category: list(dict.fromkeys(items))
        for category, items in missing_evidence_by_category.items()
    }
    missing_evidence = list(
        dict.fromkeys(item for items in missing_evidence_by_category.values() for item in items)
    )
    return AbacusHSPromotionGate(
        status="ready" if not missing_evidence else "blocked",
        promotion_ready=not missing_evidence,
        required_artifacts=required_artifacts,
        missing_evidence=missing_evidence,
        missing_evidence_by_category=missing_evidence_by_category,
        claim_boundary_ok=True,
        sentinel_must_remain_skipped=bool(missing_evidence),
    )


def convert_abacus_hs_header_to_pauli_proxy(source_ref: str) -> AbacusHSConversionResult:
    metadata = parse_abacus_hs_matrix_ref(source_ref)
    if not metadata.get("exists"):
        return AbacusHSConversionResult(
            status="unsupported",
            target_format="qcompute_pauli_dict",
            unsupported_reason="ABACUS H/S artifact does not exist.",
            metadata={"source_ref": source_ref},
        )
    if metadata.get("matrix_role") != "H":
        return AbacusHSConversionResult(
            status="unsupported",
            target_format="qcompute_pauli_dict",
            unsupported_reason="Only H matrix artifacts can be converted into a Hamiltonian proxy.",
            metadata={"source_ref": source_ref, "matrix_metadata": metadata},
        )
    diagonal_terms = _parse_diagonal_proxy_terms(Path(source_ref), metadata)
    if not diagonal_terms:
        return AbacusHSConversionResult(
            status="unsupported",
            target_format="qcompute_pauli_dict",
            unsupported_reason="No diagonal numeric terms could be extracted for proxy conversion.",
            metadata={"source_ref": source_ref, "matrix_metadata": metadata},
        )
    num_qubits = max(1, min(8, math.ceil(math.log2(max(2, len(diagonal_terms))))))
    terms = [QubitHamiltonianTerm(pauli_string="I" * num_qubits, coefficient=diagonal_terms[0])]
    for index, value in enumerate(diagonal_terms[1 : num_qubits + 1]):
        paulis = ["I"] * num_qubits
        paulis[index] = "Z"
        terms.append(QubitHamiltonianTerm(pauli_string="".join(paulis), coefficient=value))
    qubit_hamiltonian = QubitHamiltonian(
        num_qubits=num_qubits,
        terms=terms,
        source_format="abacus_hs_header_proxy",
        mapping_method="diagonal_z_proxy",
    )
    return AbacusHSConversionResult(
        status="converted",
        target_format="qcompute_pauli_dict",
        qubit_hamiltonian=qubit_hamiltonian,
        metadata={
            "source_ref": source_ref,
            "matrix_metadata": metadata,
            "conversion_kind": "diagonal_header_proxy",
            "scientifically_validated": False,
            "claim_boundary": "Proxy conversion is for QCompute pipeline contract testing only.",
        },
    )


def discover_abacus_hs_matrix_refs(input_metadata: list[dict[str, Any]]) -> list[str]:
    discovered: list[str] = []
    seen: set[str] = set()
    for metadata in input_metadata:
        if not metadata.get("exists") or not metadata.get("hs_output_keys"):
            continue
        input_path = Path(str(metadata["path"]))
        for search_root in _hs_artifact_search_roots(input_path, metadata):
            if not search_root.exists() or not search_root.is_dir():
                continue
            for pattern in HS_ARTIFACT_PATTERNS:
                for artifact_path in search_root.glob(pattern):
                    artifact = str(artifact_path)
                    if artifact not in seen and _matrix_format_family(artifact_path) != "unknown":
                        seen.add(artifact)
                        discovered.append(artifact)
    return discovered


def parse_abacus_hs_matrix_refs(source_refs: list[str]) -> list[dict[str, Any]]:
    return [
        metadata
        for ref in source_refs
        if (metadata := parse_abacus_hs_matrix_ref(ref))["exists"]
        and metadata["format_family"] != "unknown"
    ]


def parse_abacus_hs_matrix_ref(source_ref: str) -> dict[str, Any]:
    path = Path(source_ref)
    metadata = AbacusHSMatrixMetadata(
        path=source_ref,
        exists=path.exists(),
        format_family=_matrix_format_family(path),
        matrix_role=_matrix_role(path),
        parse_status="metadata_only" if path.exists() else "artifact_missing",
        parser_contract_status="metadata_only" if path.exists() else "blocked",
    )
    if not path.exists():
        return metadata.model_dump(mode="json")
    text = path.read_text(errors="replace")
    lines = text.splitlines()
    nonempty_lines = [line for line in lines if line.strip()]
    metadata.artifact_name = path.name
    metadata.suffix = path.suffix
    metadata.is_sparse = path.suffix in {".csr", ".ref"} and "csr" in path.name.lower()
    metadata.bytes = path.stat().st_size
    metadata.line_count = len(lines)
    metadata.nonempty_line_count = len(nonempty_lines)
    metadata.shape = _parse_matrix_shape(nonempty_lines)
    metadata.nnz = _parse_matrix_nnz(nonempty_lines)
    if metadata.shape is not None and metadata.nnz is not None:
        metadata.parse_status = "header_parsed"
        metadata.parser_contract_status = "header_parsed"
    metadata.validation_blockers = _matrix_validation_blockers(metadata)
    return metadata.model_dump(mode="json")


def parse_abacus_input_ref(source_ref: str) -> dict[str, Any]:
    path = Path(source_ref)
    metadata: dict[str, Any] = {
        "path": source_ref,
        "exists": path.exists(),
        "kind": "abacus_input",
        "parameters": {},
        "hs_output_keys": [],
    }
    if not path.exists() or path.name != "INPUT":
        return metadata
    parameters = _parse_input_parameters(path.read_text())
    hs_output_keys = sorted(key for key in parameters if key in HS_OUTPUT_KEYS)
    metadata["parameters"] = {
        key: parameters[key] for key in sorted(parameters) if key in INPUT_METADATA_KEYS
    }
    metadata["hs_output_keys"] = hs_output_keys
    metadata["bridge_parse_status"] = "metadata_parsed" if hs_output_keys else "no_hs_output_flag"
    return metadata


def _hs_artifact_search_roots(input_path: Path, metadata: dict[str, Any]) -> list[Path]:
    parent = input_path.parent
    roots = [parent]
    suffix_values = metadata.get("parameters", {}).get("suffix", [])
    for suffix in suffix_values:
        roots.append(parent / f"OUT.{suffix}")
    return roots


def _parse_matrix_shape(lines: list[str]) -> list[int] | None:
    rows: int | None = None
    columns: int | None = None
    for line in lines[:12]:
        lowered = line.lower().lstrip("# ")
        if lowered.startswith("matrix dimension"):
            values = _integer_tokens(line)
            if values:
                return [values[-1], values[-1]]
        if lowered.startswith("rows"):
            values = _integer_tokens(line)
            if values:
                rows = values[-1]
        if lowered.startswith("columns"):
            values = _integer_tokens(line)
            if values:
                columns = values[-1]
    if rows is not None and columns is not None:
        return [rows, columns]
    for line in lines[:5]:
        values = _integer_tokens(line)
        if len(values) >= 2 and all(value > 0 for value in values[:2]):
            return values[:2]
    return None


def _parse_matrix_nnz(lines: list[str]) -> int | None:
    for line in lines[:12]:
        lowered = line.lower().lstrip("# ")
        if lowered.startswith("matrix number"):
            values = _integer_tokens(line)
            if values:
                return values[-1]
    for line in lines[:5]:
        values = _integer_tokens(line)
        if len(values) >= 3 and values[2] >= 0:
            return values[2]
    return None


def _parse_diagonal_proxy_terms(path: Path, metadata: dict[str, Any]) -> list[float]:
    lines = path.read_text(errors="replace").splitlines()
    if metadata.get("format_family") == "abacus_text_matrix":
        return _parse_text_matrix_row_starts(lines)
    return _parse_sparse_matrix_block_values(lines)


def _parse_abacus_hs_approval_manifest(path: Path) -> AbacusHSApprovalManifest:
    try:
        payload = json.loads(path.read_text())
        manifest = AbacusHSApprovalManifest.model_validate(payload)
    except (ValueError, TypeError) as exc:
        return AbacusHSApprovalManifest(
            status="invalid",
            notes=[f"approval_manifest_parse_failed: {exc}"],
        )
    missing = []
    if not manifest.approved_by:
        missing.append("approved_by_missing")
    if not manifest.approval_role:
        missing.append("approval_role_missing")
    if not manifest.fixture_refs:
        missing.append("fixture_refs_missing")
    if not manifest.tolerance_table_ref:
        missing.append("tolerance_table_ref_missing")
    if not manifest.reference_observable:
        missing.append("reference_observable_missing")
    if missing:
        return manifest.model_copy(
            update={"status": "invalid", "notes": [*manifest.notes, *missing]}
        )
    return manifest.model_copy(update={"status": "approved"})


def _parse_small_dense_hs_reference_fixture(text: str) -> dict[str, Any]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines or lines[0] != "ABACUS_HS_DENSE_REFERENCE":
        raise ValueError("unsupported_reference_fixture_format")
    tolerance = _reference_float(lines, "tolerance")
    reference_eigenvalues = _reference_float_list(lines, "reference_eigenvalues")
    h_matrix = _reference_matrix(lines, "h_matrix", 2)
    s_matrix = _reference_matrix(lines, "s_matrix", 2)
    if len(reference_eigenvalues) != 2:
        raise ValueError("reference_eigenvalue_count_mismatch")
    _ensure_symmetric_matrix(h_matrix, "h_matrix")
    _ensure_symmetric_matrix(s_matrix, "s_matrix")
    return {
        "h_matrix": h_matrix,
        "s_matrix": s_matrix,
        "reference_eigenvalues": sorted(reference_eigenvalues),
        "tolerance": tolerance,
    }


def _solve_two_by_two_generalized_eigenproblem(
    h_matrix: list[list[float]], s_matrix: list[list[float]]
) -> tuple[list[float], list[float]]:
    s00, s01 = s_matrix[0]
    s10, s11 = s_matrix[1]
    det_s = s00 * s11 - s01 * s10
    if det_s <= 0.0 or s00 <= 0.0:
        raise ValueError("overlap_matrix_not_positive_definite")
    h00, h01 = h_matrix[0]
    h10, h11 = h_matrix[1]
    a = s00 * s11 - s01 * s10
    b = -(h00 * s11 + h11 * s00 - h01 * s10 - h10 * s01)
    c = h00 * h11 - h01 * h10
    discriminant = b * b - 4.0 * a * c
    if discriminant < 0.0:
        raise ValueError("generalized_eigenproblem_has_complex_roots")
    root = math.sqrt(discriminant)
    eigenvalues = sorted([(-b - root) / (2.0 * a), (-b + root) / (2.0 * a)])
    residual_norms = [
        _two_by_two_generalized_residual(h_matrix, s_matrix, value) for value in eigenvalues
    ]
    return eigenvalues, residual_norms


def _two_by_two_generalized_residual(
    h_matrix: list[list[float]], s_matrix: list[list[float]], eigenvalue: float
) -> float:
    shifted = [
        [
            h_matrix[0][0] - eigenvalue * s_matrix[0][0],
            h_matrix[0][1] - eigenvalue * s_matrix[0][1],
        ],
        [
            h_matrix[1][0] - eigenvalue * s_matrix[1][0],
            h_matrix[1][1] - eigenvalue * s_matrix[1][1],
        ],
    ]
    if abs(shifted[0][0]) + abs(shifted[0][1]) >= abs(shifted[1][0]) + abs(shifted[1][1]):
        vector = [-shifted[0][1], shifted[0][0]]
    else:
        vector = [-shifted[1][1], shifted[1][0]]
    norm = math.sqrt(vector[0] * vector[0] + vector[1] * vector[1])
    if norm == 0.0:
        vector = [1.0, 0.0]
    else:
        vector = [vector[0] / norm, vector[1] / norm]
    residual = [
        shifted[0][0] * vector[0] + shifted[0][1] * vector[1],
        shifted[1][0] * vector[0] + shifted[1][1] * vector[1],
    ]
    return math.sqrt(residual[0] * residual[0] + residual[1] * residual[1])


def _reference_matrix(lines: list[str], section: str, size: int) -> list[list[float]]:
    try:
        start = lines.index(section) + 1
    except ValueError as exc:
        raise ValueError(f"missing_{section}") from exc
    matrix = [[float(value) for value in line.split()] for line in lines[start : start + size]]
    if len(matrix) != size or any(len(row) != size for row in matrix):
        raise ValueError(f"{section}_shape_mismatch")
    return matrix


def _reference_float(lines: list[str], key: str) -> float:
    prefix = f"{key} "
    for line in lines:
        if line.startswith(prefix):
            return float(line.split()[1])
    raise ValueError(f"missing_{key}")


def _reference_float_list(lines: list[str], key: str) -> list[float]:
    prefix = f"{key} "
    for line in lines:
        if line.startswith(prefix):
            return sorted(float(value) for value in line.split()[1:])
    raise ValueError(f"missing_{key}")


def _ensure_symmetric_matrix(matrix: list[list[float]], section: str) -> None:
    for row_index, row in enumerate(matrix):
        for column_index, value in enumerate(row):
            if abs(value - matrix[column_index][row_index]) > 1e-12:
                raise ValueError(f"{section}_not_symmetric")


def _parse_text_matrix_row_starts(lines: list[str]) -> list[float]:
    values: list[float] = []
    capture_next_numeric = False
    for line in lines:
        if line.startswith("Row "):
            capture_next_numeric = True
            continue
        if capture_next_numeric:
            numbers = _float_tokens(line)
            if numbers:
                values.append(numbers[0])
                capture_next_numeric = False
    return values


def _parse_sparse_matrix_block_values(lines: list[str]) -> list[float]:
    values: list[float] = []
    for line in lines:
        numbers = _float_tokens(line)
        if len(numbers) >= 4 and all(float(int(number)) == number for number in numbers[:4]):
            continue
        values.extend(numbers[:8])
        if len(values) >= 8:
            break
    return values


def _float_tokens(line: str) -> list[float]:
    values: list[float] = []
    for token in re.findall(r"[-+]?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?", line):
        try:
            values.append(float(token))
        except ValueError:
            continue
    return values


def _integer_tokens(line: str) -> list[int]:
    values: list[int] = []
    for token in line.replace(",", " ").replace(":", " ").split():
        try:
            values.append(int(token))
        except ValueError:
            continue
    return values


def _matrix_validation_blockers(metadata: AbacusHSMatrixMetadata) -> list[str]:
    blockers = ["scientific_reference_missing"]
    if metadata.shape is None:
        blockers.append("matrix_shape_unparsed")
    if metadata.nnz is None:
        blockers.append("matrix_nnz_unparsed")
    if metadata.matrix_role == "unknown":
        blockers.append("matrix_role_unknown")
    return blockers


def _toy_header_int(lines: list[str], key: str) -> int:
    prefix = f"{key} "
    for line in lines:
        if line.startswith(prefix):
            return int(line.split()[1])
    raise ValueError(f"missing {key} in ABACUS_HS_TOY fixture")


def _toy_matrix(lines: list[str], norb: int) -> list[list[float]]:
    try:
        start = lines.index("h_matrix") + 1
    except ValueError as exc:
        raise ValueError("missing h_matrix in ABACUS_HS_TOY fixture") from exc
    matrix_lines = lines[start : start + norb]
    if len(matrix_lines) != norb:
        raise ValueError("h_matrix row count does not match norb")
    matrix = [[float(value) for value in line.split()] for line in matrix_lines]
    if any(len(row) != norb for row in matrix):
        raise ValueError("h_matrix column count does not match norb")
    for row_index, row in enumerate(matrix):
        for column_index, value in enumerate(row):
            if value != matrix[column_index][row_index]:
                raise ValueError("h_matrix must be symmetric for toy FCIDUMP conversion")
    return matrix


def _matrix_format_family(path: Path) -> str:
    name = path.name.lower()
    if name.endswith(".csr") or ".csr." in name:
        return "abacus_sparse_csr"
    if name.endswith(".txt") or ".txt." in name:
        return "abacus_text_matrix"
    return "unknown"


def _matrix_role(path: Path) -> str:
    name = path.name.lower()
    if name.startswith(("h", "data-h")) or "-hr-" in name:
        return "H"
    if name.startswith(("s", "data-s")) or "-sr-" in name:
        return "S"
    return "unknown"


def _source_refs(source_reference: str | dict[str, Any]) -> list[str]:
    if isinstance(source_reference, dict):
        raw_refs = source_reference.get("abacus_hs_source_refs", [])
        return [str(ref) for ref in raw_refs]
    return [source_reference]


def _parse_input_parameters(text: str) -> dict[str, list[str]]:
    parameters: dict[str, list[str]] = {}
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or line == "INPUT_PARAMETERS":
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        parameters[parts[0]] = parts[1:]
    return parameters
