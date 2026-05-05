from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from metaharness.core.models import ScoredEvidence
from metaharness_ext.lean.types import (
    LeanBlueprintItemStatus,
    LeanDiagnosticSeverity,
    LeanExecutionMode,
    LeanFamily,
    LeanValidationStatus,
)


class LeanCandidateIdentity(BaseModel):
    candidate_id: str = "lean-candidate"
    family: LeanFamily = LeanFamily.FORMAL_PROOF
    graph_version: int | None = None


class LeanPromotionMetadata(BaseModel):
    promotion_ready: bool = False
    blocks_promotion: bool = True
    failure_code: str | None = None


class LeanExecutionPolicy(BaseModel):
    mode: LeanExecutionMode = "dry_run"
    timeout_seconds: int = 60
    max_attempts: int = 1
    allow_parallel: bool = False


class LeanProjectSpec(BaseModel):
    project_root: str
    toolchain_version: str | None = None
    lakefile_path: str | None = None
    build_status: str = "unknown"


class LeanTaskSpec(BaseModel):
    family: LeanFamily = LeanFamily.FORMAL_PROOF
    target_file: str
    target_lemma: str | None = None
    project: LeanProjectSpec | None = None
    budget: int = 1
    execution_policy: LeanExecutionPolicy = Field(default_factory=LeanExecutionPolicy)
    metadata: dict[str, Any] = Field(default_factory=dict)


class LeanDiagnostic(BaseModel):
    file: str | None = None
    line: int | None = None
    column: int | None = None
    severity: LeanDiagnosticSeverity = LeanDiagnosticSeverity.INFO
    message: str
    code: str | None = None


class LeanBlueprintItem(BaseModel):
    label: str
    lean_declaration: str
    file: str
    uses: list[str] = Field(default_factory=list)
    status: LeanBlueprintItemStatus = LeanBlueprintItemStatus.TODO
    attempts: int = 0
    budget: int = 1
    informal_statement: str = ""
    informal_proof: str = ""


class LeanBlueprint(BaseModel):
    items: list[LeanBlueprintItem] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class LeanRunPlan(BaseModel):
    plan_id: str
    task_ref: str
    target_file: str
    workspace_path: str | None = None
    execution_params: dict[str, Any] = Field(default_factory=dict)


class LeanRunArtifact(BaseModel):
    artifact_id: str
    plan_ref: str
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    diagnostics: list[LeanDiagnostic] = Field(default_factory=list)
    sorry_locations: list[LeanDiagnostic] = Field(default_factory=list)
    duration_seconds: float = 0.0
    backend: str = "mock"
    execution_mode: LeanExecutionMode = "dry_run"


class LeanEnvironmentReport(BaseModel):
    lean_available: bool = False
    lake_available: bool = False
    project_root_found: bool = False
    build_status: str = "unknown"
    toolchain_version: str | None = None
    lakefile_path: str | None = None
    optional_tools: dict[str, bool] = Field(default_factory=dict)
    blocks_promotion: bool = True


class LeanValidationReport(BaseModel):
    status: LeanValidationStatus = LeanValidationStatus.ENVIRONMENT_FAILED
    sorry_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    audit_files: list[str] = Field(default_factory=list)
    drift_detected: bool = False
    drift_changes: list[dict[str, Any]] = Field(default_factory=list)
    completeness_ratio: float = 0.0
    blocks_promotion: bool = True
    retriable: bool = False
    scored_evidence: ScoredEvidence | None = None
    candidate_identity: LeanCandidateIdentity = Field(default_factory=LeanCandidateIdentity)
    promotion_metadata: LeanPromotionMetadata = Field(default_factory=LeanPromotionMetadata)
    checkpoint_refs: list[str] = Field(default_factory=list)
    provenance_refs: list[str] = Field(default_factory=list)
    trace_refs: list[str] = Field(default_factory=list)
    execution_policy: LeanExecutionPolicy = Field(default_factory=LeanExecutionPolicy)


class LeanProvenance(BaseModel):
    execution_mode: LeanExecutionMode = "dry_run"
    backend: str = "mock"
    command: list[str] = Field(default_factory=list)
    cwd: str | None = None
    lean_toolchain: str | None = None
    lakefile_path: str | None = None
    agent_model: str | None = None
    blueprint_version: str | None = None
    informal_proof_version: str | None = None
    attempts: list[dict[str, Any]] = Field(default_factory=list)


class LeanEvidenceBundle(BaseModel):
    bundle_id: str
    task_ref: str
    environment_report: LeanEnvironmentReport
    blueprint: LeanBlueprint | None = None
    artifacts: list[LeanRunArtifact] = Field(default_factory=list)
    validation_report: LeanValidationReport
    provenance: LeanProvenance = Field(default_factory=LeanProvenance)
    graph_metadata: dict[str, Any] = Field(default_factory=dict)
    candidate_identity: LeanCandidateIdentity = Field(default_factory=LeanCandidateIdentity)
    checkpoint_refs: list[str] = Field(default_factory=list)
    provenance_refs: list[str] = Field(default_factory=list)
    trace_refs: list[str] = Field(default_factory=list)
