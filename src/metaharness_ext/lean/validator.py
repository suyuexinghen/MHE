from __future__ import annotations

import hashlib
import re
from pathlib import Path

from metaharness.core.models import ScoredEvidence
from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.lean.capabilities import (
    CAP_LEAN_EVALUATE_POLICY,
    CAP_LEAN_VALIDATE_RESULT,
)
from metaharness_ext.lean.contracts import (
    LeanBlueprint,
    LeanEnvironmentReport,
    LeanEvidenceBundle,
    LeanPromotionMetadata,
    LeanProvenance,
    LeanRunArtifact,
    LeanRunPlan,
    LeanValidationReport,
)
from metaharness_ext.lean.slots import LEAN_VALIDATOR_SLOT
from metaharness_ext.lean.types import LeanDiagnosticSeverity, LeanValidationStatus

_DECLARATION_RE = re.compile(r"^\s*(?:theorem|lemma|def)\s+(?P<name>[\w'.]+)\b(?P<body>.*)$")


class LeanValidatorComponent(HarnessComponent):
    protected = True

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(LEAN_VALIDATOR_SLOT)
        api.declare_input("run", "LeanRunArtifact")
        api.declare_output("validation", "LeanValidationReport", mode="sync")
        api.provide_capability(CAP_LEAN_VALIDATE_RESULT)
        api.provide_capability(CAP_LEAN_EVALUATE_POLICY)

    def validate_run(
        self,
        artifact: LeanRunArtifact,
        plan: LeanRunPlan | None = None,
        environment_report: LeanEnvironmentReport | None = None,
        blueprint: LeanBlueprint | None = None,
    ) -> LeanValidationReport:
        if environment_report is not None and environment_report.blocks_promotion:
            return self._report(LeanValidationStatus.ENVIRONMENT_FAILED, retriable=False)

        sorry_count = self._sorry_count(artifact)
        error_count = sum(
            1
            for diagnostic in artifact.diagnostics
            if diagnostic.severity is LeanDiagnosticSeverity.ERROR and diagnostic.code != "timeout"
        )
        warning_count = sum(
            1
            for diagnostic in artifact.diagnostics
            if diagnostic.severity is LeanDiagnosticSeverity.WARNING
        )
        if any(diagnostic.code == "timeout" for diagnostic in artifact.diagnostics):
            return self._report(
                LeanValidationStatus.TIMEOUT,
                sorry_count=sorry_count,
                error_count=error_count,
                warning_count=warning_count,
                retriable=True,
            )
        if any(diagnostic.code == "workspace_error" for diagnostic in artifact.diagnostics):
            return self._report(
                LeanValidationStatus.WORKSPACE_ERROR,
                sorry_count=sorry_count,
                error_count=error_count,
                warning_count=warning_count,
                retriable=False,
            )
        if artifact.exit_code != 0 or error_count > 0:
            return self._report(
                LeanValidationStatus.COMPILATION_FAILED,
                sorry_count=sorry_count,
                error_count=max(error_count, 1),
                warning_count=warning_count,
                retriable=True,
            )
        if sorry_count > 0:
            budget = self._budget(plan, blueprint)
            attempts = self._attempts(plan)
            status = (
                LeanValidationStatus.BUDGET_EXHAUSTED
                if attempts >= budget
                else LeanValidationStatus.PARTIALLY_PROVEN
            )
            return self._report(
                status,
                sorry_count=sorry_count,
                warning_count=warning_count,
                retriable=status is LeanValidationStatus.PARTIALLY_PROVEN,
            )
        return self._report(
            LeanValidationStatus.FULLY_PROVEN,
            warning_count=warning_count,
            completeness_ratio=1.0,
            blocks_promotion=False,
            retriable=False,
        )

    def snapshot_statement(self, file: str | Path) -> dict[str, str]:
        path = Path(file)
        if not path.exists():
            return {}
        statements: dict[str, str] = {}
        for line in path.read_text().splitlines():
            match = _DECLARATION_RE.match(line)
            if match is None:
                continue
            statement = line.split(":=", 1)[0].split(" by", 1)[0].strip()
            statements[match.group("name")] = hashlib.sha256(statement.encode()).hexdigest()
        return statements

    def detect_drift(self, before: dict[str, str], after: dict[str, str]) -> list[dict[str, str]]:
        changes: list[dict[str, str]] = []
        for name in sorted(after.keys() - before.keys()):
            changes.append({"name": name, "change": "added"})
        for name in sorted(before.keys() - after.keys()):
            changes.append({"name": name, "change": "removed"})
        for name in sorted(before.keys() & after.keys()):
            if before[name] != after[name]:
                changes.append({"name": name, "change": "modified"})
        return changes

    def validate_drift(self, before: dict[str, str], after: dict[str, str]) -> LeanValidationReport:
        changes = self.detect_drift(before, after)
        blocking = any(change["change"] in {"modified", "removed"} for change in changes)
        if not changes:
            return self._report(
                LeanValidationStatus.FULLY_PROVEN,
                completeness_ratio=1.0,
                blocks_promotion=False,
            )
        report = self._report(
            LeanValidationStatus.STATEMENT_DRIFT,
            blocks_promotion=blocking,
            retriable=False,
        )
        report.drift_detected = True
        report.drift_changes = changes
        return report

    def build_evidence_bundle(
        self,
        artifact: LeanRunArtifact,
        validation: LeanValidationReport,
        environment_report: LeanEnvironmentReport,
        blueprint: LeanBlueprint | None = None,
        task_ref: str = "lean-task",
        provenance: LeanProvenance | None = None,
    ) -> LeanEvidenceBundle:
        return LeanEvidenceBundle(
            bundle_id=f"bundle:{artifact.artifact_id}",
            task_ref=task_ref,
            environment_report=environment_report,
            blueprint=blueprint,
            artifacts=[artifact],
            validation_report=validation,
            provenance=provenance
            or LeanProvenance(
                execution_mode=artifact.execution_mode,
                backend=artifact.backend,
            ),
        )

    def _report(
        self,
        status: LeanValidationStatus,
        *,
        sorry_count: int = 0,
        error_count: int = 0,
        warning_count: int = 0,
        completeness_ratio: float = 0.0,
        blocks_promotion: bool = True,
        retriable: bool = False,
    ) -> LeanValidationReport:
        return LeanValidationReport(
            status=status,
            sorry_count=sorry_count,
            error_count=error_count,
            warning_count=warning_count,
            completeness_ratio=completeness_ratio,
            blocks_promotion=blocks_promotion,
            retriable=retriable,
            scored_evidence=ScoredEvidence(
                score=completeness_ratio,
                metrics={"completeness_ratio": completeness_ratio},
                reasons=[status.value],
            ),
            promotion_metadata=LeanPromotionMetadata(
                promotion_ready=not blocks_promotion,
                blocks_promotion=blocks_promotion,
                failure_code=None if not blocks_promotion else status.value,
            ),
        )

    def _sorry_count(self, artifact: LeanRunArtifact) -> int:
        if artifact.sorry_locations:
            return len(artifact.sorry_locations)
        return sum(
            1
            for diagnostic in artifact.diagnostics
            if diagnostic.code == "sorry" or "sorry" in diagnostic.message.lower()
        )

    def _budget(self, plan: LeanRunPlan | None, blueprint: LeanBlueprint | None) -> int:
        if plan is not None and "budget" in plan.execution_params:
            return int(plan.execution_params["budget"])
        if blueprint is not None and blueprint.items:
            return max(item.budget for item in blueprint.items)
        return 1

    def _attempts(self, plan: LeanRunPlan | None) -> int:
        if plan is None:
            return 0
        return int(plan.execution_params.get("attempts", 0))
