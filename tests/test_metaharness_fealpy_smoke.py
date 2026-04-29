"""Real fealpy integration smoke tests.

These tests require a working fealpy installation and are skipped by default.
Set MHE_RUN_REAL_FEALPY=1 to enable them.
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


def _spec() -> FealpyProblemSpec:
    return FealpyProblemSpec(
        task_id="smoke-poisson-1",
        pde_family="poisson",
        example_key=1,
        backend="numpy",
        mesh=FealpyMeshSpec(meshtype="tri", nx=8, ny=8),
        fe_degree=1,
        timeout_seconds=60,
    )


def test_environment_probe_real_fealpy() -> None:
    component = FealpyEnvironmentProbeComponent()
    report = component.probe(_spec())

    assert report.available is True
    assert report.status == "available"
    # fealpy may not expose __version__ — this is non-critical
    if report.fealpy_version is None:
        assert any("version" in w.lower() for w in report.warnings)
    assert "numpy" in report.available_backends
    assert "poisson" in report.available_pde_families
    assert report.blocks_promotion is False


def test_compiler_real_fealpy() -> None:
    compiler = FealpyCompilerComponent()
    env = FealpyEnvironmentProbeComponent().probe(_spec())
    plan = compiler.compile(_spec(), environment=env)

    assert plan.plan_id.startswith("fealpy-")
    assert "from fealpy" in plan.script_source
    assert plan.workspace_dir.endswith(plan.run_id)


def test_executor_real_fealpy() -> None:
    spec = _spec()
    env = FealpyEnvironmentProbeComponent().probe(spec)
    compiler = FealpyCompilerComponent()
    plan = compiler.compile(spec, environment=env)

    executor = FealpyExecutorComponent()
    artifact = executor.execute_plan(plan, environment=env)

    assert artifact.status == "completed", f"Executor failed: {artifact.error_message}"
    assert artifact.l2_error is not None
    assert artifact.h1_error is not None
    assert artifact.dof_count is not None
    assert artifact.wall_time_seconds is not None
    assert artifact.mesh_info is not None


def test_validator_strict_tolerances_expected_failure() -> None:
    """Coarse 8x8 P1 mesh should fail strict default tolerances — validates correct behavior."""
    spec = _spec()
    env = FealpyEnvironmentProbeComponent().probe(spec)
    compiler = FealpyCompilerComponent()
    plan = compiler.compile(spec, environment=env)
    executor = FealpyExecutorComponent()
    artifact = executor.execute_plan(plan, environment=env)

    validator = FealpyValidatorComponent()
    report = validator.validate(artifact, plan)

    assert report.passed is False
    assert report.status.value == "numeric_validation_failed"
    assert report.l2_passed is False or report.h1_passed is False


def test_validator_relaxed_tolerances_passes() -> None:
    spec = _spec()
    env = FealpyEnvironmentProbeComponent().probe(spec)
    compiler = FealpyCompilerComponent()
    plan = compiler.compile(spec, environment=env)
    executor = FealpyExecutorComponent()
    artifact = executor.execute_plan(plan, environment=env)

    validator = FealpyValidatorComponent()
    report = validator.validate(artifact, plan, l2_tolerance=1.0, h1_tolerance=10.0)

    assert report.passed is True, f"Relaxed tolerance check failed: {report.messages}"
    assert report.l2_passed is True
    assert report.h1_passed is True
    assert report.status.value == "executed"


def test_full_pipeline_real_fealpy() -> None:
    """End-to-end: Poisson exp0001 with P1 elements — full pipeline with relaxed tolerances."""
    spec = _spec()

    env_component = FealpyEnvironmentProbeComponent()
    env = env_component.probe(spec)
    assert env.available is True

    compiler = FealpyCompilerComponent()
    plan = compiler.compile(spec, environment=env)

    executor = FealpyExecutorComponent()
    artifact = executor.execute_plan(plan, environment=env)
    assert artifact.status == "completed"

    validator = FealpyValidatorComponent()
    report = validator.validate(artifact, plan, l2_tolerance=1.0, h1_tolerance=10.0)
    assert report.passed is True
    assert report.l2_passed is True
    assert report.h1_passed is True

    from metaharness_ext.fealpy.evidence import build_evidence_bundle
    from metaharness_ext.fealpy.policy import FealpyEvidencePolicy

    bundle = build_evidence_bundle(run=artifact, validation=report, environment=env, plan=plan)
    assert bundle.validation_ref is not None

    policy = FealpyEvidencePolicy()
    policy_report = policy.evaluate(bundle)
    assert policy_report.passed is True
    assert policy_report.decision == "allow"
