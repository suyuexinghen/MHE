from __future__ import annotations

from enum import Enum


class NektarSolverFamily(str, Enum):
    ADR = "adr"
    INCNS = "incns"


class NektarAdrEqType(str, Enum):
    LAPLACE = "Laplace"
    POISSON = "Poisson"
    HELMHOLTZ = "Helmholtz"
    STEADY_ADVECTION_DIFFUSION = "SteadyAdvectionDiffusion"
    UNSTEADY_ADVECTION_DIFFUSION = "UnsteadyAdvectionDiffusion"
    UNSTEADY_REACTION_DIFFUSION = "UnsteadyReactionDiffusion"


class NektarIncnsEqType(str, Enum):
    STEADY_STOKES = "SteadyStokes"
    UNSTEADY_STOKES = "UnsteadyStokes"
    UNSTEADY_NAVIER_STOKES = "UnsteadyNavierStokes"


class NektarProjection(str, Enum):
    CONTINUOUS = "Continuous"
    DISCONTINUOUS = "DisContinuous"


class NektarIncnsSolverType(str, Enum):
    VELOCITY_CORRECTION = "VelocityCorrectionScheme"
    VCS_WEAK_PRESSURE = "VCSWeakPressure"
    COUPLED_LINEARISED_NS = "CoupledLinearisedNS"


class NektarBoundaryConditionType(str, Enum):
    DIRICHLET = "D"
    NEUMANN = "N"
    ROBIN = "R"
    PERIODIC = "P"


class NektarGeometryMode(str, Enum):
    DIM_2D = "2D"
    DIM_2D_HOMO1D = "2D-homogeneous-1D"
    DIM_3D = "3D"
