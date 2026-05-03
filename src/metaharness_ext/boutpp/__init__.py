from __future__ import annotations

from metaharness_ext.boutpp.benchmark_cases import boutpp_usage_case_catalog, get_boutpp_usage_cases
from metaharness_ext.boutpp.benchmark_runner import BoutPPUsageValidationRunner
from metaharness_ext.boutpp.capabilities import (
    ALL_CAPABILITIES,
    BOUTPP_ENVIRONMENT_PROBE,
    BOUTPP_EVIDENCE_BUNDLE,
    BOUTPP_MPI_EXECUTE,
    BOUTPP_OPTIONS_COMPILE,
    BOUTPP_OUTPUT_POSTPROCESS,
    BOUTPP_POLICY_EVALUATE,
    BOUTPP_RESTART_EXECUTE,
    BOUTPP_STUDY_SWEEP,
    BOUTPP_VALIDATION_BASIC,
)
from metaharness_ext.boutpp.compiler import BoutPPCompilerComponent
from metaharness_ext.boutpp.contracts import (
    BoutPPEnvironmentReport,
    BoutPPEvidenceBundle,
    BoutPPEvidenceWarning,
    BoutPPMpiSpec,
    BoutPPOptionValue,
    BoutPPOutputSpec,
    BoutPPPolicyReport,
    BoutPPPostprocessReport,
    BoutPPProblemSpec,
    BoutPPRestartSpec,
    BoutPPRunArtifact,
    BoutPPRunPlan,
    BoutPPStudyAxis,
    BoutPPStudyReport,
    BoutPPStudySpec,
    BoutPPStudyTrial,
    BoutPPValidationReport,
    BoutPPValidationSpec,
)
from metaharness_ext.boutpp.environment import BoutPPEnvironmentProbeComponent
from metaharness_ext.boutpp.evidence import build_evidence_bundle
from metaharness_ext.boutpp.executor import BoutPPExecutorComponent
from metaharness_ext.boutpp.gateway import BoutPPGatewayComponent
from metaharness_ext.boutpp.governance import BoutPPGovernanceAdapter
from metaharness_ext.boutpp.policy import BoutPPEvidencePolicy
from metaharness_ext.boutpp.postprocess import BoutPPPostprocessComponent
from metaharness_ext.boutpp.slots import (
    BOUTPP_COMPILER_SLOT,
    BOUTPP_ENVIRONMENT_SLOT,
    BOUTPP_EVIDENCE_POLICY_SLOT,
    BOUTPP_EXECUTOR_SLOT,
    BOUTPP_GATEWAY_SLOT,
    BOUTPP_POSTPROCESS_SLOT,
    BOUTPP_STUDY_SLOT,
    BOUTPP_VALIDATOR_SLOT,
    PROTECTED_SLOTS,
)
from metaharness_ext.boutpp.study import BoutPPStudyComponent
from metaharness_ext.boutpp.validator import BoutPPValidatorComponent

__all__ = (
    "ALL_CAPABILITIES",
    "BOUTPP_COMPILER_SLOT",
    "BOUTPP_ENVIRONMENT_PROBE",
    "BOUTPP_ENVIRONMENT_SLOT",
    "BOUTPP_EVIDENCE_BUNDLE",
    "BOUTPP_EVIDENCE_POLICY_SLOT",
    "BOUTPP_EXECUTOR_SLOT",
    "BOUTPP_GATEWAY_SLOT",
    "BOUTPP_MPI_EXECUTE",
    "BOUTPP_OPTIONS_COMPILE",
    "BOUTPP_OUTPUT_POSTPROCESS",
    "BOUTPP_POLICY_EVALUATE",
    "BOUTPP_POSTPROCESS_SLOT",
    "BOUTPP_RESTART_EXECUTE",
    "BOUTPP_STUDY_SLOT",
    "BOUTPP_STUDY_SWEEP",
    "BOUTPP_VALIDATION_BASIC",
    "BOUTPP_VALIDATOR_SLOT",
    "BoutPPCompilerComponent",
    "BoutPPUsageValidationRunner",
    "BoutPPEnvironmentProbeComponent",
    "BoutPPEnvironmentReport",
    "BoutPPEvidenceBundle",
    "BoutPPEvidencePolicy",
    "BoutPPEvidenceWarning",
    "BoutPPExecutorComponent",
    "BoutPPGatewayComponent",
    "BoutPPGovernanceAdapter",
    "BoutPPMpiSpec",
    "BoutPPOptionValue",
    "BoutPPOutputSpec",
    "BoutPPPolicyReport",
    "BoutPPPostprocessComponent",
    "BoutPPPostprocessReport",
    "BoutPPProblemSpec",
    "BoutPPRestartSpec",
    "BoutPPRunArtifact",
    "BoutPPRunPlan",
    "BoutPPStudyAxis",
    "BoutPPStudyComponent",
    "BoutPPStudyReport",
    "BoutPPStudySpec",
    "BoutPPStudyTrial",
    "BoutPPValidationReport",
    "BoutPPValidationSpec",
    "BoutPPValidatorComponent",
    "PROTECTED_SLOTS",
    "boutpp_usage_case_catalog",
    "build_evidence_bundle",
    "get_boutpp_usage_cases",
)
