from __future__ import annotations

CAP_FEALPY_TASK_ISSUE = "fealpy.task.issue"
CAP_FEALPY_ENV_PROBE = "fealpy.environment.probe"
CAP_FEALPY_COMPILE = "fealpy.compile"
CAP_FEALPY_EXECUTE_RUN = "fealpy.execute.run"
CAP_FEALPY_VALIDATE_REPORT = "fealpy.validate.report"
CAP_FEALPY_STUDY_RUN = "fealpy.study.run"

CAP_FEALPY_OPTIMIZER_PROPOSE = "fealpy.optimizer.propose"
CAP_FEALPY_SCHEDULER_DRYRUN = "fealpy.scheduler.dryrun"

CANONICAL_CAPABILITIES = frozenset(
    {
        CAP_FEALPY_TASK_ISSUE,
        CAP_FEALPY_ENV_PROBE,
        CAP_FEALPY_COMPILE,
        CAP_FEALPY_EXECUTE_RUN,
        CAP_FEALPY_VALIDATE_REPORT,
        CAP_FEALPY_STUDY_RUN,
        CAP_FEALPY_OPTIMIZER_PROPOSE,
        CAP_FEALPY_SCHEDULER_DRYRUN,
    }
)
