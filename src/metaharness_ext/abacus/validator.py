from __future__ import annotations

from pathlib import Path

from metaharness.core.models import (
    BudgetState,
    ConvergenceState,
    ScoredEvidence,
    ValidationIssue,
    ValidationIssueCategory,
)
from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.abacus.capabilities import CAP_ABACUS_VALIDATE
from metaharness_ext.abacus.contracts import AbacusRunArtifact, AbacusValidationReport
from metaharness_ext.abacus.slots import ABACUS_VALIDATOR_SLOT


class AbacusValidatorComponent(HarnessComponent):
    protected = True

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self, runtime: ComponentRuntime) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(ABACUS_VALIDATOR_SLOT)
        api.declare_input("run", "AbacusRunArtifact")
        api.declare_output("validation", "AbacusValidationReport", mode="sync")
        api.provide_capability(CAP_ABACUS_VALIDATE)

    def validate_run(self, artifact: AbacusRunArtifact) -> AbacusValidationReport:
        messages: list[str] = []
        issues: list[ValidationIssue] = []
        fallback_reason = artifact.result_summary.get("fallback_reason")
        evidence_files = [
            path
            for path in [
                artifact.stdout_path,
                artifact.stderr_path,
                artifact.output_root,
                *artifact.prepared_inputs,
                *artifact.output_files,
                *artifact.diagnostic_files,
                *artifact.structure_files,
            ]
            if path is not None
        ]
        evidence_refs = self._build_evidence_refs(artifact, evidence_files)

        missing_prerequisites = artifact.result_summary.get("missing_prerequisites")
        if missing_prerequisites:
            missing_list = [str(item) for item in missing_prerequisites]
            messages.append(
                "ABACUS run blocked by missing environment prerequisites: "
                + ", ".join(missing_list)
                + "."
            )
            issues.extend(
                ValidationIssue(
                    code="abacus_missing_prerequisite",
                    message=f"Missing ABACUS prerequisite: {item}.",
                    subject=artifact.task_id,
                    category=ValidationIssueCategory.PROMOTION_BLOCKER,
                    blocks_promotion=True,
                )
                for item in missing_list
            )
            return self._build_report(
                artifact,
                passed=False,
                status="environment_invalid",
                messages=messages,
                evidence_files=evidence_files,
                evidence_refs=evidence_refs,
                missing_evidence=missing_list,
                issues=issues,
            )

        if artifact.status == "unavailable" and fallback_reason:
            messages.append(f"ABACUS run unavailable: {fallback_reason}.")
            issues.append(
                ValidationIssue(
                    code=f"abacus_{fallback_reason}",
                    message=f"ABACUS run unavailable: {fallback_reason}.",
                    subject=artifact.task_id,
                    category=ValidationIssueCategory.READINESS,
                    blocks_promotion=True,
                )
            )
            return self._build_report(
                artifact,
                passed=False,
                status="environment_invalid",
                messages=messages,
                evidence_files=evidence_files,
                evidence_refs=evidence_refs,
                issues=issues,
            )

        if fallback_reason == "command_timeout":
            messages.append("ABACUS command timed out.")
            issues.append(
                ValidationIssue(
                    code="abacus_command_timeout",
                    message="ABACUS command timed out.",
                    subject=artifact.task_id,
                    category=ValidationIssueCategory.READINESS,
                    blocks_promotion=True,
                )
            )
            return self._build_report(
                artifact,
                passed=False,
                status="runtime_failed",
                messages=messages,
                evidence_files=evidence_files,
                evidence_refs=evidence_refs,
                issues=issues,
            )

        if artifact.return_code is None:
            messages.append("ABACUS command did not report an exit code.")
            issues.append(
                ValidationIssue(
                    code="abacus_missing_exit_code",
                    message="ABACUS command did not report an exit code.",
                    subject=artifact.task_id,
                    category=ValidationIssueCategory.READINESS,
                    blocks_promotion=True,
                )
            )
            return self._build_report(
                artifact,
                passed=False,
                status="runtime_failed",
                messages=messages,
                evidence_files=evidence_files,
                evidence_refs=evidence_refs,
                issues=issues,
            )

        if artifact.return_code != 0 or artifact.status == "failed":
            messages.append(f"ABACUS command exited with code {artifact.return_code}.")
            issues.append(
                ValidationIssue(
                    code="abacus_runtime_failed",
                    message=f"ABACUS command exited with code {artifact.return_code}.",
                    subject=artifact.task_id,
                    category=ValidationIssueCategory.READINESS,
                    blocks_promotion=True,
                )
            )
            return self._build_report(
                artifact,
                passed=False,
                status="runtime_failed",
                messages=messages,
                evidence_files=evidence_files,
                evidence_refs=evidence_refs,
                issues=issues,
            )

        passed, missing = self._check_family_evidence(artifact)
        if not passed:
            messages.append(
                f"ABACUS {artifact.application_family} run completed but evidence insufficient."
            )
            messages.extend(f"Missing: {m}" for m in missing)
            issues.extend(
                ValidationIssue(
                    code="abacus_missing_evidence",
                    message=f"Missing ABACUS evidence: {item}.",
                    subject=artifact.task_id,
                    category=ValidationIssueCategory.PROMOTION_BLOCKER,
                    blocks_promotion=True,
                )
                for item in missing
            )
            return self._build_report(
                artifact,
                passed=False,
                status="validation_failed",
                messages=messages,
                evidence_files=evidence_files,
                evidence_refs=evidence_refs,
                missing_evidence=missing,
                issues=issues,
            )

        messages.append(
            f"ABACUS {artifact.application_family} run completed with sufficient evidence."
        )
        return self._build_report(
            artifact,
            passed=True,
            status="executed",
            messages=messages,
            evidence_files=evidence_files,
            evidence_refs=evidence_refs,
            issues=issues,
        )

    def _build_report(
        self,
        artifact: AbacusRunArtifact,
        *,
        passed: bool,
        status: str,
        messages: list[str],
        evidence_files: list[str],
        evidence_refs: list[str],
        issues: list[ValidationIssue],
        missing_evidence: list[str] | None = None,
    ) -> AbacusValidationReport:
        summary_metrics: dict[str, float | str | bool] = {
            "return_code": artifact.return_code if artifact.return_code is not None else "none",
            "has_output_root": artifact.output_root is not None,
            "has_missing_prerequisites": bool(artifact.result_summary.get("missing_prerequisites")),
            "has_evidence_files": bool(evidence_files),
            "blocks_promotion": any(issue.blocks_promotion for issue in issues),
            "application_family": artifact.application_family,
            "status": status,
        }
        esolver_type = artifact.result_summary.get("esolver_type")
        if isinstance(esolver_type, str):
            summary_metrics["esolver_type"] = esolver_type

        governance_state = "defer" if passed else "blocked"
        scored_evidence = ScoredEvidence(
            score=1.0 if passed else 0.0,
            metrics={
                key: float(value)
                for key, value in summary_metrics.items()
                if isinstance(value, int | float)
            },
            safety_score=1.0 if passed else 0.0,
            budget=BudgetState(used=1, exhausted=not passed),
            convergence=ConvergenceState(
                converged=passed,
                criteria_met=["evidence_sufficient"] if passed else [],
                reason="validator accepted run" if passed else "validator rejected run",
            ),
            evidence_refs=evidence_refs,
            reasons=list(messages),
            attributes={
                "status": status,
                "application_family": artifact.application_family,
                "governance_state": governance_state,
            },
        )
        return AbacusValidationReport(
            task_id=artifact.task_id,
            run_id=artifact.run_id,
            passed=passed,
            status=status,
            messages=messages,
            summary_metrics=summary_metrics,
            evidence_files=evidence_files,
            evidence_refs=evidence_refs,
            missing_evidence=missing_evidence or [],
            issues=issues,
            blocks_promotion=any(issue.blocks_promotion for issue in issues),
            governance_state=governance_state,
            scored_evidence=scored_evidence,
        )

    def _build_evidence_refs(
        self, artifact: AbacusRunArtifact, evidence_files: list[str]
    ) -> list[str]:
        refs = [
            f"abacus://run/{artifact.task_id}/{artifact.run_id}",
            f"abacus://run/{artifact.task_id}/{artifact.run_id}/family/{artifact.application_family}",
        ]
        refs.extend(artifact.evidence_refs)
        refs.extend(f"abacus://file/{Path(path).name}" for path in evidence_files)
        return list(dict.fromkeys(refs))

    def _check_family_evidence(self, artifact: AbacusRunArtifact) -> tuple[bool, list[str]]:
        missing: list[str] = []
        family = artifact.application_family

        out_dirs = [
            p
            for p in [artifact.output_root, *artifact.output_files]
            if p is not None and Path(p).name.startswith("OUT.")
        ]
        if not out_dirs:
            missing.append("OUT.<suffix>/ directory")

        if family == "scf":
            log_evidence = any("running_scf.log" in Path(p).name for p in artifact.diagnostic_files)
            if not log_evidence and out_dirs:
                out_path = Path(out_dirs[0])
                if out_path.exists() and any(out_path.rglob("running_scf.log")):
                    log_evidence = True
            if not log_evidence:
                missing.append("SCF log evidence (running_scf.log)")

        elif family == "nscf":
            nscf_log_evidence = any(
                Path(p).name in {"running_nscf.log", "running_scf.log"}
                for p in artifact.diagnostic_files
            )
            if not nscf_log_evidence:
                missing.append("NSCF log evidence (running_nscf.log or running_scf.log)")

        elif family == "relax":
            structure_evidence = any(
                Path(p).name.startswith("STRU") or Path(p).suffix == ".cif"
                for p in [*artifact.output_files, *artifact.structure_files]
            )
            if not structure_evidence and out_dirs:
                out_path = Path(out_dirs[0])
                if out_path.exists() and any(out_path.rglob("STRU*")):
                    structure_evidence = True
            if not structure_evidence:
                missing.append("final structure evidence (STRU*)")

        elif family == "md":
            md_evidence = any(
                Path(p).name.startswith(("MD_dump", "Restart_md", "STRU_MD"))
                for p in artifact.output_files
            )
            if not md_evidence and out_dirs:
                out_path = Path(out_dirs[0])
                if out_path.exists():
                    for pattern in ("MD_dump*", "Restart_md*", "STRU_MD*"):
                        if any(out_path.rglob(pattern)):
                            md_evidence = True
                            break
            if not md_evidence:
                missing.append("MD evidence (MD_dump, Restart_md, STRU_MD*)")

        return (not missing, missing)
