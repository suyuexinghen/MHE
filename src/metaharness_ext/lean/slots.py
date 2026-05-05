from __future__ import annotations

LEAN_GATEWAY_SLOT = "lean_gateway.primary"
LEAN_ENVIRONMENT_SLOT = "lean_environment.primary"
LEAN_BLUEPRINT_COMPILER_SLOT = "lean_blueprint_compiler.primary"
LEAN_PROOF_WORKSPACE_SLOT = "lean_proof_workspace.primary"
LEAN_EXECUTOR_SLOT = "lean_executor.primary"
LEAN_VALIDATOR_SLOT = "lean_validator.primary"
LEAN_EVIDENCE_SLOT = "lean_evidence.primary"

PROTECTED_SLOTS = frozenset({LEAN_VALIDATOR_SLOT})
