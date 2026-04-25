from __future__ import annotations

QCOMPUTE_GATEWAY_SLOT = "qcompute_gateway.primary"
QCOMPUTE_ENVIRONMENT_SLOT = "qcompute_environment.primary"
QCOMPUTE_CONFIG_COMPILER_SLOT = "qcompute_config_compiler.primary"
QCOMPUTE_EXECUTOR_SLOT = "qcompute_executor.primary"
QCOMPUTE_VALIDATOR_SLOT = "qcompute_validator.primary"
QCOMPUTE_STUDY_SLOT = "qcompute_study.primary"

PROTECTED_SLOTS = frozenset({QCOMPUTE_VALIDATOR_SLOT})
