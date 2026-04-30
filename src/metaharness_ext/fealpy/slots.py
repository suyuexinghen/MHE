from __future__ import annotations

FEALPY_GATEWAY_SLOT = "fealpy_gateway.primary"
FEALPY_ENVIRONMENT_SLOT = "fealpy_environment.primary"
FEALPY_COMPILER_SLOT = "fealpy_compiler.primary"
FEALPY_EXECUTOR_SLOT = "fealpy_executor.primary"
FEALPY_VALIDATOR_SLOT = "fealpy_validator.primary"
FEALPY_STUDY_SLOT = "fealpy_study.primary"
FEALPY_QUOTA_PROVIDER_SLOT = "fealpy_quota_provider.primary"

PROTECTED_SLOTS = frozenset({FEALPY_VALIDATOR_SLOT})
