from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

from metaharness.sdk.research import (
    Decision,
    EvidenceBundle,
    ExperimentPlan,
    Hypothesis,
    ResearchQuestion,
)
from metaharness.sdk.review import EvidenceReview

_RECORD_MODELS: dict[str, type[BaseModel]] = {
    "question": ResearchQuestion,
    "hypothesis": Hypothesis,
    "plan": ExperimentPlan,
    "evidence": EvidenceBundle,
    "decision": Decision,
    "review": EvidenceReview,
}

T = TypeVar("T", bound=BaseModel)


class ResearchStore:
    """Lightweight JSONL store for MVP research traces."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.trace_path = root / "research_trace.jsonl"

    def record_question(self, question: ResearchQuestion) -> None:
        self._append("question", question)

    def record_hypothesis(self, hypothesis: Hypothesis) -> None:
        self._append("hypothesis", hypothesis)

    def record_plan(self, plan: ExperimentPlan) -> None:
        self._append("plan", plan)

    def record_evidence(self, evidence: EvidenceBundle) -> None:
        self._append("evidence", evidence)

    def record_decision(self, decision: Decision) -> None:
        self._append("decision", decision)

    def record_review(self, review: EvidenceReview) -> None:
        self._append("review", review)

    def list_hypotheses(self, question_id: str) -> list[Hypothesis]:
        return [
            record
            for record in self._records("hypothesis", Hypothesis)
            if record.question_id == question_id
        ]

    def evidence_for(self, hypothesis_id: str) -> list[EvidenceBundle]:
        return [
            record
            for record in self._records("evidence", EvidenceBundle)
            if hypothesis_id in record.supports or hypothesis_id in record.refutes
        ]

    def decision_history(self, question_id: str) -> list[Decision]:
        hypothesis_ids = {hypothesis.hypothesis_id for hypothesis in self.list_hypotheses(question_id)}
        return [
            record
            for record in self._records("decision", Decision)
            if record.hypothesis_id in hypothesis_ids
        ]

    def reviews_for(self, evidence_bundle_id: str) -> list[EvidenceReview]:
        return [
            record
            for record in self._records("review", EvidenceReview)
            if record.evidence_bundle_id == evidence_bundle_id
        ]

    def _append(self, record_type: str, payload: BaseModel) -> None:
        self.trace_path.parent.mkdir(parents=True, exist_ok=True)
        record = {"type": record_type, "payload": payload.model_dump(mode="json")}
        with self.trace_path.open("a") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")

    def _records(self, record_type: str, model: type[T]) -> list[T]:
        if not self.trace_path.exists():
            return []
        records: list[T] = []
        for line in self.trace_path.read_text().splitlines():
            if not line.strip():
                continue
            raw: dict[str, Any] = json.loads(line)
            if raw.get("type") == record_type:
                records.append(model.model_validate(raw["payload"]))
        return records
