from __future__ import annotations

JEDI_GATEWAY_SLOT = "jedi_gateway.primary"
JEDI_ENVIRONMENT_SLOT = "jedi_environment.primary"
JEDI_CONFIG_COMPILER_SLOT = "jedi_config_compiler.primary"
JEDI_EXECUTOR_SLOT = "jedi_executor.primary"
JEDI_VALIDATOR_SLOT = "jedi_validator.primary"
JEDI_SMOKE_POLICY_SLOT = "jedi_smoke_policy.primary"
JEDI_DIAGNOSTICS_SLOT = "jedi_diagnostics.primary"
JEDI_STUDY_SLOT = "jedi_study.primary"

PROTECTED_SLOTS = frozenset({JEDI_VALIDATOR_SLOT})
