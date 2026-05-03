from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, computed_field, field_validator

BenchmarkSuite = Literal[
    "octave-native",
    "nektar-pde",
    "qcompute-abacus",
    "fealpy-pde",
    "pycfd-pde",
    "boutpp-usage",
]
BenchmarkLane = Literal["extension", "direct", "agent"]
LaneStatus = Literal["passed", "failed", "skipped", "schema_failed"]


class MetricReference(BaseModel):
    value: float | list[float] | None = None
    tolerance: float = 0.0

    @field_validator("tolerance")
    @classmethod
    def validate_tolerance(cls, value: float) -> float:
        if value < 0:
            raise ValueError("metric tolerance must be non-negative")
        return value

    def diff(self, actual: float | list[float] | None) -> float | None:
        if actual is None or self.value is None:
            return None
        if isinstance(actual, int | float) and isinstance(self.value, int | float):
            return abs(float(actual) - float(self.value))
        if isinstance(actual, list) and isinstance(self.value, list):
            if len(actual) != len(self.value):
                return None
            return max(abs(float(left) - float(right)) for left, right in zip(actual, self.value))
        return None

    def passed(self, actual: float | list[float] | None) -> bool | None:
        diff = self.diff(actual)
        if diff is None:
            return None
        return diff <= self.tolerance


class BenchmarkCaseSpec(BaseModel):
    case_id: str
    suite: BenchmarkSuite
    task_family: str
    description: str
    required_capabilities: list[str] = Field(default_factory=list)
    source_reference: str | dict[str, Any]
    expected_metrics: list[str] = Field(default_factory=list)
    tolerance: dict[str, float] = Field(default_factory=dict)
    reference_metrics: dict[str, MetricReference] = Field(default_factory=dict)
    problem_definition: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    capability_gated: bool = False

    @field_validator("case_id")
    @classmethod
    def validate_case_id(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped or any(part in stripped for part in ("/", "\\", "..")):
            raise ValueError("case_id must be a simple identifier")
        return stripped

    @computed_field
    @property
    def metric_references(self) -> dict[str, MetricReference]:
        refs = dict(self.reference_metrics)
        for name, tolerance in self.tolerance.items():
            refs.setdefault(name, MetricReference(value=None, tolerance=tolerance))
        return refs


class AttemptRecord(BaseModel):
    attempt_id: int
    lane: BenchmarkLane
    status: LaneStatus
    started_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    finished_at: str | None = None
    repair: bool = False
    llm_call: bool = False
    message: str | None = None
    evidence_files: list[str] = Field(default_factory=list)


class AttemptLog(BaseModel):
    attempts: list[AttemptRecord] = Field(default_factory=list)

    def add(self, record: AttemptRecord) -> None:
        self.attempts.append(record)

    @computed_field
    @property
    def attempt_count(self) -> int:
        return len(self.attempts)

    @computed_field
    @property
    def repair_count(self) -> int:
        return sum(1 for attempt in self.attempts if attempt.repair)

    @computed_field
    @property
    def llm_calls(self) -> int:
        return sum(1 for attempt in self.attempts if attempt.llm_call)


class ClaudeInvocationRecord(BaseModel):
    binary: str
    command: list[str]
    prompt_path: str
    stdout_path: str
    stderr_path: str
    result_path: str | None = None
    proposal_path: str | None = None
    return_code: int | None = None


class LaneSummary(BaseModel):
    case_id: str
    suite: BenchmarkSuite
    lane: BenchmarkLane
    status: LaneStatus
    passed: bool = False
    metrics: dict[str, float | int | str | bool | list[float]] = Field(default_factory=dict)
    metric_diffs: dict[str, float] = Field(default_factory=dict)
    missing_metrics: list[str] = Field(default_factory=list)
    evidence_files: list[str] = Field(default_factory=list)
    attempt_count: int = 1
    repair_count: int = 0
    llm_calls: int = 0
    elapsed_seconds: float | None = None
    driver_time_seconds: float | None = None
    skip_reason: str | None = None
    error_message: str | None = None
    proposal_contract_status: str | None = None
    preflight_status: str | None = None
    failure_category: str | None = None
    repair_outcome: str | None = None
    diagnostics_files: list[str] = Field(default_factory=list)
    flags: list[str] = Field(default_factory=list)

    @computed_field
    @property
    def evidence_count(self) -> int:
        return len(self.evidence_files)


class RunManifest(BaseModel):
    suite: BenchmarkSuite
    lanes: list[BenchmarkLane]
    cases: list[str]
    runs_root: str
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    git_revision: str | None = None
    python_version: str | None = None
    claude_cli: dict[str, Any] = Field(default_factory=dict)
    tools: dict[str, Any] = Field(default_factory=dict)


class ComparisonRow(BaseModel):
    case_id: str
    suite: BenchmarkSuite
    extension_status: LaneStatus | None = None
    direct_status: LaneStatus | None = None
    agent_status: LaneStatus | None = None
    extension_passed: bool | None = None
    direct_passed: bool | None = None
    agent_passed: bool | None = None
    direct_attempts: int | None = None
    agent_attempts: int | None = None
    direct_repairs: int | None = None
    agent_repairs: int | None = None
    direct_llm_calls: int | None = None
    agent_llm_calls: int | None = None
    extension_evidence_count: int | None = None
    direct_evidence_count: int | None = None
    agent_evidence_count: int | None = None
    direct_proposal_contract_status: str | None = None
    agent_proposal_contract_status: str | None = None
    direct_preflight_status: str | None = None
    agent_preflight_status: str | None = None
    direct_failure_category: str | None = None
    agent_failure_category: str | None = None
    direct_repair_outcome: str | None = None
    agent_repair_outcome: str | None = None
    agent_diagnostics_count: int | None = None
    verdict: str
