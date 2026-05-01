from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from metaharness.core.models import ScoredEvidence
from metaharness.sdk.research import (
    EvidenceBundle,
    EvidenceStatus,
    ExperimentPlan,
    Hypothesis,
    ValidationStrategy,
)


class RunPlanProjection(BaseModel):
    """Protocol-compatible view of an MVP experiment plan."""

    plan_id: str
    experiment_ref: str
    target_backend: str
    execution_params: dict[str, Any] = Field(default_factory=dict)


def summary_to_evidence_bundle(
    summary: dict[str, Any],
    *,
    plan: ExperimentPlan,
    hypothesis: Hypothesis,
    artifact_ref: str,
) -> EvidenceBundle:
    status = _evidence_status(summary.get("status"))
    metrics = _numeric_metrics(summary.get("metrics", {}))
    supports: list[str] = []
    refutes: list[str] = []
    confidence = 1.0 if status == EvidenceStatus.PASSED else 0.0
    confidence_method = "deterministic_metric_threshold" if status == EvidenceStatus.PASSED else "execution_failed"

    if status == EvidenceStatus.PASSED:
        satisfied = _prediction_satisfied(metrics, hypothesis.prediction)
        if satisfied is True:
            supports.append(hypothesis.hypothesis_id)
        elif satisfied is False:
            refutes.append(hypothesis.hypothesis_id)
            confidence_method = "deterministic_metric_threshold"

    suite = str(summary.get("suite") or plan.suite)
    case_id = str(summary.get("case_id") or plan.case_id)
    lane = summary.get("lane") or plan.lane

    return EvidenceBundle(
        bundle_id=f"ev-{plan.plan_id}",
        experiment_plan_id=plan.plan_id,
        artifact_refs=[artifact_ref],
        metrics=metrics,
        status=status,
        failure_category=summary.get("failure_category"),
        confidence=confidence,
        confidence_method=confidence_method,
        validation_strategy=ValidationStrategy.GROUND_TRUTH,
        domain_tags={
            "suite": suite,
            "case_id": case_id,
            "lane": lane,
            **plan.controls,
            **plan.variables,
        },
        supports=supports,
        refutes=refutes,
    )


def evidence_to_scored_evidence(evidence: EvidenceBundle) -> ScoredEvidence:
    return ScoredEvidence(
        score=evidence.confidence,
        metrics=evidence.metrics,
        evidence_refs=evidence.artifact_refs,
        reasons=[evidence.confidence_method],
        attributes={
            "bundle_id": evidence.bundle_id,
            "experiment_plan_id": evidence.experiment_plan_id,
            "status": evidence.status.value,
            "failure_category": evidence.failure_category,
            "validation_strategy": evidence.validation_strategy.value,
            "domain_tags": evidence.domain_tags,
            "supports": evidence.supports,
            "refutes": evidence.refutes,
        },
    )


def experiment_plan_to_run_plan_projection(plan: ExperimentPlan) -> RunPlanProjection:
    target_backend = str(plan.controls.get("backend") or plan.suite)
    return RunPlanProjection(
        plan_id=plan.plan_id,
        experiment_ref=plan.hypothesis_id,
        target_backend=target_backend,
        execution_params={
            "suite": plan.suite,
            "case_id": plan.case_id,
            "lane": plan.lane,
            "controls": plan.controls,
            "variables": plan.variables,
            "expected_outcome": plan.expected_outcome,
        },
    )


def _evidence_status(raw_status: Any) -> EvidenceStatus:
    if raw_status in {"passed", "completed"}:
        return EvidenceStatus.PASSED
    if raw_status == "skipped":
        return EvidenceStatus.SKIPPED
    return EvidenceStatus.FAILED


def _numeric_metrics(raw_metrics: Any) -> dict[str, float]:
    if not isinstance(raw_metrics, dict):
        return {}
    metrics: dict[str, float] = {}
    for key, value in raw_metrics.items():
        if isinstance(value, bool):
            continue
        try:
            metrics[str(key)] = float(value)
        except (TypeError, ValueError):
            continue
    return metrics


def _prediction_satisfied(metrics: dict[str, float], prediction: dict[str, dict[str, Any]]) -> bool | None:
    verdicts: list[bool] = []
    for metric_name, constraint in prediction.items():
        if metric_name not in metrics:
            return None
        relation = constraint.get("relation")
        target = constraint.get("value")
        if not isinstance(target, int | float):
            return None
        verdicts.append(_compare(metrics[metric_name], relation, float(target)))
    if not verdicts:
        return None
    return all(verdicts)


def _compare(actual: float, relation: Any, target: float) -> bool:
    match relation:
        case "lt":
            return actual < target
        case "le":
            return actual <= target
        case "gt":
            return actual > target
        case "ge":
            return actual >= target
        case "eq":
            return actual == target
        case "approx":
            return abs(actual - target) <= max(abs(target) * 1e-9, 1e-12)
        case _:
            return False
