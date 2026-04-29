"""MHE extension for fealpy — Python Finite Element Library."""

from metaharness_ext.fealpy.async_executor import FealpyAsyncExecutor
from metaharness_ext.fealpy.benchmark_runner import FealpyBenchmarkRunner
from metaharness_ext.fealpy.capabilities import (
    CANONICAL_CAPABILITIES,
    CAP_FEALPY_COMPILE,
    CAP_FEALPY_ENV_PROBE,
    CAP_FEALPY_EXECUTE_RUN,
    CAP_FEALPY_OPTIMIZER_PROPOSE,
    CAP_FEALPY_SCHEDULER_DRYRUN,
    CAP_FEALPY_STUDY_RUN,
    CAP_FEALPY_TASK_ISSUE,
    CAP_FEALPY_VALIDATE_REPORT,
)
from metaharness_ext.fealpy.compiler import FealpyCompilerComponent
from metaharness_ext.fealpy.contracts import (
    FealpyEnvironmentReport,
    FealpyEvidenceBundle,
    FealpyEvidenceWarning,
    FealpyMeshSpec,
    FealpyPolicyReport,
    FealpyProblemSpec,
    FealpyRunArtifact,
    FealpyRunPlan,
    FealpySolverSpec,
    FealpyStudyAxis,
    FealpyStudyReport,
    FealpyStudySpec,
    FealpyStudyTrial,
    FealpyValidationReport,
)
from metaharness_ext.fealpy.environment import FealpyEnvironmentProbeComponent
from metaharness_ext.fealpy.evidence import build_evidence_bundle
from metaharness_ext.fealpy.executor import FealpyExecutorComponent
from metaharness_ext.fealpy.gateway import FealpyGatewayComponent
from metaharness_ext.fealpy.governance import FealpyGovernanceAdapter
from metaharness_ext.fealpy.optimizer import (
    FealpyDomainBrainProvider,
    FealpyOptimizerStrategy,
    FealpyProposalEvaluation,
    FealpyStudyObservation,
)
from metaharness_ext.fealpy.policy import FealpyEvidencePolicy
from metaharness_ext.fealpy.scheduler import (
    FealpySchedulerAdapter,
    FealpySlurmBackend,
    FealpySlurmSubmission,
)
from metaharness_ext.fealpy.slots import (
    FEALPY_COMPILER_SLOT,
    FEALPY_ENVIRONMENT_SLOT,
    FEALPY_EXECUTOR_SLOT,
    FEALPY_GATEWAY_SLOT,
    FEALPY_STUDY_SLOT,
    FEALPY_VALIDATOR_SLOT,
    PROTECTED_SLOTS,
)
from metaharness_ext.fealpy.study import FealpyStudyComponent
from metaharness_ext.fealpy.types import (
    FealpyBackend,
    FealpyFeSpaceType,
    FealpyMeshType,
    FealpyPdeFamily,
    FealpyRunArtifactStatus,
    FealpySolverMethod,
    FealpyValidationStatus,
)
from metaharness_ext.fealpy.validator import FealpyValidatorComponent

__all__ = [
    "CANONICAL_CAPABILITIES",
    "CAP_FEALPY_COMPILE",
    "CAP_FEALPY_ENV_PROBE",
    "CAP_FEALPY_EXECUTE_RUN",
    "CAP_FEALPY_OPTIMIZER_PROPOSE",
    "CAP_FEALPY_SCHEDULER_DRYRUN",
    "CAP_FEALPY_STUDY_RUN",
    "CAP_FEALPY_TASK_ISSUE",
    "CAP_FEALPY_VALIDATE_REPORT",
    "FEALPY_COMPILER_SLOT",
    "FEALPY_ENVIRONMENT_SLOT",
    "FEALPY_EXECUTOR_SLOT",
    "FEALPY_GATEWAY_SLOT",
    "FEALPY_STUDY_SLOT",
    "FEALPY_VALIDATOR_SLOT",
    "FealpyAsyncExecutor",
    "FealpyBackend",
    "FealpyBenchmarkRunner",
    "FealpyCompilerComponent",
    "FealpyDomainBrainProvider",
    "FealpyEnvironmentProbeComponent",
    "FealpyEnvironmentReport",
    "FealpyEvidenceBundle",
    "FealpyEvidencePolicy",
    "FealpyEvidenceWarning",
    "FealpyExecutorComponent",
    "FealpyFeSpaceType",
    "FealpyGatewayComponent",
    "FealpyGovernanceAdapter",
    "FealpyMeshSpec",
    "FealpyMeshType",
    "FealpyOptimizerStrategy",
    "FealpyPdeFamily",
    "FealpyPolicyReport",
    "FealpyProblemSpec",
    "FealpyProposalEvaluation",
    "FealpyRunArtifact",
    "FealpyRunArtifactStatus",
    "FealpyRunPlan",
    "FealpySchedulerAdapter",
    "FealpySlurmBackend",
    "FealpySlurmSubmission",
    "FealpySolverMethod",
    "FealpySolverSpec",
    "FealpyStudyAxis",
    "FealpyStudyComponent",
    "FealpyStudyObservation",
    "FealpyStudyReport",
    "FealpyStudySpec",
    "FealpyStudyTrial",
    "FealpyValidationReport",
    "FealpyValidationStatus",
    "FealpyValidatorComponent",
    "PROTECTED_SLOTS",
    "build_evidence_bundle",
]
