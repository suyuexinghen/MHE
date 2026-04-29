"""Multi-backend and multi-PDE real fealpy integration smoke tests.

Requires MHE_RUN_REAL_FEALPY=1 and the relevant backends installed.
"""

from __future__ import annotations

import os

import pytest

from metaharness_ext.fealpy.compiler import FealpyCompilerComponent
from metaharness_ext.fealpy.contracts import FealpyMeshSpec, FealpyProblemSpec
from metaharness_ext.fealpy.environment import FealpyEnvironmentProbeComponent
from metaharness_ext.fealpy.executor import FealpyExecutorComponent
from metaharness_ext.fealpy.validator import FealpyValidatorComponent

pytestmark = pytest.mark.skipif(
    os.environ.get("MHE_RUN_REAL_FEALPY") != "1",
    reason="Set MHE_RUN_REAL_FEALPY=1 to run real fealpy integration tests",
)


def _spec(*, pde_family: str = "poisson", backend: str = "numpy") -> FealpyProblemSpec:
    return FealpyProblemSpec(
        task_id=f"smoke-{pde_family}-{backend}",
        pde_family=pde_family,
        example_key=1,
        backend=backend,
        mesh=FealpyMeshSpec(meshtype="tri", nx=8, ny=8),
        fe_degree=1,
        timeout_seconds=60,
    )


def _compile_and_run(spec: FealpyProblemSpec):
    env = FealpyEnvironmentProbeComponent().probe(spec)
    plan = FealpyCompilerComponent().compile(spec, environment=env)
    artifact = FealpyExecutorComponent().execute_plan(plan, environment=env)
    return plan, artifact, env


# ── Non-Poisson Tier-1 PDE families ─────────────────────────────────────


def test_poisson_real() -> None:
    spec = _spec(pde_family="poisson")
    plan, artifact, env = _compile_and_run(spec)
    assert artifact.status == "completed", f"poisson failed: {artifact.error_message}"
    report = FealpyValidatorComponent().validate(
        artifact, plan, l2_tolerance=1.0, h1_tolerance=10.0
    )
    assert report.passed is True


def test_diffusion_convection_reaction_real() -> None:
    spec = _spec(pde_family="diffusion_convection_reaction")
    plan, artifact, env = _compile_and_run(spec)
    assert artifact.status == "completed", f"dcr failed: {artifact.error_message}"
    report = FealpyValidatorComponent().validate(
        artifact, plan, l2_tolerance=1.0, h1_tolerance=10.0
    )
    assert report.passed is True


def test_diffusion_reaction_real() -> None:
    spec = _spec(pde_family="diffusion_reaction")
    plan, artifact, env = _compile_and_run(spec)
    assert artifact.status == "completed", f"diffusion_reaction failed: {artifact.error_message}"
    report = FealpyValidatorComponent().validate(
        artifact, plan, l2_tolerance=1.0, h1_tolerance=10.0
    )
    assert report.passed is True


def test_hyperbolic_real() -> None:
    spec = _spec(pde_family="hyperbolic")
    plan, artifact, env = _compile_and_run(spec)
    assert artifact.status == "completed", f"hyperbolic failed: {artifact.error_message}"
    report = FealpyValidatorComponent().validate(
        artifact, plan, l2_tolerance=1.0, h1_tolerance=10.0
    )
    assert report.passed is True


def test_wave_real() -> None:
    spec = _spec(pde_family="wave")
    plan, artifact, env = _compile_and_run(spec)
    assert artifact.status == "completed", f"wave failed: {artifact.error_message}"
    report = FealpyValidatorComponent().validate(
        artifact, plan, l2_tolerance=1.0, h1_tolerance=10.0
    )
    assert report.passed is True


def test_interface_poisson_real() -> None:
    spec = _spec(pde_family="interface_poisson")
    plan, artifact, env = _compile_and_run(spec)
    assert artifact.status == "completed", f"interface_poisson failed: {artifact.error_message}"
    report = FealpyValidatorComponent().validate(
        artifact, plan, l2_tolerance=1.0, h1_tolerance=10.0
    )
    assert report.passed is True


def test_polyharmonic_real() -> None:
    spec = _spec(pde_family="polyharmonic")
    plan, artifact, env = _compile_and_run(spec)
    assert artifact.status == "completed", f"polyharmonic failed: {artifact.error_message}"
    report = FealpyValidatorComponent().validate(
        artifact, plan, l2_tolerance=1.0, h1_tolerance=10.0
    )
    assert report.passed is True


def test_helmholtz_real() -> None:
    spec = _spec(pde_family="helmholtz")
    plan, artifact, env = _compile_and_run(spec)
    assert artifact.status == "completed", f"helmholtz failed: {artifact.error_message}"
    report = FealpyValidatorComponent().validate(
        artifact, plan, l2_tolerance=1.0, h1_tolerance=10.0
    )
    assert report.passed is True


def test_quasilinear_elliptic_real() -> None:
    spec = _spec(pde_family="quasilinear_elliptic")
    plan, artifact, env = _compile_and_run(spec)
    assert artifact.status == "completed", f"quasilinear_elliptic failed: {artifact.error_message}"
    report = FealpyValidatorComponent().validate(
        artifact, plan, l2_tolerance=1.0, h1_tolerance=10.0
    )
    assert report.passed is True


# ── Multi-backend ────────────────────────────────────────────────────────


def test_backend_pytorch_if_available() -> None:
    env = FealpyEnvironmentProbeComponent().probe(_spec())
    if "pytorch" not in env.available_backends:
        pytest.skip("pytorch backend not available")
    spec = _spec(backend="pytorch")
    plan, artifact, _ = _compile_and_run(spec)
    assert artifact.status == "completed", f"pytorch failed: {artifact.error_message}"
    assert artifact.l2_error is not None


def test_backend_jax_if_available() -> None:
    env = FealpyEnvironmentProbeComponent().probe(_spec())
    if "jax" not in env.available_backends:
        pytest.skip("jax backend not available")
    spec = _spec(backend="jax")
    plan, artifact, _ = _compile_and_run(spec)
    assert artifact.status == "completed", f"jax failed: {artifact.error_message}"
    assert artifact.l2_error is not None


# ── Study convergence smoke ──────────────────────────────────────────────


def test_convergence_study_parameter_sweep() -> None:
    """A minimal parameter sweep (nx=4,8) with the real executor."""
    from metaharness_ext.fealpy.contracts import FealpyStudyAxis, FealpyStudySpec
    from metaharness_ext.fealpy.study import FealpyStudyComponent

    spec = FealpyStudySpec(
        study_id="smoke-conv",
        task_template=_spec(pde_family="poisson"),
        axes=[
            FealpyStudyAxis(parameter_path="mesh.nx", values=[4, 8]),
        ],
        objective="l2_error",
        goal="minimize",
    )
    report = FealpyStudyComponent().run_study(spec)
    assert len(report.trials) == 2
    assert report.best_trial_id is not None
    assert report.recommended_parameters is not None
    assert report.convergence_analysis["trial_count"] == 2
