from __future__ import annotations

from enum import Enum
from typing import Literal

BoutPPLauncherMode = Literal["direct", "mpi"]
BoutPPRestartMode = Literal["fresh", "restart", "restart_append"]
BoutPPRunStatus = Literal["planned", "completed", "failed", "timeout", "unavailable"]
BoutPPPostprocessStatus = Literal["completed", "partial", "failed", "unavailable"]
BoutPPPolicyDecision = Literal["allow", "defer", "reject"]
BoutPPStudyGoal = Literal["minimize", "maximize"]


class BoutPPValidationStatus(str, Enum):
    ENVIRONMENT_UNAVAILABLE = "environment_unavailable"
    RUNTIME_FAILED = "runtime_failed"
    ARTIFACT_MISSING = "artifact_missing"
    VARIABLE_MISSING = "variable_missing"
    METRIC_THRESHOLD_EXCEEDED = "metric_threshold_exceeded"
    EXECUTED = "executed"
