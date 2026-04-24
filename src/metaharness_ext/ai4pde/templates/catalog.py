from __future__ import annotations

from pydantic import BaseModel, Field

from metaharness_ext.ai4pde.slots import (
    EVIDENCE_MANAGER_SLOT,
    METHOD_ROUTER_SLOT,
    PHYSICS_VALIDATOR_SLOT,
    PROBLEM_FORMULATOR_SLOT,
    REFERENCE_SOLVER_SLOT,
    SOLVER_EXECUTOR_SLOT,
)
from metaharness_ext.ai4pde.types import ProblemType, RiskLevel, SolverFamily, TemplateStatus


class PDETemplate(BaseModel):
    template_id: str
    name: str
    task_family: ProblemType
    supported_slots: list[str] = Field(default_factory=list)
    fixed_contracts: list[str] = Field(default_factory=list)
    variable_params: list[str] = Field(default_factory=list)
    required_validators: list[str] = Field(default_factory=list)
    supported_methods: list[SolverFamily] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.GREEN
    reproducibility_requirements: list[str] = Field(default_factory=list)
    benchmark_profile: str = "default"
    version: str = "0.1.0"
    status: TemplateStatus = TemplateStatus.DRAFT


_DEFAULT_CATALOG = {
    "forward-solid-mechanics": PDETemplate(
        template_id="forward-solid-mechanics",
        name="ForwardSolidMechanicsTemplate",
        task_family=ProblemType.FORWARD,
        supported_slots=[
            PROBLEM_FORMULATOR_SLOT,
            METHOD_ROUTER_SLOT,
            SOLVER_EXECUTOR_SLOT,
            REFERENCE_SOLVER_SLOT,
            PHYSICS_VALIDATOR_SLOT,
            EVIDENCE_MANAGER_SLOT,
        ],
        fixed_contracts=["physics_spec", "ScientificEvidenceBundle"],
        variable_params=["loss_weights", "collocation_strategy"],
        required_validators=["residuals", "boundary_conditions", "reference_compare"],
        supported_methods=[SolverFamily.PINN_STRONG, SolverFamily.CLASSICAL_HYBRID],
        risk_level=RiskLevel.YELLOW,
        reproducibility_requirements=["baseline_compare", "evidence_bundle"],
        benchmark_profile="solid-forward",
        status=TemplateStatus.STABLE,
    ),
    "forward-fluid-mechanics": PDETemplate(
        template_id="forward-fluid-mechanics",
        name="ForwardFluidMechanicsTemplate",
        task_family=ProblemType.FORWARD,
        supported_slots=[
            PROBLEM_FORMULATOR_SLOT,
            METHOD_ROUTER_SLOT,
            SOLVER_EXECUTOR_SLOT,
            PHYSICS_VALIDATOR_SLOT,
            EVIDENCE_MANAGER_SLOT,
        ],
        fixed_contracts=["physics_spec", "ValidationBundle"],
        variable_params=["routing_thresholds", "stopping_criteria"],
        required_validators=["residuals", "boundary_conditions"],
        supported_methods=[
            SolverFamily.PINN_STRONG,
            SolverFamily.PINO,
            SolverFamily.CLASSICAL_HYBRID,
        ],
        risk_level=RiskLevel.YELLOW,
        reproducibility_requirements=["residual_trace"],
        benchmark_profile="fluid-forward",
        status=TemplateStatus.CANDIDATE,
    ),
    "inverse-parameter-identification": PDETemplate(
        template_id="inverse-parameter-identification",
        name="InverseParameterIdentificationTemplate",
        task_family=ProblemType.INVERSE,
        supported_slots=[
            PROBLEM_FORMULATOR_SLOT,
            METHOD_ROUTER_SLOT,
            SOLVER_EXECUTOR_SLOT,
            REFERENCE_SOLVER_SLOT,
            PHYSICS_VALIDATOR_SLOT,
            EVIDENCE_MANAGER_SLOT,
        ],
        fixed_contracts=["physics_spec", "ScientificEvidenceBundle", "reference_compare"],
        variable_params=["optimizer_params", "batch_size"],
        required_validators=["residuals", "boundary_conditions", "reference_compare"],
        supported_methods=[SolverFamily.CLASSICAL_HYBRID, SolverFamily.PINN_STRONG],
        risk_level=RiskLevel.RED,
        reproducibility_requirements=["baseline_compare", "benchmark_snapshot"],
        benchmark_profile="inverse-identification",
        status=TemplateStatus.CANDIDATE,
    ),
}


def get_default_catalog() -> dict[str, PDETemplate]:
    return {key: value.model_copy(deep=True) for key, value in _DEFAULT_CATALOG.items()}


def list_templates() -> list[PDETemplate]:
    return list(get_default_catalog().values())


def get_template(template_id: str) -> PDETemplate | None:
    template = _DEFAULT_CATALOG.get(template_id)
    if template is None:
        return None
    return template.model_copy(deep=True)
