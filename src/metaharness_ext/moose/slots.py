from __future__ import annotations

MOOSE_GATEWAY_SLOT = "moose_gateway.primary"
MOOSE_ENVIRONMENT_SLOT = "moose_environment.primary"
MOOSE_INPUT_COMPILER_SLOT = "moose_input_compiler.primary"
MOOSE_EXECUTOR_SLOT = "moose_executor.primary"
MOOSE_VALIDATOR_SLOT = "moose_validator.primary"
MOOSE_STUDY_SLOT = "moose_study.primary"
MOOSE_EVIDENCE_POLICY_SLOT = "moose_evidence_policy.primary"

PROTECTED_SLOTS = frozenset({MOOSE_VALIDATOR_SLOT, MOOSE_EVIDENCE_POLICY_SLOT})
