"""MHE extension for fealpy — Python Finite Element Library."""

from metaharness_ext.fealpy.async_executor import FealpyAsyncExecutor
from metaharness_ext.fealpy.backend_comparison import (
    BackendMetrics,
    FealpyBackendComparisonResult,
    FealpyBackendComparisonRunner,
)
from metaharness_ext.fealpy.benchmark_cases import fealpy_case_catalog, get_fealpy_cases
from metaharness_ext.fealpy.benchmark_runner import FealpyBenchmarkRunner
from metaharness_ext.fealpy.capabilities import (
    CANONICAL_CAPABILITIES,
    CAP_FEALPY_COMPILE,
    CAP_FEALPY_ENV_PROBE,
    CAP_FEALPY_EXECUTE_RUN,
    CAP_FEALPY_OPTIMIZER_PROPOSE,
    CAP_FEALPY_QUOTA_PROVIDE,
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
from metaharness_ext.fealpy.quota import (
    FealpyResourceQuotaProvider,
    estimate_dofs,
    estimate_memory_mb,
    estimate_taylor_hood_dofs,
)
from metaharness_ext.fealpy.scheduler import (
    FealpyK8sBackend,
    FealpyK8sJobSpec,
    FealpySchedulerAdapter,
    FealpySlurmBackend,
    FealpySlurmSubmission,
)
from metaharness_ext.fealpy.slots import (
    FEALPY_COMPILER_SLOT,
    FEALPY_ENVIRONMENT_SLOT,
    FEALPY_EXECUTOR_SLOT,
    FEALPY_GATEWAY_SLOT,
    FEALPY_QUOTA_PROVIDER_SLOT,
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
    "BackendMetrics",
    "CANONICAL_CAPABILITIES",
    "CAP_FEALPY_COMPILE",
    "CAP_FEALPY_ENV_PROBE",
    "CAP_FEALPY_EXECUTE_RUN",
    "CAP_FEALPY_OPTIMIZER_PROPOSE",
    "CAP_FEALPY_QUOTA_PROVIDE",
    "CAP_FEALPY_SCHEDULER_DRYRUN",
    "CAP_FEALPY_STUDY_RUN",
    "CAP_FEALPY_TASK_ISSUE",
    "CAP_FEALPY_VALIDATE_REPORT",
    "FEALPY_COMPILER_SLOT",
    "FEALPY_ENVIRONMENT_SLOT",
    "FEALPY_EXECUTOR_SLOT",
    "FEALPY_GATEWAY_SLOT",
    "FEALPY_QUOTA_PROVIDER_SLOT",
    "FEALPY_STUDY_SLOT",
    "FEALPY_VALIDATOR_SLOT",
    "FealpyAsyncExecutor",
    "FealpyBackend",
    "FealpyBackendComparisonResult",
    "FealpyBackendComparisonRunner",
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
    "FealpyK8sBackend",
    "FealpyK8sJobSpec",
    "FealpyMeshSpec",
    "FealpyMeshType",
    "FealpyOptimizerStrategy",
    "FealpyPdeFamily",
    "FealpyPolicyReport",
    "FealpyProblemSpec",
    "FealpyProposalEvaluation",
    "FealpyResourceQuotaProvider",
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
    "estimate_dofs",
    "fealpy_case_catalog",
    "get_fealpy_cases",
    "estimate_memory_mb",
    "estimate_taylor_hood_dofs",
]
