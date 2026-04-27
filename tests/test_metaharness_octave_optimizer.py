from metaharness_ext.octave.contracts import OctaveStudyAxis, OctaveStudyReport, OctaveStudyTrial
from metaharness_ext.octave.optimizer import OctaveDomainBrainProvider


def test_octave_optimizer_converts_study_trials_to_observations() -> None:
    report = OctaveStudyReport(
        study_id="study-1",
        trials=[
            OctaveStudyTrial(
                trial_id="trial-1",
                parameter_snapshot={"parameters.alpha": 1.0},
                metric_value=0.2,
                passed=True,
            )
        ],
    )

    observations = OctaveDomainBrainProvider().observations_from_study(report)

    assert observations[0].trial_id == "trial-1"
    assert observations[0].parameters == {"parameters.alpha": 1.0}


def test_octave_optimizer_proposes_only_axis_whitelist_paths() -> None:
    provider = OctaveDomainBrainProvider()
    axes = [OctaveStudyAxis(parameter_path="parameters.alpha", values=[1.0, 2.0])]
    observations = provider.observations_from_study(
        OctaveStudyReport(
            study_id="study-1",
            trials=[
                OctaveStudyTrial(
                    trial_id="trial-1",
                    parameter_snapshot={"parameters.alpha": 1.0},
                    metric_value=0.5,
                    passed=True,
                )
            ],
        )
    )

    proposals = provider.propose(axes, observations)

    assert len(proposals) == 1
    payload = proposals[0].domain_payload
    assert payload is not None
    assert payload["parameters"] == {"parameters.alpha": 2.0}
    assert payload["whitelist_paths"] == ["parameters.alpha"]


def test_octave_optimizer_evaluates_against_ready_observations() -> None:
    provider = OctaveDomainBrainProvider()
    observations = provider.observations_from_study(
        OctaveStudyReport(
            study_id="study-1",
            trials=[
                OctaveStudyTrial(
                    trial_id="trial-1",
                    parameter_snapshot={"parameters.alpha": 1.0},
                    metric_value=0.5,
                    passed=True,
                )
            ],
        )
    )
    proposal = provider.propose(
        [OctaveStudyAxis(parameter_path="parameters.alpha", values=[2.0])], observations
    )[0]

    evaluation = provider.evaluate(proposal, observations)

    assert evaluation.score > 0
    assert "typed_whitelist_parameter_proposal" in evaluation.reasons
    assert evaluation.evidence.metrics["ready_observations"] == 1.0
