from __future__ import annotations

JEDI_GATEWAY_SLOT = "jedi_gateway.primary"
JEDI_ENVIRONMENT_SLOT = "jedi_environment.primary"
JEDI_CONFIG_COMPILER_SLOT = "jedi_config_compiler.primary"
JEDI_EXECUTOR_SLOT = "jedi_executor.primary"
JEDI_VALIDATOR_SLOT = "jedi_validator.primary"

PROTECTED_SLOTS = frozenset({JEDI_VALIDATOR_SLOT})
