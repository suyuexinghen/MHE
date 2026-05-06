from __future__ import annotations

from metaharness_ext.lean.backends import MockLeanBackend, MockLeanResult
from metaharness_ext.lean.benchmark_cases import get_lean_proof_cases, lean_proof_case_catalog
from metaharness_ext.lean.benchmark_runner import LeanProofBenchmarkRunner
from metaharness_ext.lean.blueprint_compiler import LeanBlueprintCompilerComponent
from metaharness_ext.lean.capabilities import (
    CANONICAL_CAPABILITIES,
    CAP_LEAN_BUILD_EVIDENCE,
    CAP_LEAN_COMPILE_BLUEPRINT,
    CAP_LEAN_EVALUATE_POLICY,
    CAP_LEAN_EXECUTE_PROOF,
    CAP_LEAN_ORCHESTRATE_WORKFLOW,
    CAP_LEAN_PREPARE_WORKSPACE,
    CAP_LEAN_PROBE_ENVIRONMENT,
    CAP_LEAN_VALIDATE_RESULT,
)
from metaharness_ext.lean.contracts import (
    LeanBlueprint,
    LeanBlueprintItem,
    LeanCandidateIdentity,
    LeanDiagnostic,
    LeanEnvironmentReport,
    LeanEvidenceBundle,
    LeanExecutionPolicy,
    LeanProjectSpec,
    LeanPromotionMetadata,
    LeanProvenance,
    LeanRunArtifact,
    LeanRunPlan,
    LeanTaskSpec,
    LeanValidationReport,
)
from metaharness_ext.lean.environment import LeanEnvironmentComponent
from metaharness_ext.lean.evidence import LeanEvidenceComponent
from metaharness_ext.lean.executor import LeanExecutorComponent
from metaharness_ext.lean.gateway import LeanGatewayComponent
from metaharness_ext.lean.proof_workspace import LeanProofWorkspaceComponent
from metaharness_ext.lean.slots import (
    LEAN_BLUEPRINT_COMPILER_SLOT,
    LEAN_ENVIRONMENT_SLOT,
    LEAN_EVIDENCE_SLOT,
    LEAN_EXECUTOR_SLOT,
    LEAN_GATEWAY_SLOT,
    LEAN_PROOF_WORKSPACE_SLOT,
    LEAN_VALIDATOR_SLOT,
    PROTECTED_SLOTS,
)
from metaharness_ext.lean.types import (
    LeanBlueprintItemStatus,
    LeanDiagnosticSeverity,
    LeanExecutionMode,
    LeanFamily,
    LeanValidationStatus,
)
from metaharness_ext.lean.validator import LeanValidatorComponent

__all__ = [
    "CANONICAL_CAPABILITIES",
    "CAP_LEAN_BUILD_EVIDENCE",
    "CAP_LEAN_COMPILE_BLUEPRINT",
    "CAP_LEAN_EVALUATE_POLICY",
    "CAP_LEAN_EXECUTE_PROOF",
    "CAP_LEAN_ORCHESTRATE_WORKFLOW",
    "CAP_LEAN_PREPARE_WORKSPACE",
    "CAP_LEAN_PROBE_ENVIRONMENT",
    "CAP_LEAN_VALIDATE_RESULT",
    "LEAN_BLUEPRINT_COMPILER_SLOT",
    "LEAN_ENVIRONMENT_SLOT",
    "LEAN_EVIDENCE_SLOT",
    "LEAN_EXECUTOR_SLOT",
    "LEAN_GATEWAY_SLOT",
    "LEAN_PROOF_WORKSPACE_SLOT",
    "LEAN_VALIDATOR_SLOT",
    "PROTECTED_SLOTS",
    "LeanBlueprint",
    "LeanBlueprintCompilerComponent",
    "LeanBlueprintItem",
    "LeanBlueprintItemStatus",
    "LeanCandidateIdentity",
    "LeanDiagnostic",
    "LeanDiagnosticSeverity",
    "LeanEnvironmentComponent",
    "LeanEnvironmentReport",
    "LeanEvidenceBundle",
    "LeanEvidenceComponent",
    "LeanExecutionMode",
    "LeanExecutionPolicy",
    "LeanExecutorComponent",
    "LeanFamily",
    "LeanGatewayComponent",
    "LeanProofBenchmarkRunner",
    "LeanProjectSpec",
    "LeanPromotionMetadata",
    "LeanProofWorkspaceComponent",
    "LeanProvenance",
    "LeanRunArtifact",
    "LeanRunPlan",
    "LeanTaskSpec",
    "LeanValidationReport",
    "LeanValidationStatus",
    "LeanValidatorComponent",
    "MockLeanBackend",
    "MockLeanResult",
    "get_lean_proof_cases",
    "lean_proof_case_catalog",
]
