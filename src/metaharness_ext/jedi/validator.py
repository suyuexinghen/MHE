from __future__ import annotations

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.jedi.capabilities import CAP_JEDI_VALIDATE
from metaharness_ext.jedi.contracts import JediRunArtifact, JediValidationReport
from metaharness_ext.jedi.slots import JEDI_VALIDATOR_SLOT


class JediValidatorComponent(HarnessComponent):
    protected = True

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(JEDI_VALIDATOR_SLOT)
        api.declare_input("run", "JediRunArtifact")
        api.declare_output("validation", "JediValidationReport", mode="sync")
        api.provide_capability(CAP_JEDI_VALIDATE)

    def validate_run(self, artifact: JediRunArtifact) -> JediValidationReport:
        fallback_reason = artifact.result_summary.get("fallback_reason")
        messages: list[str] = []
        evidence_files = [
            path
            for path in [
                artifact.config_path,
                artifact.stdout_path,
                artifact.stderr_path,
                artifact.schema_path,
            ]
            if path is not None
        ]

        if artifact.status == "unavailable":
            if fallback_reason == "execution_mode_not_supported":
                messages.append("JEDI Phase 0 does not execute real_run mode.")
                return JediValidationReport(
                    task_id=artifact.task_id,
                    run_id=artifact.run_id,
                    passed=False,
                    status="validation_failed",
                    messages=messages,
                    evidence_files=evidence_files,
                )
            messages.append(f"JEDI run unavailable: {fallback_reason}.")
            return JediValidationReport(
                task_id=artifact.task_id,
                run_id=artifact.run_id,
                passed=False,
                status="environment_invalid",
                messages=messages,
                evidence_files=evidence_files,
            )

        if fallback_reason == "command_timeout":
            messages.append("JEDI command timed out.")
            return JediValidationReport(
                task_id=artifact.task_id,
                run_id=artifact.run_id,
                passed=False,
                status="runtime_failed",
                messages=messages,
                evidence_files=evidence_files,
            )

        if artifact.return_code not in {0, None}:
            messages.append(f"JEDI command exited with code {artifact.return_code}.")
            return JediValidationReport(
                task_id=artifact.task_id,
                run_id=artifact.run_id,
                passed=False,
                status="validation_failed",
                messages=messages,
                evidence_files=evidence_files,
            )

        if artifact.execution_mode == "schema" and artifact.schema_path is None:
            messages.append("Schema output file was not produced.")
            return JediValidationReport(
                task_id=artifact.task_id,
                run_id=artifact.run_id,
                passed=False,
                status="validation_failed",
                messages=messages,
                evidence_files=evidence_files,
            )

        messages.append("JEDI configuration validated successfully.")
        summary_metrics: dict[str, float | str] = {}
        if artifact.schema_path is not None:
            summary_metrics["schema_path"] = artifact.schema_path
        return JediValidationReport(
            task_id=artifact.task_id,
            run_id=artifact.run_id,
            passed=True,
            status="validated",
            messages=messages,
            summary_metrics=summary_metrics,
            evidence_files=evidence_files,
        )
