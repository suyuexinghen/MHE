from __future__ import annotations

from metaharness.core.graph_versions import CandidateRecord
from metaharness.core.models import (
    GraphSnapshot,
    ValidationIssue,
    ValidationIssueCategory,
    ValidationReport,
)
from metaharness_ext.deepmd.contracts import (
    DeepMDEvidenceBundle,
    DeepMDPolicyReport,
    DeepMDValidationReport,
)


class DeepMDGovernanceAdapter:
    def build_core_validation_report(
        self,
        validation: DeepMDValidationReport,
        policy: DeepMDPolicyReport,
    ) -> ValidationReport:
        issues = list(validation.issues)
        issues.extend(self._policy_gate_issues(validation, policy))
        valid = (
            validation.passed
            and not validation.blocks_promotion
            and validation.governance_state == "ready"
            and policy.passed
            and policy.decision == "allow"
            and not any(issue.blocks_promotion for issue in issues)
        )
        return ValidationReport(valid=valid, issues=issues)

    def build_candidate_record(
        self,
        bundle: DeepMDEvidenceBundle,
        policy: DeepMDPolicyReport,
        *,
        snapshot: GraphSnapshot | None = None,
    ) -> CandidateRecord:
        validation = self._require_validation(bundle)
        report = self.build_core_validation_report(validation, policy)
        candidate_snapshot = snapshot or GraphSnapshot(
            graph_version=self._resolve_graph_version(bundle, validation)
        )
        return CandidateRecord(
            candidate_id=self._resolve_candidate_id(bundle, validation, candidate_snapshot),
            snapshot=candidate_snapshot,
            report=report,
            promoted=report.valid,
        )

    def _policy_gate_issues(
        self,
        validation: DeepMDValidationReport,
        policy: DeepMDPolicyReport,
    ) -> list[ValidationIssue]:
        return [
            ValidationIssue(
                code=f"deepmd_gate_{gate.gate}",
                message=gate.reason,
                subject=validation.task_id,
                category=ValidationIssueCategory.PROMOTION_BLOCKER,
                blocks_promotion=True,
            )
            for gate in policy.gates
            if gate.decision.value != "allow"
        ]

    def _resolve_graph_version(
        self,
        bundle: DeepMDEvidenceBundle,
        validation: DeepMDValidationReport,
    ) -> int:
        metadata = bundle.metadata
        raw_graph_version = (
            metadata.get("graph_version")
            or metadata.get("graph_version_id")
            or validation.summary_metrics.get("graph_version")
            or validation.summary_metrics.get("graph_version_id")
            or 0
        )
        try:
            return int(raw_graph_version)
        except (TypeError, ValueError):
            return 0

    def _resolve_candidate_id(
        self,
        bundle: DeepMDEvidenceBundle,
        validation: DeepMDValidationReport,
        snapshot: GraphSnapshot,
    ) -> str:
        metadata = bundle.metadata
        raw_candidate_id = (
            metadata.get("candidate_id")
            or validation.summary_metrics.get("candidate_id")
            or snapshot.graph_version and f"deepmd-candidate-v{snapshot.graph_version}"
            or bundle.run_id
        )
        return str(raw_candidate_id)

    def _require_validation(self, bundle: DeepMDEvidenceBundle) -> DeepMDValidationReport:
        if bundle.validation is None:
            raise ValueError("DeepMD evidence bundle requires an attached validation report")
        return bundle.validation
