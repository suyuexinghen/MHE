from __future__ import annotations

DEEPMD_GATEWAY_SLOT = "deepmd_gateway.primary"
DEEPMD_ENVIRONMENT_SLOT = "deepmd_environment.primary"
DEEPMD_CONFIG_COMPILER_SLOT = "deepmd_config_compiler.primary"
DEEPMD_EXECUTOR_SLOT = "deepmd_executor.primary"
DEEPMD_VALIDATOR_SLOT = "deepmd_validator.primary"

PROTECTED_SLOTS = frozenset({DEEPMD_VALIDATOR_SLOT})
