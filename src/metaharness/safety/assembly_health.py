"""WARN-only assembly health gate for graph promotion."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel

from metaharness.core.assembly import AssemblyHealthSummary, AssemblyLedger, CopyCountIndex
from metaharness.core.models import PromotionContext
from metaharness.core.mutation import MutationProposal
from metaharness.safety.gates import GateDecision, GateResult


class AssemblyHealthPolicyMode(str, Enum):
    """Calibrated assembly-health enforcement levels."""

    WARN_ONLY = "warn_only"
    DEFER_HIGH_RISK = "defer_high_risk"
    REJECT_CRITICAL = "reject_critical"


class AssemblyHealthPolicy(BaseModel):
    """Configurable policy for assembly-health enforcement."""

    mode: AssemblyHealthPolicyMode = AssemblyHealthPolicyMode.WARN_ONLY
    high_assembly_index: int = 3
    low_history_folding_ratio: float = 0.5
    require_complete_lineage_for_reject: bool = True

    @classmethod
    def from_context(cls, value: object | None) -> "AssemblyHealthPolicy":
        if isinstance(value, cls):
            return value
        if isinstance(value, dict):
            return cls.model_validate(value)
        return cls()


class AssemblyHealthGate:
    """Report assembly-health evidence without blocking promotion by default."""

    name = "assembly_health"

    def __init__(self, policy: AssemblyHealthPolicy | None = None) -> None:
        self.policy = policy or AssemblyHealthPolicy()

    def evaluate(
        self, proposal: MutationProposal, context: dict[str, Any] | None = None
    ) -> GateResult:
        return GateResult(gate=self.name, decision=GateDecision.ALLOW, reason="assembly_health_ok")

    def evaluate_promotion(
        self, promotion: PromotionContext, context: dict[str, Any] | None = None
    ) -> GateResult:
        gate_context = context or {}
        policy = AssemblyHealthPolicy.from_context(
            gate_context.get("assembly_health_policy", self.policy)
        )
        summary = self._summary_for(promotion, gate_context)
        risk = self._risk_for(summary, gate_context, policy)
        evidence = {
            "candidate_id": summary.candidate_id,
            "graph_version": summary.graph_version,
            "component_count": summary.component_count,
            "edge_count": summary.edge_count,
            "lineage_completeness": summary.lineage_completeness,
            "new_component_refs": summary.new_component_refs,
            "low_copy_component_refs": summary.low_copy_component_refs,
            "assembly_index": summary.assembly_index,
            "history_folding_ratio": summary.history_folding_ratio,
            "low_copy_critical_dependency_count": summary.low_copy_critical_dependency_count,
            "lineage_status": summary.lineage_status,
            "dependency_graph_ref": summary.dependency_graph_ref,
            "evidence_refs": summary.evidence_refs,
            "warnings": summary.warnings,
            "policy_mode": policy.mode.value,
            "risk_level": risk["level"],
            "risk_reasons": risk["reasons"],
            "critical_mismatch_refs": risk["critical_mismatch_refs"],
        }
        if policy.mode == AssemblyHealthPolicyMode.WARN_ONLY:
            reason = "assembly_health_warn" if summary.warnings else "assembly_health_ok"
            return GateResult(
                gate=self.name, decision=GateDecision.ALLOW, reason=reason, evidence=evidence
            )
        if risk["level"] == "critical" and risk["critical_mismatch_refs"]:
            return GateResult(
                gate=self.name,
                decision=GateDecision.REJECT,
                reason="assembly_health_critical",
                evidence=evidence,
            )
        if risk["level"] in {"high", "critical"}:
            return GateResult(
                gate=self.name,
                decision=GateDecision.DEFER,
                reason="assembly_health_deferred",
                evidence=evidence,
            )
        return GateResult(
            gate=self.name,
            decision=GateDecision.ALLOW,
            reason="assembly_health_ok",
            evidence=evidence,
        )

    def _risk_for(
        self,
        summary: AssemblyHealthSummary,
        context: dict[str, Any],
        policy: AssemblyHealthPolicy,
    ) -> dict[str, Any]:
        reasons: list[str] = []
        if summary.low_copy_critical_dependency_count:
            reasons.append("low_copy_critical_dependencies")
        if summary.lineage_status in {"unknown", "partial"} and summary.component_count:
            reasons.append(f"assembly_lineage_{summary.lineage_status}")
        if (
            summary.assembly_index >= policy.high_assembly_index
            and summary.history_folding_ratio < policy.low_history_folding_ratio
        ):
            reasons.append("high_assembly_index_low_reuse")
        critical_mismatch_refs = list(context.get("critical_mismatch_refs") or [])
        if critical_mismatch_refs:
            reasons.append("critical_mismatch")
        if critical_mismatch_refs:
            level = "critical"
        elif reasons:
            level = "high"
        else:
            level = "low"
        return {
            "level": level,
            "reasons": reasons,
            "critical_mismatch_refs": critical_mismatch_refs,
        }

    def _summary_for(
        self, promotion: PromotionContext, context: dict[str, Any]
    ) -> AssemblyHealthSummary:
        existing = context.get("assembly_health_summary")
        if isinstance(existing, AssemblyHealthSummary):
            return existing
        if isinstance(existing, dict):
            return AssemblyHealthSummary.model_validate(existing)

        ledger = context.get("assembly_ledger")
        copy_count_index = context.get("copy_count_index")
        if isinstance(ledger, AssemblyLedger):
            component_refs = [node.component_id for node in promotion.candidate_snapshot.nodes]
            edge_count = len(promotion.candidate_snapshot.edges)
            return ledger.health_summary(
                candidate_id=promotion.candidate_id,
                graph_version=promotion.proposed_graph_version,
                component_refs=component_refs,
                edge_count=edge_count,
                copy_count_index=copy_count_index
                if isinstance(copy_count_index, CopyCountIndex)
                else None,
                dependency_graph_snapshot=context.get("dependency_graph_snapshot"),
            )
        component_refs = [node.component_id for node in promotion.candidate_snapshot.nodes]
        warnings = ["assembly_ledger_missing"] if component_refs else []
        low_copy_refs = list(component_refs)
        return AssemblyHealthSummary(
            candidate_id=promotion.candidate_id,
            graph_version=promotion.proposed_graph_version,
            component_count=len(component_refs),
            edge_count=len(promotion.candidate_snapshot.edges),
            lineage_completeness=0.0 if component_refs else 1.0,
            new_component_refs=component_refs,
            low_copy_component_refs=low_copy_refs,
            lineage_status="unknown" if component_refs else "complete",
            warnings=warnings or ["assembly_health_unavailable"],
        )
