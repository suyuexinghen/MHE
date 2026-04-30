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
    from metaharness_ext.fealpy.compiler import _FAMILY_RENDERERS

    scalar_families = {k for k, v in _FAMILY_RENDERERS.items() if v == "_render_scalar_diffusion"}
    compiler = FealpyCompilerComponent()
    for family in sorted(scalar_families):
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
    spec.solver = FealpySolverSpec(method="scipy")
    compiler = FealpyCompilerComponent()
    plan = compiler.compile(spec)
    assert "spsolve(A, F, solver='scipy')" in plan.script_source


def test_compiler_fe_space_type_in_script() -> None:
    """Scalar diffusion template uses LagrangeFESpace directly."""
    spec = _spec()
    spec.fe_space_type = "Lagrange"
    compiler = FealpyCompilerComponent()
    plan = compiler.compile(spec)
    assert "LagrangeFESpace(mesh, p=1)" in plan.script_source
    assert "ScalarDiffusionIntegrator()" in plan.script_source


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


# ── Tier 2 PDE family templates ────────────────────────────────────────────


def test_render_curl_curl_template():
    compiler = FealpyCompilerComponent()
    spec = FealpyProblemSpec(
        task_id="cc-test",
        pde_family="curlcurl",
        mesh=FealpyMeshSpec(meshtype="tri", nx=4, ny=4),
    )
    plan = compiler.compile(spec)
    source = plan.script_source
    assert "FirstNedelecFESpace" in source
    assert "CurlCurlIntegrator" in source
    assert "PDEModelManager('curlcurl')" in source


def test_render_linear_elasticity_template():
    compiler = FealpyCompilerComponent()
    spec = FealpyProblemSpec(
        task_id="le-test",
        pde_family="linear_elasticity",
        mesh=FealpyMeshSpec(meshtype="tri", nx=4, ny=4),
    )
    plan = compiler.compile(spec)
    source = plan.script_source
    assert "HuZhangFESpace" in source
    assert "LinearElasticityIntegrator" in source
    assert "ElasticMaterial" in source
    assert "VectorSourceIntegrator" in source
    assert "PDEModelManager('linear_elasticity')" in source


def test_render_darcy_template():
    compiler = FealpyCompilerComponent()
    spec = FealpyProblemSpec(
        task_id="darcy-test",
        pde_family="darcy",
        mesh=FealpyMeshSpec(meshtype="tri", nx=4, ny=4),
    )
    plan = compiler.compile(spec)
    source = plan.script_source
    assert "RaviartThomasFESpace" in source
    assert "BlockForm" in source
    assert "DivIntegrator" in source
    assert "PDEModelManager('darcy')" in source


def test_render_stokes_template():
    compiler = FealpyCompilerComponent()
    spec = FealpyProblemSpec(
        task_id="stokes-test",
        pde_family="stokes",
        mesh=FealpyMeshSpec(meshtype="tri", nx=4, ny=4),
    )
    plan = compiler.compile(spec)
    source = plan.script_source
    assert "ViscousWorkIntegrator" in source
    assert "BlockForm" in source
    assert "DivIntegrator" in source
    assert "velocity_space = LagrangeFESpace(mesh, p=2)" in source
    assert "pressure_space = LagrangeFESpace(mesh, p=1)" in source
    assert "PDEModelManager('stokes')" in source


def test_darcyforchheimer_uses_render_darcy():
    compiler = FealpyCompilerComponent()
    spec = FealpyProblemSpec(
        task_id="df-test",
        pde_family="darcyforchheimer",
        mesh=FealpyMeshSpec(meshtype="tri", nx=4, ny=4),
    )
    plan = compiler.compile(spec)
    assert "RaviartThomasFESpace" in plan.script_source


def test_unknown_family_falls_back_to_scalar_diffusion():
    compiler = FealpyCompilerComponent()
    spec = FealpyProblemSpec(
        task_id="unknown-test",
        pde_family="optimal_control",  # not yet in _FAMILY_RENDERERS
        mesh=FealpyMeshSpec(meshtype="tri", nx=4, ny=4),
    )
    plan = compiler.compile(spec)
    assert "ScalarDiffusionIntegrator" in plan.script_source
    assert "LagrangeFESpace" in plan.script_source


# ── 3D mesh rendering ──────────────────────────────────────────────────


def test_render_mesh_builder_3d_tet() -> None:
    compiler = FealpyCompilerComponent()
    spec = FealpyProblemSpec(
        task_id="mesh-3d-tet",
        pde_family="poisson",
        mesh=FealpyMeshSpec(meshtype="tet", nx=4, ny=4, nz=4),
    )
    plan = compiler.compile(spec)
    source = plan.script_source
    assert "TetrahedronMesh.from_box" in source
    assert "nz=nz or nx" in source


