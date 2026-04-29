from __future__ import annotations

from metaharness_ext.fealpy.contracts import (
    FealpyEnvironmentReport,
    FealpyEvidenceBundle,
    FealpyProblemSpec,
    FealpyRunArtifact,
    FealpyRunPlan,
    FealpyValidationReport,
)
from metaharness_ext.fealpy.evidence import build_evidence_bundle
from metaharness_ext.fealpy.policy import FealpyEvidencePolicy
from metaharness_ext.fealpy.types import FealpyValidationStatus


def _artifact(**overrides) -> FealpyRunArtifact:
    defaults = {
        "artifact_id": "artifact-evid-1",
        "run_id": "run-evid-1",
        "task_id": "evid-test",
        "plan_ref": "fealpy-evid-test-abc",
        "status": "completed",
        "l2_error": 1e-8,
        "h1_error": 1e-6,
        "summary_metrics": {"l2_error": 1e-8, "h1_error": 1e-6},
        "evidence_refs": ["fealpy://run/evid-test/run-evid-1"],
    }
    defaults.update(overrides)
    return FealpyRunArtifact(**defaults)


def _validation(**overrides) -> FealpyValidationReport:
    defaults = {
        "task_id": "evid-test",
        "plan_ref": "fealpy-evid-test-abc",
        "artifact_ref": "artifact-evid-1",
        "passed": True,
        "status": FealpyValidationStatus.EXECUTED,
        "l2_passed": True,
        "h1_passed": True,
        "evidence_refs": ["fealpy://validation/evid-test/artifact-evid-1"],
    }
    defaults.update(overrides)
    return FealpyValidationReport(**defaults)


def _environment(**overrides) -> FealpyEnvironmentReport:
    defaults = {
        "task_id": "evid-test",
        "available": True,
        "status": "available",
        "fealpy_version": "5.0.0",
        "available_backends": ["numpy"],
        "evidence_refs": ["fealpy://env/evid-test"],
    }
    defaults.update(overrides)
    return FealpyEnvironmentReport(**defaults)


def _plan() -> FealpyRunPlan:

    spec = FealpyProblemSpec(task_id="evid-test", pde_family="poisson")
    return FealpyRunPlan(
        plan_id="fealpy-evid-test-abc",
        task_id="evid-test",
        run_id="run-evid-1",
        spec=spec,
        workspace_dir="/tmp/.runs/fealpy/evid-test/run-evid-1",
        script_source="print('hello')",
        evidence_refs=["fealpy://plan/evid-test"],
    )


# ── Evidence bundle tests ──────────────────────────────────────────────


def test_build_evidence_bundle_full() -> None:
    bundle = build_evidence_bundle(
        run=_artifact(),
        validation=_validation(),
        environment=_environment(),
        plan=_plan(),
    )
    assert bundle.bundle_id.startswith("fealpy-evid-test-")
    assert bundle.task_id == "evid-test"
    assert bundle.validation_ref is not None
    assert bundle.environment is not None
    assert bundle.plan is not None
    assert bundle.artifact is not None
    assert bundle.validation is not None
    assert len(bundle.evidence_refs) > 0
    assert bundle.provenance["task_id"] == "evid-test"


def test_build_evidence_bundle_minimal() -> None:
    bundle = build_evidence_bundle(run=_artifact())
    assert bundle.bundle_id.startswith("fealpy-")
    assert bundle.validation is None
    assert bundle.environment is None


def test_build_evidence_bundle_missing_validation_warning() -> None:
    bundle = build_evidence_bundle(run=_artifact())
    assert any(w.code == "validation_missing" for w in bundle.warnings)


def test_build_evidence_bundle_environment_prerequisites_warning() -> None:
    env = _environment(
        available=True,
        missing_prerequisites=["pytorch"],
    )
    bundle = build_evidence_bundle(run=_artifact(), environment=env)
    assert any(w.code == "environment_prerequisite_error" for w in bundle.warnings)


