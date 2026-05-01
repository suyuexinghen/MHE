from __future__ import annotations

import pytest
from pydantic import ValidationError

from metaharness.research.dossier import (
    NegativeResultAggregator,
    build_research_dossier,
    classify_evidence_quality,
    reproducibility_tier_for,
)
from metaharness.research.store import ResearchStore
from metaharness.sdk.research import (
    DossierClaim,
    EvidenceBundle,
    EvidenceQuality,
    EvidenceStatus,
    ReproducibilityTier,
    ResearchConclusion,
    ResearchQuestion,
    ResearchQuestionStatus,
)


def _question() -> ResearchQuestion:
    return ResearchQuestion(question_id="rq", statement="Can the metric be improved?")


def _conclusion() -> ResearchConclusion:
    return ResearchConclusion(
        question_id="rq",
        decision_ids=["dec-1"],
        supported_hypotheses=["h-supported"],
        refuted_hypotheses=["h-refuted"],
        status=ResearchQuestionStatus.ANSWERED,
    )


def _evidence(
    bundle_id: str,
    *,
    status: EvidenceStatus = EvidenceStatus.PASSED,
    supports: list[str] | None = None,
    refutes: list[str] | None = None,
    failure_category: str | None = None,
    metric_schema: str = "fealpy.poisson.v1",
) -> EvidenceBundle:
    return EvidenceBundle(
        bundle_id=bundle_id,
        experiment_plan_id="plan-1",
        artifact_refs=[f".runs/{bundle_id}/summary.json"],
        metrics={"l2_error": 0.02},
        status=status,
        failure_category=failure_category,
        confidence=1.0 if status == EvidenceStatus.PASSED else 0.0,
        confidence_method="deterministic_metric_threshold"
        if status == EvidenceStatus.PASSED
        else "execution_failed",
        domain_tags={"suite": "fealpy-pde", "case_id": "poisson-2d-numpy", "metric_schema": metric_schema},
        supports=supports or [],
        refutes=refutes or [],
    )


def test_dossier_claim_requires_evidence_or_baseline_trace() -> None:
    with pytest.raises(ValidationError):
        DossierClaim(
            claim_id="claim-untraceable",
            statement="Untraceable claim",
            confidence=1.0,
            evidence_quality=EvidenceQuality.HIGH,
            reproducibility_tier=ReproducibilityTier.DETERMINISTIC,
        )


def test_negative_result_aggregator_groups_dead_ends_by_domain_and_failure() -> None:
    first = _evidence("ev-refuted-1", refutes=["h-refuted"])
    second = _evidence("ev-refuted-2", refutes=["h-refuted-again"])
    execution_failure = _evidence(
        "ev-failed",
        status=EvidenceStatus.FAILED,
        failure_category="runner_error",
        metric_schema="fealpy.poisson.v1",
    )

    clusters = NegativeResultAggregator().aggregate([first, second, execution_failure])

    refuted_cluster = next(cluster for cluster in clusters if cluster.failure_category is None)
    failed_cluster = next(cluster for cluster in clusters if cluster.failure_category == "runner_error")
    assert refuted_cluster.metric_schema == "fealpy.poisson.v1"
    assert refuted_cluster.evidence_bundle_ids == ["ev-refuted-1", "ev-refuted-2"]
    assert refuted_cluster.refuted_hypothesis_ids == ["h-refuted", "h-refuted-again"]
    assert refuted_cluster.repeated_dead_end is True
    assert failed_cluster.evidence_bundle_ids == ["ev-failed"]
    assert failed_cluster.repeated_dead_end is False


def test_repeated_dead_end_detection_matches_existing_cluster() -> None:
    aggregator = NegativeResultAggregator(repeat_threshold=2)
    history = [_evidence("ev-refuted-1", refutes=["h-a"]), _evidence("ev-refuted-2", refutes=["h-b"])]
    candidate = _evidence("ev-refuted-3", refutes=["h-c"])

    assert aggregator.is_repeated_dead_end(history, candidate) is True
    assert aggregator.is_repeated_dead_end(history, _evidence("ev-supported", supports=["h-ok"])) is False


def test_research_dossier_builds_traceable_claims_and_negative_clusters() -> None:
    supported = _evidence("ev-supported", supports=["h-supported"])
    refuted = _evidence("ev-refuted", refutes=["h-refuted"])

    dossier = build_research_dossier(_question(), [supported, refuted], _conclusion())

    assert dossier.dossier_id == "dossier-rq"
    assert dossier.question_id == "rq"
    assert {claim.evidence_bundle_ids[0] for claim in dossier.claims} == {"ev-supported", "ev-refuted"}
    assert {claim.hypothesis_ids[0] for claim in dossier.claims} == {"h-supported", "h-refuted"}
    assert dossier.negative_result_clusters[0].evidence_bundle_ids == ["ev-refuted"]


def test_evidence_quality_and_reproducibility_policy_are_deterministic() -> None:
    supported = _evidence("ev-supported", supports=["h-supported"])
    inconclusive = _evidence("ev-inconclusive")
    failed = _evidence("ev-failed", status=EvidenceStatus.FAILED, failure_category="runner_error")

    assert classify_evidence_quality(supported) == EvidenceQuality.HIGH
    assert classify_evidence_quality(inconclusive) == EvidenceQuality.INCONCLUSIVE
    assert classify_evidence_quality(failed) == EvidenceQuality.EXECUTION_FAILURE
    assert reproducibility_tier_for(supported) == ReproducibilityTier.DETERMINISTIC
    assert reproducibility_tier_for(failed) == ReproducibilityTier.UNVERIFIED


def test_research_store_records_dossiers(tmp_path) -> None:
    dossier = build_research_dossier(
        _question(),
        [_evidence("ev-supported", supports=["h-supported"])],
        _conclusion(),
    )
    store = ResearchStore(tmp_path)

    store.record_dossier(dossier)

    assert store.dossiers_for("rq") == [dossier]
