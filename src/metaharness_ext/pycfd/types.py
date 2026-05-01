from __future__ import annotations

from enum import Enum
from typing import Literal

PyCFDCaseType = Literal[
    "vortex",
    "airfoil",
    "cylinder",
    "mms",
    "shock_diffraction",
]

PyCFDMeshType = Literal["tri", "quad"]

PyCFDFluxType = Literal["roe"]

PyCFDLimiterType = Literal["none", "venkatakrishnan", "van_albada"]

PyCFDRunArtifactStatus = Literal["completed", "failed", "timeout", "unavailable"]

PyCFDSolverType = Literal[
    "explicit_unsteady_solver",
    "explicit_steady_solver",
    "mms_solver",
    "explicit_unsteady_solver_efficient_shockdiffraction",
]

PyCFDFlowType = Literal["vortex", "freestream", "shock-diffraction", "mms"]


class PyCFDValidationStatus(str, Enum):
    ENVIRONMENT_UNAVAILABLE = "environment_unavailable"
    COMPILE_FAILED = "compile_failed"
    RUNTIME_FAILED = "runtime_failed"
    RESIDUAL_EXCEEDED = "residual_exceeded"
    EXECUTED = "executed"
