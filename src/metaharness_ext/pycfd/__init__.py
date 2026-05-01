from __future__ import annotations

from metaharness_ext.pycfd.benchmark_cases import get_pycfd_cases, pycfd_case_catalog  # noqa: F401
from metaharness_ext.pycfd.benchmark_runner import PyCFDBenchmarkRunner  # noqa: F401
from metaharness_ext.pycfd.capabilities import (  # noqa: F401
    CANONICAL_CAPABILITIES,
    CAP_PYCFD_COMPILE,
    CAP_PYCFD_ENV_PROBE,
    CAP_PYCFD_EXECUTE_RUN,
    CAP_PYCFD_OPTIMIZER_PROPOSE,
    CAP_PYCFD_QUOTA_PROVIDE,
    CAP_PYCFD_SCHEDULER_DRYRUN,
    CAP_PYCFD_STUDY_RUN,
    CAP_PYCFD_TASK_ISSUE,
    CAP_PYCFD_VALIDATE_REPORT,
)
from metaharness_ext.pycfd.compiler import PyCFDCompilerComponent  # noqa: F401
from metaharness_ext.pycfd.contracts import (  # noqa: F401
    PyCFDEnvironmentReport,
    PyCFDEvidenceBundle,
    PyCFDEvidenceWarning,
    PyCFDFlowSpec,
    PyCFDMeshSpec,
    PyCFDPolicyReport,
    PyCFDProblemSpec,
    PyCFDRunArtifact,
    PyCFDRunPlan,
    PyCFDSolverSpec,
    PyCFDStudyAxis,
    PyCFDStudyReport,
    PyCFDStudySpec,
    PyCFDStudyTrial,
    PyCFDValidationReport,
)
from metaharness_ext.pycfd.environment import PyCFDEnvironmentProbeComponent  # noqa: F401
from metaharness_ext.pycfd.evidence import build_evidence_bundle  # noqa: F401
from metaharness_ext.pycfd.executor import PyCFDExecutorComponent  # noqa: F401
from metaharness_ext.pycfd.gateway import PyCFDGatewayComponent  # noqa: F401
from metaharness_ext.pycfd.governance import PyCFDGovernanceAdapter  # noqa: F401
from metaharness_ext.pycfd.policy import PyCFDEvidencePolicy  # noqa: F401
from metaharness_ext.pycfd.slots import (  # noqa: F401
    PROTECTED_SLOTS,
    PYCFD_COMPILER_SLOT,
    PYCFD_ENVIRONMENT_SLOT,
    PYCFD_EXECUTOR_SLOT,
    PYCFD_GATEWAY_SLOT,
    PYCFD_QUOTA_PROVIDER_SLOT,
    PYCFD_STUDY_SLOT,
    PYCFD_VALIDATOR_SLOT,
)
from metaharness_ext.pycfd.study import PyCFDStudyComponent  # noqa: F401
from metaharness_ext.pycfd.types import (  # noqa: F401
    PyCFDCaseType,
    PyCFDFlowType,
    PyCFDFluxType,
    PyCFDLimiterType,
    PyCFDMeshType,
    PyCFDRunArtifactStatus,
    PyCFDSolverType,
    PyCFDValidationStatus,
)
from metaharness_ext.pycfd.validator import PyCFDValidatorComponent  # noqa: F401
