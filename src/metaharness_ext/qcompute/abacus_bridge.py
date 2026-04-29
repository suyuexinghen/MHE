from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

HS_OUTPUT_KEYS = {"out_mat_hs", "out_mat_hs2", "out_mat_hsR", "out_mat_t", "out_mat_r"}
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


class AbacusHSConversionResult(BaseModel):
    status: Literal["unsupported", "converted"]
    target_format: Literal["fcidump", "qcompute_pauli_dict"] = "fcidump"
    fcidump_text: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    unsupported_reason: str | None = None


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
    unsupported_reason: str = "ABACUS H/S matrix converter is not implemented."


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
    conversion_plan: AbacusHSConversionPlan = Field(default_factory=AbacusHSConversionPlan)
    promotion_ready: bool = False
    missing_capabilities: list[str] = Field(
        default_factory=lambda: ["abacus_hs_parser", "abacus_hs_to_fcidump_converter"]
    )
    reason: str = "ABACUS H/S-to-FCIDUMP or qubit-Hamiltonian bridge is not implemented."


def build_abacus_hs_bridge_status(
    *,
    case_id: str,
    source_reference: str | dict[str, Any],
    reason: str | None = None,
) -> AbacusHSBridgeStatus:
    source_refs = _source_refs(source_reference)
    parsed_metadata = parse_abacus_input_refs(source_refs)
    metadata_available = any(
        ref.get("exists") and ref.get("hs_output_keys") for ref in parsed_metadata
    )
    return AbacusHSBridgeStatus(
        case_id=case_id,
        status="converter_missing" if metadata_available else "fixture_missing",
        source_refs=source_refs,
        parsed_metadata={"input_refs": parsed_metadata},
        conversion_plan=build_abacus_hs_conversion_plan(metadata_available=metadata_available),
        missing_capabilities=["abacus_hs_to_fcidump_converter"],
        reason=reason or AbacusHSBridgeStatus.model_fields["reason"].default,
    )


def build_abacus_hs_conversion_plan(*, metadata_available: bool) -> AbacusHSConversionPlan:
    return AbacusHSConversionPlan(status="metadata_only" if metadata_available else "unsupported")


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
