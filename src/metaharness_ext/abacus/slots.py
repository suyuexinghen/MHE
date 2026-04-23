from __future__ import annotations

ABACUS_GATEWAY_SLOT = "abacus_gateway.primary"
ABACUS_ENVIRONMENT_SLOT = "abacus_environment.primary"
ABACUS_INPUT_COMPILER_SLOT = "abacus_input_compiler.primary"
ABACUS_EXECUTOR_SLOT = "abacus_executor.primary"
ABACUS_VALIDATOR_SLOT = "abacus_validator.primary"

PROTECTED_SLOTS = frozenset({ABACUS_VALIDATOR_SLOT})
