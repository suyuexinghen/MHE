from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


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
    source_refs: list[str]
    if isinstance(source_reference, dict):
        raw_refs = source_reference.get("abacus_hs_source_refs", [])
        source_refs = [str(ref) for ref in raw_refs]
    else:
        source_refs = [source_reference]
    return AbacusHSBridgeStatus(
        case_id=case_id,
        source_refs=source_refs,
        reason=reason or AbacusHSBridgeStatus.model_fields["reason"].default,
    )
