from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from metaharness.sdk.research import (
    DossierClaim,
    EvidenceBundle,
    EvidenceQuality,
    EvidenceStatus,
    NegativeResultCluster,
    ReproducibilityTier,
    ResearchConclusion,
    ResearchDossier,
    ResearchQuestion,
)


def classify_evidence_quality(evidence: EvidenceBundle) -> EvidenceQuality:
    if evidence.status != EvidenceStatus.PASSED:
        return EvidenceQuality.EXECUTION_FAILURE
    if evidence.supports or evidence.refutes:
        return EvidenceQuality.HIGH
    return EvidenceQuality.INCONCLUSIVE


def reproducibility_tier_for(evidence: EvidenceBundle) -> ReproducibilityTier:
    if evidence.status != EvidenceStatus.PASSED:
        return ReproducibilityTier.UNVERIFIED
    if evidence.confidence_method == "deterministic_metric_threshold":
        return ReproducibilityTier.DETERMINISTIC
    return ReproducibilityTier.SINGLE_RUN


@dataclass(frozen=True)
class NegativeResultAggregator:
    repeat_threshold: int = 2

    def aggregate(self, evidence: list[EvidenceBundle]) -> list[NegativeResultCluster]:
        groups: dict[str, list[EvidenceBundle]] = {}
        for bundle in evidence:
            if not _is_negative_result(bundle):
                continue
            groups.setdefault(_cluster_key(bundle), []).append(bundle)
        return [self._cluster_for(items) for items in groups.values()]

    def is_repeated_dead_end(
        self, evidence: list[EvidenceBundle], candidate: EvidenceBundle
    ) -> bool:
        if not _is_negative_result(candidate):
            return False
        candidate_key = _cluster_key(candidate)
        matching_count = sum(
            1
            for bundle in evidence
            if _is_negative_result(bundle) and _cluster_key(bundle) == candidate_key
        )
        return matching_count >= self.repeat_threshold

    def _cluster_for(self, evidence: list[EvidenceBundle]) -> NegativeResultCluster:
        first = evidence[0]
        evidence_bundle_ids = sorted(bundle.bundle_id for bundle in evidence)
        refuted_hypothesis_ids = sorted(
            {hypothesis_id for bundle in evidence for hypothesis_id in bundle.refutes}
        )
        return NegativeResultCluster(
            cluster_id=f"negative-{_digest(_cluster_key(first))}",
            domain_tags=dict(first.domain_tags),
            metric_schema=_metric_schema(first),
            failure_category=first.failure_category,
            evidence_bundle_ids=evidence_bundle_ids,
            refuted_hypothesis_ids=refuted_hypothesis_ids,
            repeated_dead_end=len(evidence) >= self.repeat_threshold,
        )


def build_research_dossier(
    question: ResearchQuestion,
    evidence: list[EvidenceBundle],
    conclusion: ResearchConclusion,
    *,
    dossier_id: str | None = None,
    aggregator: NegativeResultAggregator | None = None,
) -> ResearchDossier:
    negative_result_aggregator = aggregator or NegativeResultAggregator()
    claims = _claims_for(evidence)
    return ResearchDossier(
        dossier_id=dossier_id or f"dossier-{question.question_id}",
        question_id=question.question_id,
        claims=claims,
        negative_result_clusters=negative_result_aggregator.aggregate(evidence),
        conclusion=conclusion,
    )


def _claims_for(evidence: list[EvidenceBundle]) -> list[DossierClaim]:
    claims: list[DossierClaim] = []
    for bundle in evidence:
        for hypothesis_id in bundle.supports:
            claims.append(_claim_for(bundle, hypothesis_id, supported=True))
        for hypothesis_id in bundle.refutes:
            claims.append(_claim_for(bundle, hypothesis_id, supported=False))
    return claims


def _claim_for(bundle: EvidenceBundle, hypothesis_id: str, *, supported: bool) -> DossierClaim:
    outcome = "supported" if supported else "refuted"
    return DossierClaim(
        claim_id=f"claim-{bundle.bundle_id}-{hypothesis_id}-{outcome}",
        statement=f"Hypothesis {hypothesis_id} was {outcome} by evidence {bundle.bundle_id}.",
        hypothesis_ids=[hypothesis_id],
        evidence_bundle_ids=[bundle.bundle_id],
        confidence=bundle.confidence,
        evidence_quality=classify_evidence_quality(bundle),
        reproducibility_tier=reproducibility_tier_for(bundle),
    )


def _is_negative_result(evidence: EvidenceBundle) -> bool:
    return bool(evidence.refutes) or evidence.status != EvidenceStatus.PASSED


def _cluster_key(evidence: EvidenceBundle) -> str:
    return json.dumps(
        {
            "domain_tags": evidence.domain_tags,
            "failure_category": evidence.failure_category,
            "metric_schema": _metric_schema(evidence),
        },
        sort_keys=True,
    )


def _metric_schema(evidence: EvidenceBundle) -> str | None:
    value: Any = evidence.domain_tags.get("metric_schema")
    return str(value) if value is not None else None


def _digest(value: str) -> str:
    return hashlib.sha1(value.encode()).hexdigest()[:12]
