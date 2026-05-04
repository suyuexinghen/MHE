"""Execution-mode and instantiation boundary records."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ExecutionMode(str, Enum):
    """Conservative core execution-mode vocabulary."""

    SIMULATION = "simulation"
    DRY_RUN = "dry_run"
    STAGED = "staged"
    INSTANTIATED = "instantiated"
    EXTERNAL_VERIFIED = "external_verified"
    UNKNOWN = "unknown"

    @classmethod
    def normalize(
        cls,
        value: "ExecutionMode | str | None",
        *,
        extension_family: str | None = None,
    ) -> "ExecutionMode":
        if isinstance(value, cls):
            return value
        if value is None:
            return cls.UNKNOWN
        normalized = str(value).strip().lower().replace("-", "_").replace(" ", "_")
        family = extension_family.lower() if extension_family else None
        direct = {mode.value: mode for mode in cls}
        direct.update(
            {
                "simulate": cls.SIMULATION,
                "simulator": cls.SIMULATION,
                "dryrun": cls.DRY_RUN,
                "validate_only": cls.DRY_RUN,
                "validation_only": cls.DRY_RUN,
                "schema": cls.DRY_RUN,
                "run": cls.INSTANTIATED,
                "real_run": cls.INSTANTIATED,
                "external": cls.EXTERNAL_VERIFIED,
                "verified": cls.EXTERNAL_VERIFIED,
                "hybrid": cls.STAGED,
            }
        )
        if family == "deepmd" and normalized.startswith("dpgen_"):
            return cls.STAGED
        return direct.get(normalized, cls.UNKNOWN)


class InstantiationRecord(BaseModel):
    """Core boundary record linking execution claims, actions, and evidence."""

    record_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    execution_mode: ExecutionMode = ExecutionMode.UNKNOWN
    native_execution_mode: str | None = None
    claim_ref: str | None = None
    action_ref: str | None = None
    run_artifact_ref: str | None = None
    validation_ref: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    external_evidence_refs: list[str] = Field(default_factory=list)
    reconciliation_status: str = "recorded_partial"
    candidate_id: str | None = None
    graph_version: int | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