def test_build_evidence_bundle_dedup_evidence_refs() -> None:
    plan = _plan()
    bundle = build_evidence_bundle(
        run=_artifact(),
        validation=_validation(),
        environment=_environment(),
        plan=plan,
    )
    # evidence_refs should be deduplicated
    assert len(bundle.evidence_refs) == len(set(bundle.evidence_refs))


# ── Policy tests ───────────────────────────────────────────────────────


def test_policy_environment_reject() -> None:
    env = _environment(available=False, status="prerequisite_missing", blocks_promotion=True)
    bundle = build_evidence_bundle(
        run=_artifact(l2_error=None, h1_error=None, status="unavailable"),
        environment=env,
    )
    policy = FealpyEvidencePolicy()
    report = policy.evaluate(bundle)

    assert report.passed is False
    assert report.decision == "reject"
    assert any(g.gate == "fealpy_environment_readiness" for g in report.gates)


def test_policy_validation_missing_defers() -> None:
    bundle = build_evidence_bundle(run=_artifact())
    policy = FealpyEvidencePolicy()
    report = policy.evaluate(bundle)

    assert report.passed is False
    assert report.decision == "defer"
    assert any(g.gate == "fealpy_validation_presence" for g in report.gates)


def test_policy_validation_failed_rejects() -> None:
    bundle = build_evidence_bundle(
        run=_artifact(),
        validation=_validation(
            passed=False,
            status=FealpyValidationStatus.NUMERIC_VALIDATION_FAILED,
            l2_passed=False,
            h1_passed=False,
        ),
    )
    # We need blocks_promotion to be True for REJECT
    from metaharness.core.models import ValidationIssue

    val_with_blocker = _validation(
        passed=False,
        status=FealpyValidationStatus.NUMERIC_VALIDATION_FAILED,
        l2_passed=False,
        h1_passed=False,
        issues=[
            ValidationIssue(
                code="FEALPY_L2_TOLERANCE",
                message="L2 error exceeds tolerance",
                subject="l2_error",
                blocks_promotion=True,
            )
        ],
    )
    bundle = build_evidence_bundle(run=_artifact(), validation=val_with_blocker)
    policy = FealpyEvidencePolicy()
    report = policy.evaluate(bundle)

    assert report.decision == "reject"
    assert any(g.gate == "fealpy_validation_status" for g in report.gates)


def test_policy_no_evidence_refs_defers() -> None:
    artifact = _artifact(evidence_refs=[])
    validation = _validation(evidence_refs=[])
    bundle = build_evidence_bundle(run=artifact, validation=validation)
    policy = FealpyEvidencePolicy()
    report = policy.evaluate(bundle)

    # The bundle still generates some evidence_refs from run/artifact
    # So test with truly empty refs by constructing bundle directly
    empty_bundle = FealpyEvidenceBundle(
        bundle_id="empty",
        task_id="test",
        artifact=_artifact(evidence_refs=[]),
        validation=_validation(evidence_refs=[]),
        evidence_refs=[],
    )
    report = policy.evaluate(empty_bundle)
    assert any(g.gate == "fealpy_evidence_files" for g in report.gates)


def test_policy_all_gates_pass() -> None:
    bundle = build_evidence_bundle(
        run=_artifact(),
        validation=_validation(),
        environment=_environment(),
        plan=_plan(),
    )
    policy = FealpyEvidencePolicy()
    report = policy.evaluate(bundle)

    assert report.passed is True
    assert report.decision == "allow"
    assert any(g.gate == "fealpy_evidence_ready" for g in report.gates)


def test_policy_report_includes_evidence() -> None:
    bundle = build_evidence_bundle(
        run=_artifact(),
        validation=_validation(),
        environment=_environment(),
    )
    policy = FealpyEvidencePolicy()
    report = policy.evaluate(bundle)

    assert "task_id" in report.evidence
    assert report.evidence["task_id"] == "evid-test"
    assert "evidence_ref_count" in report.evidence
