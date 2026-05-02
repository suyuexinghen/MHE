from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from metaharness.research.decision import decision_from_evidence
from metaharness.research.mappers import summary_to_evidence_bundle
from metaharness.research.store import ResearchStore
from metaharness.sdk.research import (
    Decision,
    EvidenceBundle,
    ExperimentPlan,
    Hypothesis,
    HypothesisStatus,
    ResearchBudget,
    ResearchConclusion,
    ResearchQuestion,
    ResearchQuestionStatus,
)


@dataclass(frozen=True)
class ResearchLoopRun:
    question: ResearchQuestion
    hypotheses: list[Hypothesis]
    evidence: list[EvidenceBundle]
    decisions: list[Decision]
    conclusion: ResearchConclusion
    budget: ResearchBudget


class ResearchOrchestrator:
    """Minimal research-loop wrapper over benchmark summaries."""

    def __init__(self, store: ResearchStore, budget: ResearchBudget | None = None) -> None:
        self.store = store
        self.budget = budget or ResearchBudget()

    def pursue(
        self,
        question: ResearchQuestion,
        *,
        hypotheses: list[Hypothesis],
        plans: list[ExperimentPlan],
        summaries: dict[str, dict[str, Any]],
        artifact_refs: dict[str, str] | None = None,
    ) -> ResearchLoopRun:
        artifact_refs = artifact_refs or {}
        hypotheses_by_id = {hypothesis.hypothesis_id: hypothesis for hypothesis in hypotheses}
        self.store.record_question(question)

        evidence_records: list[EvidenceBundle] = []
        decisions: list[Decision] = []
        budget = self.budget

        for plan in plans:
            if budget.exhausted:
                break
            hypothesis = hypotheses_by_id[plan.hypothesis_id]
            self.store.record_plan(plan)
            summary = summaries[plan.plan_id]
            evidence = summary_to_evidence_bundle(
                summary,
                plan=plan,
                hypothesis=hypothesis,
                artifact_ref=artifact_refs.get(plan.plan_id, "summary.json"),
            )
            decision = decision_from_evidence(evidence, hypothesis)
            hypothesis.status = _status_from_evidence(evidence, hypothesis)

            self.store.record_evidence(evidence)
            self.store.record_decision(decision)
            evidence_records.append(evidence)
            decisions.append(decision)
            budget = budget.consume_experiment()

        for hypothesis in hypotheses:
            self.store.record_hypothesis(hypothesis)

        conclusion = _conclusion_for(question, hypotheses, decisions, budget, len(plans))
        self.budget = budget
        return ResearchLoopRun(
            question=question,
            hypotheses=hypotheses,
            evidence=evidence_records,
            decisions=decisions,
            conclusion=conclusion,
            budget=budget,
        )


def _status_from_evidence(evidence: EvidenceBundle, hypothesis: Hypothesis) -> HypothesisStatus:
    if hypothesis.hypothesis_id in evidence.supports:
        return HypothesisStatus.SUPPORTED
    if hypothesis.hypothesis_id in evidence.refutes:
        return HypothesisStatus.REFUTED
    return hypothesis.status


def _conclusion_for(
    question: ResearchQuestion,
    hypotheses: list[Hypothesis],
    decisions: list[Decision],
    budget: ResearchBudget,
    plan_count: int,
) -> ResearchConclusion:
    supported = [
        hypothesis.hypothesis_id
        for hypothesis in hypotheses
        if hypothesis.status == HypothesisStatus.SUPPORTED
    ]
    refuted = [
        hypothesis.hypothesis_id
        for hypothesis in hypotheses
        if hypothesis.status == HypothesisStatus.REFUTED
    ]
    if budget.exhausted and len(decisions) < plan_count:
        status = ResearchQuestionStatus.STALE
    elif supported or refuted:
        status = ResearchQuestionStatus.ANSWERED
    else:
        status = question.status
    return ResearchConclusion(
        question_id=question.question_id,
        decision_ids=[decision.decision_id for decision in decisions],
        supported_hypotheses=supported,
        refuted_hypotheses=refuted,
        status=status,
    )
