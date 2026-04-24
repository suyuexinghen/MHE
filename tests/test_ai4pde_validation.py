from metaharness_ext.ai4pde.components.physics_validator import PhysicsValidatorComponent
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


def test_ai4pde_validator_populates_promotion_and_rollback_metadata() -> None:
    plan = PDEPlan(
        plan_id="plan-validate",
        task_id="task-validate",
        selected_method=SolverFamily.PINN_STRONG,
    )
    artifact = run_pinn_strong(plan)
    reference = ReferenceSolverComponent().run_reference(plan)

    validation = PhysicsValidatorComponent().validate_run(
        artifact,
        graph_version_id=4,
        reference_result=reference,
    )

    assert validation.candidate_identity.candidate_id == artifact.run_id
    assert validation.candidate_identity.graph_version_id == 4
    assert validation.promotion_metadata.candidate_identity.candidate_id == artifact.run_id
    assert validation.safety_evaluation.protection.protected_components == ["physics_validator"]
    assert validation.rollback_context.rollback_recommended is False
    assert validation.scored_evidence is not None
    assert validation.scored_evidence.score > 0.0
    assert validation.scored_evidence.metrics["residual_l2"] == 0.01
    assert len(validation.session_events) == 1
    assert validation.session_events[0].event_type.value == "candidate_validated"
    assert validation.provenance["candidate_id"] == artifact.run_id
