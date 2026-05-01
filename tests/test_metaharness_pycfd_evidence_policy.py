from __future__ import annotations

from metaharness_ext.pycfd.contracts import (
    PyCFDEnvironmentReport,
    PyCFDEvidenceBundle,
    PyCFDProblemSpec,
    PyCFDRunArtifact,
    PyCFDRunPlan,
    PyCFDValidationReport,
)
from metaharness_ext.pycfd.evidence import build_evidence_bundle
from metaharness_ext.pycfd.policy import PyCFDEvidencePolicy
from metaharness_ext.pycfd.types import PyCFDValidationStatus


class TestEvidenceBundle:
    def test_full_bundle(self):
        env = PyCFDEnvironmentReport(task_id="t1", available=True, status="ready")
        spec = PyCFDProblemSpec(task_id="t1")
        plan = PyCFDRunPlan(
            plan_id="p1",
            task_id="t1",
            run_id="r1",
            spec=spec,
            workspace_dir="/tmp",
            script_source="x",
        )
        artifact = PyCFDRunArtifact(
            artifact_id="a1", run_id="r1", task_id="t1", plan_ref="p1", status="completed"
        )
        validation = PyCFDValidationReport(
            task_id="t1",
            plan_ref="p1",
            artifact_ref="a1",
            passed=True,
            status=PyCFDValidationStatus.EXECUTED,
        )

        bundle = build_evidence_bundle(
            task_id="t1",
            environment=env,
            plan=plan,
            artifact=artifact,
            validation=validation,
        )
        assert bundle.bundle_id.startswith("pycfd-evidence-")
        assert bundle.environment is env
        assert len(bundle.evidence_refs) == 4

    def test_minimal_bundle(self):
        bundle = build_evidence_bundle(task_id="t1")
        assert bundle.task_id == "t1"
        assert bundle.environment is None
        assert len(bundle.warnings) >= 1  # environment not ready

    def test_missing_validation_warns(self):
        env = PyCFDEnvironmentReport(task_id="t1", available=True, status="ready")
        bundle = build_evidence_bundle(task_id="t1", environment=env)
        assert any(w.code == "pycfd_validation_missing" for w in bundle.warnings)


class TestPyCFDEvidencePolicy:
    def test_all_gates_pass(self):
        env = PyCFDEnvironmentReport(task_id="t1", available=True, status="ready")
        validation = PyCFDValidationReport(
            task_id="t1",
            plan_ref="p1",
            artifact_ref="a1",
            passed=True,
            status=PyCFDValidationStatus.EXECUTED,
        )
        bundle = PyCFDEvidenceBundle(
            bundle_id="b1",
            task_id="t1",
            environment=env,
            validation=validation,
            evidence_refs=["pycfd://artifacts/a1"],
        )
        policy = PyCFDEvidencePolicy()
        report = policy.evaluate(bundle)
        assert report.passed
        assert report.decision == "allow"

    def test_environment_unavailable_rejects(self):
        env = PyCFDEnvironmentReport(
            task_id="t1", available=False, status="not_found", blocks_promotion=True
        )
        bundle = PyCFDEvidenceBundle(bundle_id="b1", task_id="t1", environment=env)
        policy = PyCFDEvidencePolicy()
        report = policy.evaluate(bundle)
        assert report.decision == "reject"

    def test_validation_failed_defers(self):
        env = PyCFDEnvironmentReport(task_id="t1", available=True, status="ready")
        validation = PyCFDValidationReport(
            task_id="t1",
            plan_ref="p1",
            artifact_ref="a1",
            passed=False,
            status=PyCFDValidationStatus.RESIDUAL_EXCEEDED,
        )
        bundle = PyCFDEvidenceBundle(
            bundle_id="b1",
            task_id="t1",
            environment=env,
            validation=validation,
            evidence_refs=["pycfd://artifacts/a1"],
        )
        policy = PyCFDEvidencePolicy()
        report = policy.evaluate(bundle)
        assert report.decision == "defer"

    def test_no_evidence_defers(self):
        env = PyCFDEnvironmentReport(task_id="t1", available=True, status="ready")
        validation = PyCFDValidationReport(
            task_id="t1",
            plan_ref="p1",
            artifact_ref="a1",
            passed=True,
            status=PyCFDValidationStatus.EXECUTED,
        )
        bundle = PyCFDEvidenceBundle(
            bundle_id="b1",
            task_id="t1",
            environment=env,
            validation=validation,
            evidence_refs=[],
            evidence_files=[],
        )
        policy = PyCFDEvidencePolicy()
        report = policy.evaluate(bundle)
        assert report.decision == "defer"

    def test_five_gates_always_evaluated(self):
        env = PyCFDEnvironmentReport(task_id="t1", available=True, status="ready")
        validation = PyCFDValidationReport(
            task_id="t1",
            plan_ref="p1",
            artifact_ref="a1",
            passed=True,
            status=PyCFDValidationStatus.EXECUTED,
        )
        bundle = PyCFDEvidenceBundle(
            bundle_id="b1",
            task_id="t1",
            environment=env,
            validation=validation,
            evidence_refs=["ref1"],
        )
        policy = PyCFDEvidencePolicy()
        report = policy.evaluate(bundle)
        assert len(report.gates) == 5
