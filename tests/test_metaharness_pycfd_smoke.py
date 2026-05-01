"""Smoke tests for PyCFD extension — gated behind MHE_RUN_REAL_PYCFD=1.

These tests require a working PyCFD installation at PYCFD_SRC_PATH.
Run with: MHE_RUN_REAL_PYCFD=1 pytest tests/test_metaharness_pycfd_smoke.py -v
"""

from __future__ import annotations

import os

import pytest


@pytest.fixture
def pycfd_src_path():
    path = os.environ.get("PYCFD_SRC_PATH", "")
    if not path or not os.path.isdir(path):
        pytest.skip("PYCFD_SRC_PATH not set or not a directory")
    return path


@pytest.fixture
def require_real_pycfd():
    if os.environ.get("MHE_RUN_REAL_PYCFD") != "1":
        pytest.skip("MHE_RUN_REAL_PYCFD=1 not set")


class TestPyCFDSmoke:
    @pytest.mark.pycfd
    def test_environment_probe_real(self, pycfd_src_path, require_real_pycfd):
        from metaharness_ext.pycfd.environment import PyCFDEnvironmentProbeComponent

        probe = PyCFDEnvironmentProbeComponent(pycfd_src_path=pycfd_src_path)
        report = probe.probe(task_id="smoke-env")
        assert report.available
        assert report.pycfd_src_path

    @pytest.mark.pycfd
    def test_compiler_generates_runnable_script(self, pycfd_src_path, require_real_pycfd):
        from metaharness_ext.pycfd.compiler import PyCFDCompilerComponent
        from metaharness_ext.pycfd.contracts import PyCFDProblemSpec

        compiler = PyCFDCompilerComponent(pycfd_src_path=pycfd_src_path)
        spec = PyCFDProblemSpec(task_id="smoke-compile", case_type="vortex", t_final=0.1, dt=0.05)
        plan = compiler.compile(spec, run_id="smoke-r1", workspace_dir="/tmp/pycfd-smoke")
        assert plan.plan_id
        assert "run_pycfd_case" in plan.script_source

    @pytest.mark.pycfd
    def test_full_pipeline_vortex(self, pycfd_src_path, require_real_pycfd):
        from metaharness_ext.pycfd.compiler import PyCFDCompilerComponent
        from metaharness_ext.pycfd.contracts import PyCFDProblemSpec
        from metaharness_ext.pycfd.environment import PyCFDEnvironmentProbeComponent
        from metaharness_ext.pycfd.evidence import build_evidence_bundle
        from metaharness_ext.pycfd.executor import PyCFDExecutorComponent
        from metaharness_ext.pycfd.policy import PyCFDEvidencePolicy
        from metaharness_ext.pycfd.validator import PyCFDValidatorComponent

        env = PyCFDEnvironmentProbeComponent(pycfd_src_path=pycfd_src_path)
        env_report = env.probe(task_id="smoke-pipeline")
        assert env_report.available, f"PyCFD not available: {env_report.missing_prerequisites}"

        compiler = PyCFDCompilerComponent(pycfd_src_path=pycfd_src_path)
        spec = PyCFDProblemSpec(
            task_id="smoke-pipeline", case_type="vortex", t_final=0.05, dt=0.05, timeout_seconds=120
        )
        plan = compiler.compile(spec, run_id="smoke-full", workspace_dir="/tmp/pycfd-smoke")

        executor = PyCFDExecutorComponent(workspace_root="/tmp/pycfd-smoke")
        artifact = executor.execute(plan)
        assert artifact.status == "completed", f"Execution failed: {artifact.error_message}"

        validator = PyCFDValidatorComponent(residual_tolerance=1.0)  # loose for smoke
        validation = validator.validate(artifact, plan_ref=plan.plan_id)

        evidence = build_evidence_bundle(
            task_id="smoke-pipeline",
            environment=env_report,
            plan=plan,
            artifact=artifact,
            validation=validation,
        )

        policy = PyCFDEvidencePolicy()
        policy_report = policy.evaluate(evidence)
        assert policy_report.decision in ("allow", "defer")
