from __future__ import annotations

BOUTPP_GATEWAY_SLOT = "boutpp_gateway.primary"
BOUTPP_ENVIRONMENT_SLOT = "boutpp_environment.primary"
BOUTPP_COMPILER_SLOT = "boutpp_compiler.primary"
BOUTPP_EXECUTOR_SLOT = "boutpp_executor.primary"
BOUTPP_POSTPROCESS_SLOT = "boutpp_postprocess.primary"
BOUTPP_VALIDATOR_SLOT = "boutpp_validator.primary"
BOUTPP_EVIDENCE_POLICY_SLOT = "boutpp_evidence_policy.primary"
BOUTPP_STUDY_SLOT = "boutpp_study.primary"

PROTECTED_SLOTS = frozenset({BOUTPP_VALIDATOR_SLOT, BOUTPP_EVIDENCE_POLICY_SLOT})
