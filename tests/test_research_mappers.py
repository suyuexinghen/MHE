from __future__ import annotations

from metaharness.research.mappers import (
    evidence_to_scored_evidence,
    experiment_plan_to_run_plan_projection,
    summary_to_evidence_bundle,
)
from metaharness.sdk.research import EvidenceStatus, ExperimentPlan, Hypothesis


def _hypothesis(threshold: float = 0.01) -> Hypothesis:
    return Hypothesis(
        hypothesis_id="h-fealpy-poisson-p1-16x16",
        question_id="rq-fealpy-poisson-l2-threshold",
        statement="P1 Lagrange elements produce L2 error below threshold.",
        prediction={"l2_error": {"relation": "lt", "value": threshold}},
    )


def _plan() -> ExperimentPlan:
    return ExperimentPlan(
        plan_id="plan-fealpy-poisson-extension",
        hypothesis_id="h-fealpy-poisson-p1-16x16",
        suite="fealpy-pde",
        case_id="poisson-2d-numpy",
        lane="extension",
        controls={"backend": "numpy", "meshtype": "tri"},
        variables={"nx": 16, "ny": 16, "fe_degree": 1},
    )


def test_summary_to_evidence_supports_satisfied_hypothesis() -> None:
    evidence = summary_to_evidence_bundle(
        {
            "suite": "fealpy-pde",
            "case_id": "poisson-2d-numpy",
            "lane": "extension",
            "status": "passed",
            "metrics": {"l2_error": 0.0024865245884339074, "dof": 289, "status": "completed"},
            "failure_category": None,
        },
        plan=_plan(),
        hypothesis=_hypothesis(),
        artifact_ref="summary.json",
    )

    assert evidence.status == EvidenceStatus.PASSED
    assert evidence.metrics == {"l2_error": 0.0024865245884339074, "dof": 289.0}
    assert evidence.supports == ["h-fealpy-poisson-p1-16x16"]
    assert evidence.refutes == []
    assert evidence.domain_tags["backend"] == "numpy"
    assert evidence.domain_tags["nx"] == 16


def test_summary_to_evidence_refutes_unsatisfied_hypothesis() -> None:
    evidence = summary_to_evidence_bundle(
        {"status": "passed", "metrics": {"l2_error": 0.02}, "failure_category": None},
        plan=_plan(),
        hypothesis=_hypothesis(),
        artifact_ref="summary.json",
    )

    assert evidence.supports == []
    assert evidence.refutes == ["h-fealpy-poisson-p1-16x16"]
    assert evidence.confidence == 1.0


def test_failed_summary_records_execution_failure_without_refuting_hypothesis() -> None:
    evidence = summary_to_evidence_bundle(
        {"status": "failed", "metrics": {}, "failure_category": "solver_failure"},
        plan=_plan(),
        hypothesis=_hypothesis(),
        artifact_ref="summary.json",
    )

    assert evidence.status == EvidenceStatus.FAILED
    assert evidence.failure_category == "solver_failure"
    assert evidence.confidence == 0.0
    assert evidence.supports == []
    assert evidence.refutes == []


def test_evidence_to_scored_evidence_preserves_metrics_and_attributes() -> None:
    evidence = summary_to_evidence_bundle(
        {"status": "passed", "metrics": {"l2_error": 0.002}, "failure_category": None},
        plan=_plan(),
        hypothesis=_hypothesis(),
        artifact_ref="summary.json",
    )

    scored = evidence_to_scored_evidence(evidence)

    assert scored.score == 1.0
    assert scored.metrics == {"l2_error": 0.002}
    assert scored.evidence_refs == ["summary.json"]
    assert scored.attributes["supports"] == ["h-fealpy-poisson-p1-16x16"]
    assert scored.attributes["domain_tags"]["case_id"] == "poisson-2d-numpy"


def test_experiment_plan_to_run_plan_projection() -> None:
    projected = experiment_plan_to_run_plan_projection(_plan())

    assert projected.plan_id == "plan-fealpy-poisson-extension"
    assert projected.experiment_ref == "h-fealpy-poisson-p1-16x16"
    assert projected.target_backend == "numpy"
    assert projected.execution_params["suite"] == "fealpy-pde"
    assert projected.execution_params["case_id"] == "poisson-2d-numpy"
