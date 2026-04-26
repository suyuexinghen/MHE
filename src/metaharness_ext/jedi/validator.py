from __future__ import annotations

from metaharness.core.models import SessionEventType
from metaharness.observability.events import make_session_event
from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.jedi.capabilities import CAP_JEDI_VALIDATE
from metaharness_ext.jedi.contracts import (
    JediDiagnosticSummary,
    JediRunArtifact,
    JediValidationReport,
)
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
                *artifact.prepared_inputs,
                *artifact.output_files,
                *artifact.diagnostic_files,
                *artifact.reference_files,
            ]
            if path is not None
        ]
        prerequisite_evidence = self._coerce_prerequisite_evidence(
            artifact.result_summary.get("prerequisite_evidence")
        )
        provenance_refs = self._coerce_string_list(artifact.result_summary.get("provenance_refs"))
        checkpoint_refs = self._coerce_string_list(artifact.result_summary.get("checkpoint_refs"))
        audit_refs = self._coerce_string_list(artifact.result_summary.get("audit_refs"))
        candidate_id = self._coerce_optional_string(artifact.result_summary.get("candidate_id"))
        graph_version_id = self._coerce_optional_int(
            artifact.result_summary.get("graph_version_id")
        )
        session_id = (
            self._coerce_optional_string(artifact.result_summary.get("session_id"))
            or artifact.task_id
        )

        def build_report(
            *,
            passed: bool,
            status: str,
            summary_metrics: dict[str, float | str] | None = None,
        ) -> JediValidationReport:
            policy_decision = self._policy_decision_for_status(status)
            session_events = self._build_session_events(
                artifact=artifact,
                session_id=session_id,
                candidate_id=candidate_id,
                graph_version_id=graph_version_id,
                policy_decision=policy_decision,
                blocking_reasons=self._blocking_reasons_for_status(status, messages),
            )
            return JediValidationReport(
                task_id=artifact.task_id,
                run_id=artifact.run_id,
                passed=passed,
                status=status,
                messages=list(messages),
                summary_metrics=summary_metrics or {},
                evidence_files=evidence_files,
                blocking_reasons=self._blocking_reasons_for_status(status, messages),
                policy_decision=policy_decision,
                prerequisite_evidence=prerequisite_evidence,
                provenance_refs=provenance_refs,
                checkpoint_refs=checkpoint_refs,
                candidate_id=candidate_id or artifact.run_id,
                graph_version_id=graph_version_id,
                session_id=session_id,
                session_events=session_events,
                audit_refs=audit_refs,
            )

        if artifact.status == "unavailable":
            messages.append(f"JEDI run unavailable: {fallback_reason}.")
            return build_report(passed=False, status="environment_invalid")

        if fallback_reason == "command_timeout":
            messages.append("JEDI command timed out.")
            return build_report(passed=False, status="runtime_failed")

        if artifact.return_code is None:
            messages.append("JEDI command did not report an exit code.")
            return build_report(passed=False, status="runtime_failed")

        if artifact.return_code != 0 or artifact.status == "failed":
            messages.append(f"JEDI command exited with code {artifact.return_code}.")
            return build_report(passed=False, status="runtime_failed")

        summary_metrics: dict[str, float | str] = {}
        if artifact.execution_mode == "schema":
            if artifact.schema_path is None:
                messages.append("Schema output file was not produced.")
                return build_report(passed=False, status="validation_failed")
            messages.append("JEDI configuration validated successfully.")
            summary_metrics["schema_path"] = artifact.schema_path
            return build_report(
                passed=True,
                status="validated",
                summary_metrics=summary_metrics,
            )

        if artifact.execution_mode == "validate_only":
            messages.append("JEDI configuration validated successfully.")
            return build_report(
                passed=True,
                status="validated",
                summary_metrics=summary_metrics,
            )

        if not artifact.output_files:
            messages.append("JEDI real_run finished without a primary analysis output.")
            return build_report(passed=False, status="validation_failed")

        if not artifact.diagnostic_files and not artifact.reference_files:
            messages.append("JEDI real_run finished without diagnostics or reference evidence.")
            return build_report(passed=False, status="validation_failed")

        summary_metrics["primary_output"] = artifact.output_files[0]
        summary_metrics["diagnostic_count"] = float(len(artifact.diagnostic_files))
        summary_metrics["reference_count"] = float(len(artifact.reference_files))

        scientific_check = artifact.result_summary.get("scientific_check", "runtime_only")
        if scientific_check == "rms_improves":
            if not self._has_rms_improvement(artifact.result_summary):
                messages.append(
                    "JEDI real_run did not satisfy the minimum RMS improvement criterion."
                )
                return build_report(
                    passed=False,
                    status="validation_failed",
                    summary_metrics=summary_metrics,
                )
            summary_metrics["rms_observation_minus_analysis"] = float(
                artifact.result_summary["rms_observation_minus_analysis"]
            )
            summary_metrics["rms_observation_minus_background"] = float(
                artifact.result_summary["rms_observation_minus_background"]
            )
            messages.append("JEDI real_run completed with minimum scientific evidence.")
        elif scientific_check == "ensemble_outputs_present":
            messages.append("JEDI local_ensemble_da completed with minimum ensemble evidence.")
        else:
            messages.append("JEDI real_run completed with runtime and artifact evidence.")

        return build_report(
            passed=True,
            status="executed",
            summary_metrics=summary_metrics,
        )

    def validate_run_with_diagnostics(
        self,
        artifact: JediRunArtifact,
        diagnostic_summary: JediDiagnosticSummary | None = None,
    ) -> JediValidationReport:
        """Validate a run with optional Phase 1 diagnostics enrichment.

        Falls back to `validate_run` when no diagnostic summary is provided.
        When diagnostics are present, the report includes IODA group-level
        evidence and distinguishes runtime completion from scientific acceptance.
        """
        report = self.validate_run(artifact)
        if diagnostic_summary is None:
            return report

        # Enrich the existing report with diagnostics metadata
        enriched_metrics = dict(report.summary_metrics)
        enriched_messages = list(report.messages)
        enriched_files = list(report.evidence_files)

        enriched_metrics["ioda_groups_found"] = len(diagnostic_summary.ioda_groups_found)
        enriched_metrics["ioda_groups_missing"] = len(diagnostic_summary.ioda_groups_missing)
        enriched_metrics["diagnostic_files_scanned"] = len(diagnostic_summary.files_scanned)

        if diagnostic_summary.minimizer_iterations is not None:
            enriched_metrics["minimizer_iterations"] = float(
                diagnostic_summary.minimizer_iterations
            )
        if diagnostic_summary.outer_iterations is not None:
            enriched_metrics["outer_iterations"] = float(diagnostic_summary.outer_iterations)
        if diagnostic_summary.inner_iterations is not None:
            enriched_metrics["inner_iterations"] = float(diagnostic_summary.inner_iterations)
        if diagnostic_summary.initial_cost_function is not None:
            enriched_metrics["initial_cost_function"] = diagnostic_summary.initial_cost_function
        if diagnostic_summary.final_cost_function is not None:
            enriched_metrics["final_cost_function"] = diagnostic_summary.final_cost_function
        if diagnostic_summary.initial_gradient_norm is not None:
            enriched_metrics["initial_gradient_norm"] = diagnostic_summary.initial_gradient_norm
        if diagnostic_summary.final_gradient_norm is not None:
            enriched_metrics["final_gradient_norm"] = diagnostic_summary.final_gradient_norm
        if diagnostic_summary.gradient_norm_reduction is not None:
            enriched_metrics["gradient_norm_reduction"] = diagnostic_summary.gradient_norm_reduction
        enriched_metrics["posterior_output_detected"] = str(
            diagnostic_summary.posterior_output_detected
        )
        enriched_metrics["observer_output_detected"] = str(
            diagnostic_summary.observer_output_detected
        )

        if diagnostic_summary.ioda_groups_found:
            enriched_messages.append(
                f"IODA groups detected: {', '.join(diagnostic_summary.ioda_groups_found)}."
            )
        if diagnostic_summary.ioda_groups_missing:
            enriched_messages.append(
                f"Missing IODA groups: {', '.join(diagnostic_summary.ioda_groups_missing)}."
            )
        if diagnostic_summary.gradient_norm_reduction is not None:
            enriched_messages.append(
                f"Gradient norm reduction: {diagnostic_summary.gradient_norm_reduction:.6f}."
            )
        if diagnostic_summary.posterior_output_detected:
            enriched_messages.append("Posterior output evidence detected.")
        if diagnostic_summary.observer_output_detected:
            enriched_messages.append("Observer output evidence detected.")

        has_structured_signal = self._has_structured_diagnostics(diagnostic_summary)
        passed = report.passed
        status = report.status
        policy_decision = report.policy_decision
        blocking_reasons = list(report.blocking_reasons)
        session_events = list(report.session_events)

        if artifact.execution_mode == "real_run" and report.passed and not has_structured_signal:
            diagnostics_message = "JEDI real_run completed without structured diagnostics evidence."
            enriched_messages.append(diagnostics_message)
            passed = False
            status = "validation_failed"
            policy_decision = "defer"
            blocking_reasons.append(diagnostics_message)
            session_events = self._build_session_events(
                artifact=artifact,
                session_id=report.session_id,
                candidate_id=report.candidate_id,
                graph_version_id=report.graph_version_id,
                policy_decision=policy_decision,
                blocking_reasons=blocking_reasons,
            )

        enriched_files.extend(diagnostic_summary.files_scanned)
        deduped_files = list(dict.fromkeys(enriched_files))

        return JediValidationReport(
            task_id=report.task_id,
            run_id=report.run_id,
            passed=passed,
            status=status,
            messages=enriched_messages,
            summary_metrics=enriched_metrics,
            evidence_files=deduped_files,
            blocking_reasons=blocking_reasons,
            policy_decision=policy_decision,
            prerequisite_evidence=dict(report.prerequisite_evidence),
            provenance_refs=list(report.provenance_refs),
            checkpoint_refs=list(report.checkpoint_refs),
            candidate_id=report.candidate_id,
            graph_version_id=report.graph_version_id,
            session_id=report.session_id,
            session_events=session_events,
            audit_refs=list(report.audit_refs),
        )

    def _has_rms_improvement(self, result_summary: dict[str, object]) -> bool:
        observation_minus_analysis = result_summary.get("rms_observation_minus_analysis")
        observation_minus_background = result_summary.get("rms_observation_minus_background")
        if not isinstance(observation_minus_analysis, int | float):
            return False
        if not isinstance(observation_minus_background, int | float):
            return False
        return float(observation_minus_analysis) < float(observation_minus_background)

    def _has_structured_diagnostics(self, diagnostic_summary: JediDiagnosticSummary) -> bool:
        return bool(
            diagnostic_summary.files_scanned
            or diagnostic_summary.ioda_groups_found
            or diagnostic_summary.gradient_norm_reduction is not None
            or diagnostic_summary.observer_output_detected
            or diagnostic_summary.posterior_output_detected
        )

    def _blocking_reasons_for_status(self, status: str, messages: list[str]) -> list[str]:
        if status in {"validated", "executed"}:
            return []
        return list(messages)

    def _policy_decision_for_status(self, status: str) -> str:
        if status in {"validated", "executed"}:
            return "allow"
        if status == "environment_invalid":
            return "reject"
        return "defer"

    def _build_session_events(
        self,
        *,
        artifact: JediRunArtifact,
        session_id: str,
        candidate_id: str | None,
        graph_version_id: int | None,
        policy_decision: str,
        blocking_reasons: list[str],
    ) -> list:
        payload = {
            "run_id": artifact.run_id,
            "status": policy_decision,
            "execution_mode": artifact.execution_mode,
            "blocking_reasons": list(blocking_reasons),
        }
        validated_event = make_session_event(
            session_id,
            SessionEventType.CANDIDATE_VALIDATED,
            graph_version=graph_version_id,
            candidate_id=candidate_id or artifact.run_id,
            payload=payload,
        )
        if policy_decision == "reject":
            return [
                validated_event,
                make_session_event(
                    session_id,
                    SessionEventType.CANDIDATE_REJECTED,
                    graph_version=graph_version_id,
                    candidate_id=candidate_id or artifact.run_id,
                    payload=payload,
                ),
            ]
        return [validated_event]

    def _coerce_prerequisite_evidence(self, value: object) -> dict[str, list[str]]:
        if not isinstance(value, dict):
            return {}
        evidence: dict[str, list[str]] = {}
        for key, raw_paths in value.items():
            if not isinstance(key, str) or not isinstance(raw_paths, list):
                continue
            evidence[key] = [path for path in raw_paths if isinstance(path, str)]
        return evidence

    def _coerce_string_list(self, value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, str)]

    def _coerce_optional_string(self, value: object) -> str | None:
        return value if isinstance(value, str) and value else None

    def _coerce_optional_int(self, value: object) -> int | None:
        return value if isinstance(value, int) else None
