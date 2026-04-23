from __future__ import annotations

from typing import Literal

JediApplicationFamily = Literal["variational", "local_ensemble_da", "hofx", "forecast"]
JediExecutionMode = Literal["schema", "validate_only", "real_run"]
JediLauncher = Literal["direct", "mpiexec", "mpirun", "srun", "jsrun"]
JediCostType = Literal["3D-Var", "4D-Var", "4DEnsVar", "4D-Weak"]
JediRunStatus = Literal["planned", "completed", "failed", "unavailable"]
JediValidationStatus = Literal[
    "environment_invalid",
    "validated",
    "executed",
    "validation_failed",
    "runtime_failed",
]
