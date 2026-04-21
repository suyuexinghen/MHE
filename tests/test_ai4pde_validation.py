from metaharness_ext.ai4pde.components.reference_solver import ReferenceSolverComponent
from metaharness_ext.ai4pde.contracts import PDEPlan, PDETaskRequest
from metaharness_ext.ai4pde.executors import run_pinn_strong
from metaharness_ext.ai4pde.templates import (
    can_instantiate_template,
    instantiate_template_for_task,
    list_templates,
    promote_template_status,
)
from metaharness_ext.ai4pde.types import ProblemType, SolverFamily, TemplateStatus
from metaharness_ext.ai4pde.validation import (
    compare_against_reference,
    summarize_boundary_conditions,
    summarize_residuals,
)


def test_ai4pde_validation_helpers_return_minimal_summaries() -> None:
    plan = PDEPlan(
        plan_id="plan-1",
        task_id="task-1",
        selected_method=SolverFamily.PINN_STRONG,
    )
    artifact = run_pinn_strong(plan)

    residuals = summarize_residuals(artifact)
    boundaries = summarize_boundary_conditions(artifact)
    reference = ReferenceSolverComponent().run_reference(plan)
    comparison = compare_against_reference(artifact, reference)

    assert residuals["residual_l2"] == 0.01
    assert residuals["residual_ok"] == 1.0
    assert boundaries["boundary_error"] == 0.0
    assert boundaries["boundary_ok"] == 1.0
    assert comparison["baseline_residual_l2"] == 0.02
    assert comparison["status"] == "better_or_equal"


def test_ai4pde_templates_can_be_listed_and_instantiated() -> None:
    templates = list_templates()

    assert len(templates) >= 3
    assert all(
        can_instantiate_template(template)
        for template in templates
        if template.status != TemplateStatus.DRAFT
    )

    request = PDETaskRequest(
        task_id="task-template",
        goal="solve a forward PDE",
        problem_type=ProblemType.FORWARD,
    )
    template, template_data = instantiate_template_for_task(request)

    assert template is not None
    assert template.template_id == "forward-solid-mechanics"
    assert template_data["selected_method"] == SolverFamily.PINN_STRONG
    assert template_data["parameter_overrides"]["benchmark_profile"] == "solid-forward"


def test_ai4pde_template_status_promotion_is_threshold_based() -> None:
    template = list_templates()[0]

    assert promote_template_status(template, successful_benchmarks=0) == TemplateStatus.DRAFT
    assert promote_template_status(template, successful_benchmarks=1) == TemplateStatus.CANDIDATE
    assert promote_template_status(template, successful_benchmarks=3) == TemplateStatus.STABLE
