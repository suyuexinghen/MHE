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
    artifact = BoutPPRunArtifact(artifact_id="a1", run_id="r1", task_id="t1", plan_ref="p1", status="completed", missing_artifacts=["settings"])
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
    spec = BoutPPValidationSpec(required_variables=["T"], metric_thresholds={"runtime_seconds": 10.0})
    report = BoutPPValidatorComponent().validate(artifact, plan_ref="plan", postprocess=postprocess, validation_spec=spec)
    assert report.passed is True
    assert report.status.value == "executed"


def test_policy_rejects_missing_environment():
    bundle = BoutPPEvidenceBundle(bundle_id="b1", task_id="t1", environment=BoutPPEnvironmentReport(task_id="env", available=False))
    policy = BoutPPEvidencePolicy().evaluate(bundle)
    assert policy.decision == "reject"
