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


def test_compiler_tier1_pde_families_compile() -> None:
    """All Tier-1 scalar diffusion families produce valid plans."""
    from metaharness_ext.fealpy.compiler import _SCALAR_DIFFUSION_FAMILIES

    compiler = FealpyCompilerComponent()
    for family in sorted(_SCALAR_DIFFUSION_FAMILIES):
        spec = FealpyProblemSpec(
            task_id=f"compile-{family}",
            pde_family=family,  # type: ignore[arg-type]
            mesh=FealpyMeshSpec(meshtype="tri", nx=4, ny=4),
        )
        plan = compiler.compile(spec)
        assert f"PDEModelManager('{family}')" in plan.script_source


def test_compiler_generated_script_has_bc_dispatch() -> None:
    """Generated script includes runtime BC dispatch for PDE attributes."""
    compiler = FealpyCompilerComponent()
    plan = compiler.compile(_spec())
    source = plan.script_source
    assert "hasattr(pde, 'dirichlet')" in source
    assert "hasattr(pde, 'gradient')" in source
    assert "DirichletBC(space, gd=pde.solution)" in source


def test_compiler_solver_method_wired() -> None:
    """spec.solver.method is wired into spsolve call."""
    from metaharness_ext.fealpy.contracts import FealpySolverSpec

    spec = _spec()
    spec.solver = FealpySolverSpec(method="cg")
    compiler = FealpyCompilerComponent()
    plan = compiler.compile(spec)
    assert "spsolve(A, F, solver='cg')" in plan.script_source


def test_compiler_fe_space_type_in_script() -> None:
    """spec.fe_space_type appears in the generated script dispatch."""
    spec = _spec()
    spec.fe_space_type = "Lagrange"
    compiler = FealpyCompilerComponent()
    plan = compiler.compile(spec)
    assert 'fe_space_type == "Lagrange"' in plan.script_source


def test_compiler_different_pde_family_different_plan_id() -> None:
    """Different PDE families produce different plan IDs."""
    compiler = FealpyCompilerComponent()
    s1 = _spec()
    s2 = FealpyProblemSpec(
        task_id="compile-test",
        pde_family="wave",
        mesh=FealpyMeshSpec(meshtype="tri", nx=4, ny=4),
    )
    assert compiler.compile(s1).plan_id != compiler.compile(s2).plan_id
