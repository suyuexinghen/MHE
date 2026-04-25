from __future__ import annotations

from enum import Enum
from typing import Literal

QComputeExecutionMode = Literal["simulate", "run", "hybrid"]


class QComputeValidationStatus(str, Enum):
    ENVIRONMENT_INVALID = "environment_invalid"
    BACKEND_UNAVAILABLE = "backend_unavailable"
    EXECUTION_FAILED = "execution_failed"
    RESULT_INCOMPLETE = "result_incomplete"
    BELOW_FIDELITY_THRESHOLD = "below_fidelity"
    NOISE_CORRUPTED = "noise_corrupted"
    VALIDATED = "validated"
    CONVERGED = "converged"
