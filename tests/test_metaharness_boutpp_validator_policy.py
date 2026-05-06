from __future__ import annotations

from metaharness_ext.boutpp.contracts import (
    BoutPPEnvironmentReport,
    BoutPPEvidenceBundle,
    BoutPPPostprocessReport,
    BoutPPRunArtifact,
    BoutPPValidationSpec,
)
from metaharness_ext.boutpp.policy import BoutPPEvidencePolicy
from metaharness_ext.boutpp.validator import BoutPPValidatorComponent


def test_validator_artifact_missing():
    artifact = BoutPPRunArtifact(
        artifact_id="a1",
        run_id="r1",
        task_id="t1",
        plan_ref="p1",
        status="completed",
        missing_artifacts=["settings"],
    )
    report = BoutPPValidatorComponent().validate(artifact, plan_ref="p1")
    assert report.passed is False
    assert report.status.value == "artifact_missing"


def test_validator_metric_threshold_and_required_variables():
    artifact = BoutPPRunArtifact(
        artifact_id="a1",
        run_id="r1",
        task_id="t1",
        plan_ref="p1",
        status="completed",
        summary_metrics={"runtime_seconds": 5.0},
    )
    postprocess = BoutPPPostprocessReport(
        report_id="p1",
        task_id="t1",
        artifact_ref="a1",
        status="completed",
        variable_names=["T"],
        summary_metrics={"runtime_seconds": 5.0},
    )
    spec = BoutPPValidationSpec(
        required_variables=["T"], metric_thresholds={"runtime_seconds": 10.0}
    )
    report = BoutPPValidatorComponent().validate(
        artifact, plan_ref="plan", postprocess=postprocess, validation_spec=spec
    )
    assert report.passed is True
    assert report.status.value == "executed"


def test_validator_domain_requirements_are_optional_and_blocking():
    artifact = BoutPPRunArtifact(
        artifact_id="a1",
        run_id="r1",
        task_id="t1",
        plan_ref="p1",
        status="completed",
        return_code=0,
    )
    postprocess = BoutPPPostprocessReport(
        report_id="p1",
        task_id="t1",
        artifact_ref="a1",
        status="completed",
        variable_names=["T"],
        dimension_sizes={"t": 2, "y": 100},
        variable_dimensions={"T": ["t", "y"]},
    )
    passing_spec = BoutPPValidationSpec(
        required_dimensions={"y": 100},
        required_variable_dimensions={"T": ["t", "y"]},
    )
    failing_spec = BoutPPValidationSpec(
        required_dimensions={"y": 99},
        required_variable_dimensions={"T": ["t", "x"]},
    )

    passing_report = BoutPPValidatorComponent().validate(
        artifact,
        plan_ref="plan",
        postprocess=postprocess,
        validation_spec=passing_spec,
    )
    failing_report = BoutPPValidatorComponent().validate(
        artifact,
        plan_ref="plan",
        postprocess=postprocess,
        validation_spec=failing_spec,
    )

    assert passing_report.passed is True
    assert failing_report.passed is False
    assert failing_report.status.value == "domain_validation_failed"
    assert len(failing_report.issues) == 2


def test_validator_can_opt_out_of_successful_return_code_requirement():
    artifact = BoutPPRunArtifact(
        artifact_id="a1",
        run_id="r1",
        task_id="t1",
        plan_ref="p1",
        status="completed",
        return_code=1,
    )
    spec = BoutPPValidationSpec(require_successful_return_code=False)

    report = BoutPPValidatorComponent().validate(artifact, plan_ref="plan", validation_spec=spec)

    assert report.passed is True


def test_policy_rejects_missing_environment():
    bundle = BoutPPEvidenceBundle(
        bundle_id="b1",
        task_id="t1",
        environment=BoutPPEnvironmentReport(task_id="env", available=False),
    )
    policy = BoutPPEvidencePolicy().evaluate(bundle)
    assert policy.decision == "reject"
