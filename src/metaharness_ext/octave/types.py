from __future__ import annotations

from enum import Enum
from typing import Literal

OctaveExperimentFamily = Literal["script_run", "function_eval", "numeric_benchmark"]
OctaveScriptMode = Literal["inline", "file", "function"]
OctaveInputKind = Literal["script", "mat", "csv", "json", "text", "data"]
OctaveOutputKind = Literal["variable", "mat", "json", "csv", "figure", "text", "log"]
OctaveRunArtifactStatus = Literal["completed", "failed", "timeout", "unavailable"]
OctaveWarningSeverity = Literal["benign", "suspicious", "blocking"]
OctaveGovernanceState = Literal["ready", "defer", "blocked"]
OctaveStudyStrategy = Literal["grid", "sequential", "bayesian"]


class OctaveValidationStatus(str, Enum):
    ENVIRONMENT_INVALID = "environment_invalid"
    COMPILE_FAILED = "compile_failed"
    RUNTIME_FAILED = "runtime_failed"
    OUTPUT_MISSING = "output_missing"
    OUTPUT_PARSE_FAILED = "output_parse_failed"
    NUMERIC_VALIDATION_FAILED = "numeric_validation_failed"
    EXECUTED = "executed"
