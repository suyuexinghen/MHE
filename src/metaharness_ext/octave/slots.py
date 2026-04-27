from __future__ import annotations

OCTAVE_GATEWAY_SLOT = "octave_gateway.primary"
OCTAVE_ENVIRONMENT_SLOT = "octave_environment.primary"
OCTAVE_SCRIPT_COMPILER_SLOT = "octave_script_compiler.primary"
OCTAVE_EXECUTOR_SLOT = "octave_executor.primary"
OCTAVE_VALIDATOR_SLOT = "octave_validator.primary"
OCTAVE_STUDY_SLOT = "octave_study.primary"

PROTECTED_SLOTS = frozenset({OCTAVE_VALIDATOR_SLOT})
