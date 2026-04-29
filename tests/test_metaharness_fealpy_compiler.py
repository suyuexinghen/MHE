from metaharness_ext.fealpy.compiler import FealpyCompilerComponent
from metaharness_ext.fealpy.contracts import FealpyMeshSpec, FealpyProblemSpec


def _spec() -> FealpyProblemSpec:
    return FealpyProblemSpec(
        task_id="compile-test",
        pde_family="poisson",
        example_key=1,
        backend="numpy",
        mesh=FealpyMeshSpec(meshtype="tri", nx=4, ny=4),
        fe_degree=1,
    )


def test_compiler_deterministic_plan_id() -> None:
    compiler = FealpyCompilerComponent()
    spec = _spec()
    plan1 = compiler.compile(spec)
    plan2 = compiler.compile(spec)
    assert plan1.plan_id == plan2.plan_id
    assert plan1.run_id == plan2.run_id


def test_compiler_different_spec_different_plan_id() -> None:
    compiler = FealpyCompilerComponent()
    spec1 = _spec()
    spec2 = FealpyProblemSpec(
        task_id="compile-test",
        pde_family="poisson",
        example_key=2,
        backend="numpy",
        mesh=FealpyMeshSpec(meshtype="tri", nx=4, ny=4),
        fe_degree=1,
    )
    plan1 = compiler.compile(spec1)
    plan2 = compiler.compile(spec2)
    assert plan1.plan_id != plan2.plan_id


def test_compiler_script_contains_expected_lines() -> None:
    compiler = FealpyCompilerComponent()
    plan = compiler.compile(_spec())
    source = plan.script_source
    assert "import fealpy" not in source  # uses from-imports
    assert "from fealpy.backend import backend_manager" in source
    assert "from fealpy.fem import BilinearForm" in source
    assert "from fealpy.model import PDEModelManager" in source
    assert "PDEModelManager('poisson')" in source
    assert "get_example(1)" in source
    assert "LagrangeFESpace" in source
    assert "json.dumps" in source


def test_compiler_plan_fields() -> None:
    compiler = FealpyCompilerComponent()
    plan = compiler.compile(_spec())
    assert plan.task_id == "compile-test"
    assert plan.plan_id.startswith("fealpy-compile-test-")
    assert plan.run_id.startswith("run-")
    assert plan.experiment_ref == "compile-test"
    assert ".runs/fealpy/" in plan.workspace_dir
    assert len(plan.evidence_refs) > 0


def test_compiler_rejects_unavailable_environment() -> None:
    import pytest

    from metaharness_ext.fealpy.contracts import FealpyEnvironmentReport

    compiler = FealpyCompilerComponent()
    env = FealpyEnvironmentReport(
        task_id="compile-test", available=False, status="prerequisite_missing"
    )
    with pytest.raises(ValueError, match="unavailable"):
        compiler.compile(_spec(), environment=env)
