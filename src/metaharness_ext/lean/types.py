from __future__ import annotations

from enum import Enum
from typing import Literal

LeanExecutionMode = Literal["dry_run", "real_lean"]


class LeanValidationStatus(str, Enum):
    FULLY_PROVEN = "fully_proven"
    PARTIALLY_PROVEN = "partially_proven"
    BUDGET_EXHAUSTED = "budget_exhausted"
    COMPILATION_FAILED = "compilation_failed"
    STATEMENT_DRIFT = "statement_drift"
    ENVIRONMENT_FAILED = "environment_failed"
    TIMEOUT = "timeout"
    WORKSPACE_ERROR = "workspace_error"


class LeanFamily(str, Enum):
    FORMAL_PROOF = "formal_proof"
    PROOF_AUDIT = "proof_audit"
    FORMALIZATION_PROJECT = "formalization_project"


class LeanBlueprintItemStatus(str, Enum):
    TODO = "todo"
    PARTIAL = "partial"
    DONE = "done"
    BLOCKED = "blocked"


class LeanDiagnosticSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
