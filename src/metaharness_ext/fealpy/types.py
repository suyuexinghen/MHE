from __future__ import annotations

from enum import Enum
from typing import Literal

FealpyPdeFamily = Literal[
    "poisson",
    "stokes",
    "navier_stokes",
    "parabolic",
    "hyperbolic",
    "helmholtz",
    "curlcurl",
    "diffusion",
    "diffusion_convection",
    "diffusion_convection_reaction",
    "diffusion_reaction",
    "darcy",
    "darcyforchheimer",
    "linear_elasticity",
    "interface_poisson",
    "surface_poisson",
    "wave",
    "allen_cahn",
    "nonlinear",
    "polyharmonic",
    "quasilinear_elliptic",
    "optimal_control",
    "ion_flow",
    "dld_microfluidic_chip",
    "mgtensor_possion",
]

FealpyBackend = Literal["numpy", "pytorch", "jax"]

FealpySolverMethod = Literal["direct", "cg", "gmres", "minres", "bicgstab", "amg"]

FealpyFeSpaceType = Literal["Lagrange", "CrConforming", "FirstNedelec", "RaviartThomas", "HuZhang"]

FealpyRunArtifactStatus = Literal["completed", "failed", "timeout", "unavailable"]
FealpyMeshType = Literal["interval", "tri", "quad", "tet", "hex", "uniform"]


class FealpyValidationStatus(str, Enum):
    ENVIRONMENT_INVALID = "environment_invalid"
    COMPILE_FAILED = "compile_failed"
    RUNTIME_FAILED = "runtime_failed"
    OUTPUT_MISSING = "output_missing"
    NUMERIC_VALIDATION_FAILED = "numeric_validation_failed"
    EXECUTED = "executed"
