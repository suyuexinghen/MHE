from __future__ import annotations

from metaharness_ext.ai4pde.contracts import PDEPlan, PDETaskRequest
from metaharness_ext.ai4pde.slots import SOLVER_EXECUTOR_SLOT
from metaharness_ext.ai4pde.templates.catalog import PDETemplate, get_default_catalog
from metaharness_ext.ai4pde.templates.status import can_instantiate_template
from metaharness_ext.ai4pde.types import SolverFamily


def instantiate_template_for_task(
    request: PDETaskRequest,
    *,
    catalog: dict[str, PDETemplate] | None = None,
) -> tuple[PDETemplate | None, dict[str, object]]:
    active_catalog = catalog or get_default_catalog()
    for template in active_catalog.values():
        if template.task_family != request.problem_type:
            continue
        if not can_instantiate_template(template):
            continue
        selected_method = (
            template.supported_methods[0]
            if template.supported_methods
            else SolverFamily.PINN_STRONG
        )
        return template, {
            "selected_method": selected_method,
            "slot_bindings": {SOLVER_EXECUTOR_SLOT: selected_method.value},
            "required_validators": template.required_validators,
            "parameter_overrides": {"benchmark_profile": template.benchmark_profile},
        }
    return None, {
        "selected_method": SolverFamily.PINN_STRONG,
        "slot_bindings": {SOLVER_EXECUTOR_SLOT: SolverFamily.PINN_STRONG.value},
        "required_validators": ["residuals", "boundary_conditions"],
        "parameter_overrides": {},
    }


def apply_template_to_plan(
    plan: PDEPlan, template: PDETemplate | None, template_data: dict[str, object]
) -> PDEPlan:
    updated = plan.model_copy(deep=True)
    if template is not None and updated.template_id is None:
        updated.template_id = template.template_id
    if template is not None and updated.graph_family == "ai4pde-minimal":
        updated.graph_family = f"template::{template.template_id}"
    selected_method = template_data["selected_method"]
    if (
        isinstance(selected_method, SolverFamily)
        and updated.selected_method == SolverFamily.PINN_STRONG
    ):
        updated.selected_method = selected_method
    template_slot_bindings = dict(template_data["slot_bindings"])
    updated.slot_bindings = {**template_slot_bindings, **updated.slot_bindings}
    if not updated.required_validators:
        updated.required_validators = list(template_data["required_validators"])
    template_overrides = dict(template_data["parameter_overrides"])
    updated.parameter_overrides = {**template_overrides, **updated.parameter_overrides}
    if not updated.expected_artifacts:
        updated.expected_artifacts = ["solution_field", "validation_bundle", "evidence_bundle"]
    return updated
