from pathlib import Path

import pytest

from metaharness_ext.ai4pde.case_parser import (
    Ai4PdeCaseXmlError,
    parse_ai4pde_case_xml,
    parse_ai4pde_case_xml_text,
)
from metaharness_ext.ai4pde.types import ProblemType, RiskLevel, SolverFamily

CASE_XML = Path(__file__).parent.parent / ".trash" / "xml-demo" / "cylinder-flow-re100.xml"


def test_parse_ai4pde_case_xml_compiles_request_and_plan() -> None:
    task, plan = parse_ai4pde_case_xml(CASE_XML)

    assert task.task_id == "cylinder-flow-re100"
    assert task.problem_type == ProblemType.FORWARD
    assert task.goal == (
        "forward:incompressible_navier_stokes:cylinder_in_channel:classical_hybrid/nektar++"
    )
    assert task.budget.cpu_hours == 4.0
    assert task.risk_level == RiskLevel.YELLOW
    assert task.physics_spec["reference"]["kind"] == "literature"
    assert task.data_spec["runtime"]["required_components"][0] == "pde_gateway.primary"
    assert task.deliverables == [
        "solution_field",
        "validation_summary",
        "evidence_bundle",
        "vtu_field",
        "png_snapshot",
        "residual_curve",
        "drag_lift_curve",
        "derived_field/vorticity",
    ]

    assert plan.plan_id == "plan-cylinder-flow-re100"
    assert plan.task_id == "cylinder-flow-re100"
    assert plan.selected_method == SolverFamily.CLASSICAL_HYBRID
    assert plan.template_id == "forward-fluid-mechanics"
    assert plan.graph_family == "template::forward-fluid-mechanics"
    assert plan.slot_bindings == {
        "solver_executor.primary": "classical_hybrid",
        "reference_solver.primary": "classical_hybrid",
        "knowledge_adapter.primary": "nektar_case_library",
    }
    assert plan.parameter_overrides["backend"] == "nektar++"
    assert plan.parameter_overrides["nektar_solver"] == "IncNavierStokesSolver"
    assert plan.parameter_overrides["reference"]["metric"] == "drag_lift_residual"
    assert plan.required_validators == [
        "residuals",
        "boundary_consistency",
        "conservation",
        "boundary_conditions",
        "reference_compare",
    ]
    assert plan.expected_artifacts == [
        "solution_field",
        "validation_bundle",
        "evidence_bundle",
        "vtu_field",
        "png_snapshot",
        "residual_curve",
        "drag_lift_curve",
        "derived_field/vorticity",
    ]


def test_parse_ai4pde_case_xml_rejects_missing_required_component(test_runs_dir: Path) -> None:
    broken_case_dir = test_runs_dir / "ai4pde-case-parser"
    broken_case_dir.mkdir(parents=True, exist_ok=True)
    broken_xml = CASE_XML.read_text().replace(
        "knowledge_adapter.primary",
        "missing_component.primary",
    )

    with pytest.raises(Ai4PdeCaseXmlError, match="missing_component.primary"):
        parse_ai4pde_case_xml_text(broken_xml, base_dir=broken_case_dir)