def test_render_mesh_builder_3d_hex() -> None:
    compiler = FealpyCompilerComponent()
    spec = FealpyProblemSpec(
        task_id="mesh-3d-hex",
        pde_family="poisson",
        mesh=FealpyMeshSpec(meshtype="hex", nx=4, ny=4, nz=4),
    )
    plan = compiler.compile(spec)
    source = plan.script_source
    assert "HexahedronMesh.from_box" in source


def test_render_mesh_builder_3d_uniform() -> None:
    compiler = FealpyCompilerComponent()
    spec = FealpyProblemSpec(
        task_id="mesh-3d-uniform",
        pde_family="poisson",
        mesh=FealpyMeshSpec(meshtype="uniform", nx=4, ny=4, nz=4),
    )
    plan = compiler.compile(spec)
    source = plan.script_source
    assert "UniformMesh3d.from_box" in source


# ── Tier 3: transient + nonlinear PDE templates ───────────────────────


def test_render_allen_cahn_template() -> None:
    compiler = FealpyCompilerComponent()
    spec = FealpyProblemSpec(
        task_id="ac-test",
        pde_family="allen_cahn",
        mesh=FealpyMeshSpec(meshtype="tri", nx=4, ny=4),
        dt=0.01,
        num_time_steps=50,
    )
    plan = compiler.compile(spec)
    source = plan.script_source
    assert "ScalarDiffusionIntegrator" in source
    assert "ScalarMassIntegrator" in source
    assert "for step in range(50)" in source
    assert "dt_inv = 1.0 / 0.01" in source
    assert "u[:] ** 3 - u[:]" in source  # double-well nonlinearity
    assert "PDEModelManager('allen_cahn')" in source
    assert "epsilon" in source
    assert "num_time_steps" in source


def test_render_allen_cahn_different_dt_different_plan_id() -> None:
    compiler = FealpyCompilerComponent()
    spec1 = FealpyProblemSpec(
        task_id="ac-dt",
        pde_family="allen_cahn",
        mesh=FealpyMeshSpec(meshtype="tri", nx=4, ny=4),
        dt=0.01,
    )
    spec2 = FealpyProblemSpec(
        task_id="ac-dt",
        pde_family="allen_cahn",
        mesh=FealpyMeshSpec(meshtype="tri", nx=4, ny=4),
        dt=0.05,
    )
    assert compiler.compile(spec1).plan_id != compiler.compile(spec2).plan_id


def test_render_navier_stokes_template() -> None:
    compiler = FealpyCompilerComponent()
    spec = FealpyProblemSpec(
        task_id="ns-test",
        pde_family="navier_stokes",
        mesh=FealpyMeshSpec(meshtype="tri", nx=4, ny=4),
        dt=0.01,
        num_time_steps=20,
    )
    plan = compiler.compile(spec)
    source = plan.script_source
    assert "velocity_space = LagrangeFESpace(mesh, p=2)" in source
    assert "pressure_space = LagrangeFESpace(mesh, p=1)" in source
    assert "ViscousWorkIntegrator" in source
    assert "BlockForm" in source
    assert "DivIntegrator" in source
    assert "for step in range(20)" in source
    assert "picard_iter" in source
    assert "PDEModelManager('navier_stokes')" in source


def test_render_navier_stokes_different_num_steps_different_plan_id() -> None:
    compiler = FealpyCompilerComponent()
    spec1 = FealpyProblemSpec(
        task_id="ns-steps",
        pde_family="navier_stokes",
        mesh=FealpyMeshSpec(meshtype="tri", nx=4, ny=4),
        num_time_steps=10,
    )
    spec2 = FealpyProblemSpec(
        task_id="ns-steps",
        pde_family="navier_stokes",
        mesh=FealpyMeshSpec(meshtype="tri", nx=4, ny=4),
        num_time_steps=50,
    )
    assert compiler.compile(spec1).plan_id != compiler.compile(spec2).plan_id


def test_allen_cahn_contains_time_loop_and_nonlinear() -> None:
    compiler = FealpyCompilerComponent()
    plan = compiler.compile(
        FealpyProblemSpec(
            task_id="ac-loop",
            pde_family="allen_cahn",
            mesh=FealpyMeshSpec(meshtype="tri", nx=4, ny=4),
        )
    )
    source = plan.script_source
    assert "for step in range(" in source
    assert "double-well" in source.lower() or "** 3" in source


def test_navier_stokes_contains_picard_convergence() -> None:
    compiler = FealpyCompilerComponent()
    plan = compiler.compile(
        FealpyProblemSpec(
            task_id="ns-picard",
            pde_family="navier_stokes",
            mesh=FealpyMeshSpec(meshtype="tri", nx=4, ny=4),
        )
    )
    source = plan.script_source
    assert "max_picard_iters" in source
    assert "picard_rtol" in source
    assert "norm_diff < picard_rtol" in source
