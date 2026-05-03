from __future__ import annotations

from enum import Enum
from typing import Literal

MooseInputMode = Literal["inline", "file"]
MooseOutputKind = Literal["exodus", "csv", "text", "log", "other"]
MooseRunArtifactStatus = Literal["completed", "failed", "timeout", "unavailable"]


class MooseValidationStatus(str, Enum):
    ENVIRONMENT_INVALID = "environment_invalid"
    RUNTIME_FAILED = "runtime_failed"
    OUTPUT_MISSING = "output_missing"
    EXECUTED = "executed"
