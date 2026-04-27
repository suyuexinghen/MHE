from __future__ import annotations

CAP_OCTAVE_TASK_ISSUE = "octave.task.issue"
CAP_OCTAVE_ENV_PROBE = "octave.environment.probe"
CAP_OCTAVE_SCRIPT_COMPILE = "octave.script.compile"
CAP_OCTAVE_EXECUTE_RUN = "octave.execute.run"
CAP_OCTAVE_VALIDATE_REPORT = "octave.validate.report"
CAP_OCTAVE_EVIDENCE_BUNDLE = "octave.evidence.bundle"
CAP_OCTAVE_POLICY_EVALUATE = "octave.policy.evaluate"
CAP_OCTAVE_STUDY_RUN = "octave.study.run"
CAP_OCTAVE_GOVERNANCE_ADAPT = "octave.governance.adapt"
CAP_OCTAVE_ASYNC_EXECUTE = "octave.execute.async"
CAP_OCTAVE_SCHEDULER_DRYRUN = "octave.scheduler.dryrun"
CAP_OCTAVE_ARTIFACT_DISCOVER = "octave.artifact.discover"
CAP_OCTAVE_OPTIMIZER_PROPOSE = "octave.optimizer.propose"
CAP_OCTAVE_SECURITY_SCAN = "octave.security.scan"

CANONICAL_CAPABILITIES = frozenset(
    {
        CAP_OCTAVE_TASK_ISSUE,
        CAP_OCTAVE_ENV_PROBE,
        CAP_OCTAVE_SCRIPT_COMPILE,
        CAP_OCTAVE_EXECUTE_RUN,
        CAP_OCTAVE_VALIDATE_REPORT,
        CAP_OCTAVE_EVIDENCE_BUNDLE,
        CAP_OCTAVE_POLICY_EVALUATE,
        CAP_OCTAVE_STUDY_RUN,
        CAP_OCTAVE_GOVERNANCE_ADAPT,
        CAP_OCTAVE_ASYNC_EXECUTE,
        CAP_OCTAVE_SCHEDULER_DRYRUN,
        CAP_OCTAVE_ARTIFACT_DISCOVER,
        CAP_OCTAVE_OPTIMIZER_PROPOSE,
        CAP_OCTAVE_SECURITY_SCAN,
    }
)
