from __future__ import annotations

CAP_MOOSE_TASK_ISSUE = "moose.task.issue"
CAP_MOOSE_ENV_PROBE = "moose.environment.probe"
CAP_MOOSE_INPUT_COMPILE = "moose.input.compile"
CAP_MOOSE_EXECUTE_RUN = "moose.execute.run"
CAP_MOOSE_VALIDATE_REPORT = "moose.validate.report"
CAP_MOOSE_EVIDENCE_BUNDLE = "moose.evidence.bundle"
CAP_MOOSE_POLICY_EVALUATE = "moose.policy.evaluate"
CAP_MOOSE_STUDY_RUN = "moose.study.run"

CANONICAL_CAPABILITIES = frozenset(
    {
        CAP_MOOSE_TASK_ISSUE,
        CAP_MOOSE_ENV_PROBE,
        CAP_MOOSE_INPUT_COMPILE,
        CAP_MOOSE_EXECUTE_RUN,
        CAP_MOOSE_VALIDATE_REPORT,
        CAP_MOOSE_EVIDENCE_BUNDLE,
        CAP_MOOSE_POLICY_EVALUATE,
        CAP_MOOSE_STUDY_RUN,
    }
)
