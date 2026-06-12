from __future__ import annotations

from metaharness.benchmark_drivers.models import BenchmarkCaseSpec, MetricReference

MOOSE_ROOT = "/home/linden/code/work/Solvers/FEM/moose"
SIMPLE_DIFFUSION_INPUT = """[Mesh]
  type = GeneratedMesh
  dim = 2
  nx = 10
  ny = 10
[]

[Variables]
  [u]
  []
[]

[Kernels]
  [diff]
    type = Diffusion
    variable = u
  []
[]

[BCs]
  [left]
    type = DirichletBC
    variable = u
    boundary = left
    value = 0
  []
  [right]
    type = DirichletBC
    variable = u
    boundary = right
    value = 1
  []
[]

[Executioner]
  type = Steady
  solve_type = 'PJFNK'
  petsc_options_iname = '-pc_type'
  petsc_options_value = 'hypre'
[]

[Outputs]
  exodus = true
[]
"""


def moose_case_catalog() -> dict[str, BenchmarkCaseSpec]:
    cases = [
        BenchmarkCaseSpec(
            case_id="simple-diffusion-hit",
            suite="moose-usage",
            task_family="moose_fem_input",
            description="MOOSE test-app simple diffusion HIT input workflow with Exodus output evidence.",
            required_capabilities=["moose.execute.run", "moose.validate.report"],
            source_reference={
                "input": f"{MOOSE_ROOT}/test/tests/kernels/simple_diffusion/simple_diffusion.i",
                "binary": f"{MOOSE_ROOT}/test/moose_test-opt",
                "source_root": MOOSE_ROOT,
            },
            expected_metrics=["spec_valid", "plan_valid", "output_count", "elapsed_seconds"],
            reference_metrics={
                "spec_valid": MetricReference(value=1.0, tolerance=0.0),
                "plan_valid": MetricReference(value=1.0, tolerance=0.0),
                "output_count": MetricReference(value=1.0, tolerance=0.0),
            },
            problem_definition={
                "input_source": SIMPLE_DIFFUSION_INPUT,
                "input_filename": "input.i",
                "expected_output": "input_out.e",
                "solver_family": "moose_test_app",
                "execution_mode": "steady_diffusion",
            },
            metadata={
                "proposal_contract": "moose_hit_input_v1",
                "allow_direct_fallback": True,
                "real_tool_default_binary": f"{MOOSE_ROOT}/test/moose_test-opt",
                "claim_boundary": "workflow and artifact evidence only; no numerical superiority claim",
                "scientific_review_status": "pending_external_signoff",
                "domain_metric_status": "solver-log metrics only; no analytic error reference",
            },
        ),
        BenchmarkCaseSpec(
            case_id="malformed-hit-proposal",
            suite="moose-usage",
            task_family="moose_proposal_repair",
            description="Malformed MOOSE proposal contrast where direct fails contract validation and agent records deterministic repair evidence.",
            required_capabilities=["moose.input.compile", "moose.evidence.bundle"],
            source_reference={
                "input": f"{MOOSE_ROOT}/test/tests/kernels/simple_diffusion/simple_diffusion.i",
                "source_root": MOOSE_ROOT,
            },
            expected_metrics=["spec_valid", "plan_valid", "output_count", "elapsed_seconds"],
            reference_metrics={
                "spec_valid": MetricReference(value=1.0, tolerance=0.0),
                "plan_valid": MetricReference(value=1.0, tolerance=0.0),
                "output_count": MetricReference(value=1.0, tolerance=0.0),
            },
            problem_definition={
                "input_source": SIMPLE_DIFFUSION_INPUT,
                "input_filename": "input.i",
                "expected_output": "input_out.e",
                "solver_family": "moose_test_app",
                "execution_mode": "steady_diffusion",
            },
            metadata={
                "proposal_contract": "moose_hit_input_v1",
                "malformed_direct_challenge": True,
                "claim_boundary": "agent repair evidence is workflow evidence, not solver evidence",
                "scientific_review_status": "pending_external_signoff",
                "domain_metric_status": "solver-log metrics only; no analytic error reference",
            },
        ),
    ]
    return {case.case_id: case for case in cases}


def get_moose_cases(case_ids: list[str] | None = None) -> list[BenchmarkCaseSpec]:
    catalog = moose_case_catalog()
    if not case_ids:
        return list(catalog.values())
    return [catalog[case_id] for case_id in case_ids]
