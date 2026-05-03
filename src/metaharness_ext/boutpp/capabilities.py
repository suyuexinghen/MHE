from __future__ import annotations

BOUTPP_ENVIRONMENT_PROBE = "boutpp.environment.probe"
BOUTPP_OPTIONS_COMPILE = "boutpp.options.compile"
BOUTPP_MPI_EXECUTE = "boutpp.mpi.execute"
BOUTPP_RESTART_EXECUTE = "boutpp.restart.execute"
BOUTPP_OUTPUT_POSTPROCESS = "boutpp.output.postprocess"
BOUTPP_VALIDATION_BASIC = "boutpp.validation.basic"
BOUTPP_EVIDENCE_BUNDLE = "boutpp.evidence.bundle"
BOUTPP_POLICY_EVALUATE = "boutpp.policy.evaluate"
BOUTPP_STUDY_SWEEP = "boutpp.study.sweep"

ALL_CAPABILITIES = frozenset(
    {
        BOUTPP_ENVIRONMENT_PROBE,
        BOUTPP_OPTIONS_COMPILE,
        BOUTPP_MPI_EXECUTE,
        BOUTPP_RESTART_EXECUTE,
        BOUTPP_OUTPUT_POSTPROCESS,
        BOUTPP_VALIDATION_BASIC,
        BOUTPP_EVIDENCE_BUNDLE,
        BOUTPP_POLICY_EVALUATE,
        BOUTPP_STUDY_SWEEP,
    }
)
