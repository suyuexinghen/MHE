from __future__ import annotations

NEKTAR_GATEWAY_SLOT = "nektar_gateway.primary"
SESSION_COMPILER_SLOT = "session_compiler.primary"
SOLVER_EXECUTOR_SLOT = "solver_executor.primary"
POSTPROCESS_SLOT = "postprocess.primary"
VALIDATOR_SLOT = "validator.primary"
CONVERGENCE_STUDY_SLOT = "convergence_study.primary"

PROTECTED_SLOTS = frozenset({VALIDATOR_SLOT})
