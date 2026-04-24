from __future__ import annotations

from enum import Enum


class ProblemType(str, Enum):
    FORWARD = "forward"
    INVERSE = "inverse"
    DESIGN = "design"
    SURROGATE = "surrogate"


class SolverFamily(str, Enum):
    PINN_STRONG = "pinn_strong"
    DEM_ENERGY = "dem_energy"
    OPERATOR_LEARNING = "operator_learning"
    PINO = "pino"
    CLASSICAL_HYBRID = "classical_hybrid"


class RiskLevel(str, Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


class NextAction(str, Enum):
    ACCEPT = "accept"
    RETRY = "retry"
    ESCALATE = "escalate"
    REPLAN = "replan"


class PromotionOutcome(str, Enum):
    PENDING = "pending"
    PROMOTED = "promoted"
    REJECTED = "rejected"
    ROLLED_BACK = "rolled_back"


class SafetyOutcome(str, Enum):
    UNKNOWN = "unknown"
    ALLOWED = "allowed"
    REJECTED = "rejected"
    ROLLBACK_RECOMMENDED = "rollback_recommended"


class TemplateStatus(str, Enum):
    DRAFT = "draft"
    CANDIDATE = "candidate"
    STABLE = "stable"
    RETIRED = "retired"
