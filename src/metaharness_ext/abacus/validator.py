from __future__ import annotations

from pathlib import Path

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

        if artifact.status == "unavailable" and fallback_reason:
            messages.append(f"ABACUS run unavailable: {fallback_reason}.")
            return AbacusValidationReport(
                task_id=artifact.task_id,
                run_id=artifact.run_id,
                passed=False,
                status="environment_invalid",
                messages=messages,
                evidence_files=evidence_files,
            )

        if fallback_reason == "command_timeout":
            messages.append("ABACUS command timed out.")
            return AbacusValidationReport(
                task_id=artifact.task_id,
                run_id=artifact.run_id,
                passed=False,
                status="runtime_failed",
                messages=messages,
                evidence_files=evidence_files,
            )

        if artifact.return_code is None:
            messages.append("ABACUS command did not report an exit code.")
            return AbacusValidationReport(
                task_id=artifact.task_id,
                run_id=artifact.run_id,
                passed=False,
                status="runtime_failed",
                messages=messages,
                evidence_files=evidence_files,
            )

        if artifact.return_code != 0 or artifact.status == "failed":
            messages.append(f"ABACUS command exited with code {artifact.return_code}.")
            return AbacusValidationReport(
                task_id=artifact.task_id,
                run_id=artifact.run_id,
                passed=False,
                status="runtime_failed",
                messages=messages,
                evidence_files=evidence_files,
            )

        passed, missing = self._check_family_evidence(artifact)
        if not passed:
            messages.append(
                f"ABACUS {artifact.application_family} run completed but evidence insufficient."
            )
            messages.extend(f"Missing: {m}" for m in missing)
            return AbacusValidationReport(
                task_id=artifact.task_id,
                run_id=artifact.run_id,
                passed=False,
                status="validation_failed",
                messages=messages,
                evidence_files=evidence_files,
                missing_evidence=missing,
            )

        messages.append(
            f"ABACUS {artifact.application_family} run completed with sufficient evidence."
        )
        return AbacusValidationReport(
            task_id=artifact.task_id,
            run_id=artifact.run_id,
            passed=True,
            status="executed",
            messages=messages,
            evidence_files=evidence_files,
        )

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
