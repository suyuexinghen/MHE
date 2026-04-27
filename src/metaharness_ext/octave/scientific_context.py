from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from metaharness.core.models import (
    BudgetState,
    ConvergenceState,
    ScoredEvidence,
    ValidationIssue,
    ValidationIssueCategory,
)
from metaharness_ext.octave.contracts import (
    OctaveExperimentSpec,
    OctaveRunArtifact,
    OctaveValidationReport,
)


@dataclass(slots=True)
class OctaveScientificContextResult:
    spec: OctaveExperimentSpec | None = None
    issues: list[ValidationIssue] = field(default_factory=list)
    scored_evidence: ScoredEvidence | None = None
    context_facts: dict[str, Any] = field(default_factory=dict)


class OctaveScientificContextAdapter:
    def pre_compile(self, spec: OctaveExperimentSpec) -> OctaveScientificContextResult:
        issues: list[ValidationIssue] = []
        input_units = {asset.variable_name: asset.unit for asset in spec.inputs if asset.unit}
        output_units = {
            output.metric_key: output.unit for output in spec.expected_outputs if output.unit
        }
        if any(output.invariants for output in spec.expected_outputs) and not output_units:
            issues.append(
                ValidationIssue(
                    code="octave_context_invariant_without_units",
                    message="Octave invariants are declared without output unit annotations.",
                    subject=spec.task_id,
                    category=ValidationIssueCategory.READINESS,
                    blocks_promotion=False,
                )
            )
        if spec.script.method_hints.get("stiffness") not in {None, "auto", "stiff", "non_stiff"}:
            issues.append(
                ValidationIssue(
                    code="octave_context_invalid_stiffness_hint",
                    message="Octave method_hints.stiffness must be auto, stiff, or non_stiff.",
                    subject=spec.task_id,
                    category=ValidationIssueCategory.READINESS,
                    blocks_promotion=False,
                )
            )
        return OctaveScientificContextResult(
            spec=spec,
            issues=issues,
            context_facts={
                "input_units": input_units,
                "output_units": output_units,
                "method_hints": dict(spec.script.method_hints),
            },
        )

    def post_validate(
        self,
        report: OctaveValidationReport,
        artifact: OctaveRunArtifact,
        spec: OctaveExperimentSpec,
    ) -> OctaveScientificContextResult:
        issues: list[ValidationIssue] = []
        context_facts: dict[str, Any] = {
            "numeric_metric_count": len(report.numeric_metrics),
            "warning_count": len(artifact.warnings),
            "units_checked": bool(
                [output for output in spec.expected_outputs if output.unit]
                or [asset for asset in spec.inputs if asset.unit]
            ),
        }
        for output in spec.expected_outputs:
            for invariant in output.invariants:
                description = (
                    invariant.get("description")
                    if isinstance(invariant, dict)
                    else invariant.description
                )
                issues.append(
                    ValidationIssue(
                        code="octave_context_invariant_deferred",
                        message=f"Invariant requires domain evaluation: {description}.",
                        subject=f"{spec.task_id}:{output.metric_key}",
                        category=ValidationIssueCategory.READINESS,
                        blocks_promotion=False,
                    )
                )
        score = 1.0 if report.passed and not issues else 0.5 if report.passed else 0.0
        scored_evidence = ScoredEvidence(
            score=score,
            metrics={
                key: float(value)
                for key, value in report.numeric_metrics.items()
                if isinstance(value, int | float) and not isinstance(value, bool)
            },
            safety_score=1.0 if not any(issue.blocks_promotion for issue in issues) else 0.0,
            budget=BudgetState(used=1, exhausted=False),
            convergence=ConvergenceState(
                converged=report.passed and not issues,
                criteria_met=["context_checked"] if report.passed else [],
                reason="scientific context checked" if report.passed else "validation failed",
            ),
            evidence_refs=list(report.evidence_refs),
            reasons=[*report.messages, *(issue.message for issue in issues)],
            attributes={
                "adapter": "octave_scientific_context",
                "validation_status": report.status,
                "governance_state": report.governance_state,
            },
        )
        return OctaveScientificContextResult(
            issues=issues,
            scored_evidence=scored_evidence,
            context_facts=context_facts,
        )
