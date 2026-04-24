from __future__ import annotations

from metaharness.safety.gates import GateDecision, GateResult
from metaharness_ext.jedi.contracts import JediEvidenceBundle, JediEvidenceWarning, JediPolicyReport


class JediEvidencePolicy:
    def _report_evidence(self, bundle: JediEvidenceBundle, validation_status: str | None) -> dict[str, object]:
        evidence: dict[str, object] = {"run_id": bundle.run_id, "status": validation_status}
        for key in (
            "diagnostic_files_scanned",
            "ioda_groups_found",
            "ioda_groups_missing",
            "minimizer_iterations",
            "outer_iterations",
            "inner_iterations",
            "initial_cost_function",
            "final_cost_function",
            "initial_gradient_norm",
            "final_gradient_norm",
            "gradient_norm_reduction",
            "observer_output_detected",
            "posterior_output_detected",
        ):
            if key in bundle.metadata:
                evidence[key] = bundle.metadata[key]
        return evidence

    def evaluate(self, bundle: JediEvidenceBundle) -> JediPolicyReport:
        gates: list[GateResult] = []
        warnings = list(bundle.warnings)
        validation = bundle.validation
        if validation is None:
            gates.append(
                GateResult(
                    gate="validation_presence",
                    decision=GateDecision.DEFER,
                    reason="Validation report is not attached to the evidence bundle.",
                    evidence={"run_id": bundle.run_id},
                )
            )
            return JediPolicyReport(
                passed=False,
                decision="defer",
                reason="Validation report is not attached to the evidence bundle.",
                warnings=warnings,
                gates=gates,
                evidence={"run_id": bundle.run_id},
            )

        if validation.status == "environment_invalid":
            gates.append(
                GateResult(
                    gate="environment_readiness",
                    decision=GateDecision.REJECT,
                    reason="Validation status is environment_invalid.",
                    evidence={
                        "status": validation.status,
                        "run_id": bundle.run_id,
                        "blocking_reasons": validation.blocking_reasons,
                    },
                )
            )
            return JediPolicyReport(
                passed=False,
                decision="reject",
                reason="Validation status is environment_invalid.",
                warnings=warnings,
                gates=gates,
                evidence=self._report_evidence(bundle, validation.status),
            )

        if validation.status in {"runtime_failed", "validation_failed"}:
            gates.append(
                GateResult(
                    gate="run_status",
                    decision=GateDecision.DEFER,
                    reason=f"Validation status is {validation.status}.",
                    evidence={
                        "status": validation.status,
                        "run_id": bundle.run_id,
                        "blocking_reasons": validation.blocking_reasons,
                    },
                )
            )
            return JediPolicyReport(
                passed=False,
                decision="defer",
                reason=f"Validation status is {validation.status}.",
                warnings=warnings,
                gates=gates,
                evidence=self._report_evidence(bundle, validation.status),
            )

        incomplete = False
        if not bundle.run.stdout_path or not bundle.run.stderr_path:
            incomplete = True
            gates.append(
                GateResult(
                    gate="log_completeness",
                    decision=GateDecision.DEFER,
                    reason="Evidence bundle is missing stdout/stderr log references.",
                    evidence={"run_id": bundle.run_id},
                )
            )

        if bundle.execution_mode == "real_run" and not bundle.run.output_files:
            incomplete = True
            gates.append(
                GateResult(
                    gate="primary_output_evidence",
                    decision=GateDecision.DEFER,
                    reason="Real run evidence is missing a primary output artifact.",
                    evidence={"run_id": bundle.run_id},
                )
            )

        if bundle.execution_mode == "real_run" and not bundle.run.diagnostic_files and not bundle.run.reference_files:
            incomplete = True
            gates.append(
                GateResult(
                    gate="diagnostic_or_reference_evidence",
                    decision=GateDecision.DEFER,
                    reason="Real run evidence is missing diagnostics or reference artifacts.",
                    evidence={"run_id": bundle.run_id},
                )
            )

        if bundle.execution_mode == "real_run" and bundle.summary is None:
            warnings.append(
                JediEvidenceWarning(
                    code="diagnostics_summary_missing",
                    message="Real run evidence bundle does not include a diagnostics summary.",
                    severity="info",
                    evidence={"run_id": bundle.run_id},
                )
            )
        elif bundle.execution_mode == "real_run":
            diagnostics_summary = bundle.summary
            has_structured_signal = bool(
                diagnostics_summary.files_scanned
                or diagnostics_summary.ioda_groups_found
                or diagnostics_summary.gradient_norm_reduction is not None
                or diagnostics_summary.observer_output_detected
                or diagnostics_summary.posterior_output_detected
            )
            if not has_structured_signal:
                incomplete = True
                gates.append(
                    GateResult(
                        gate="diagnostics_structured_signal",
                        decision=GateDecision.DEFER,
                        reason="Diagnostics summary is present but does not contain structured diagnostics evidence.",
                        evidence={"run_id": bundle.run_id},
                    )
                )
            else:
                gates.append(
                    GateResult(
                        gate="diagnostics_structured_signal",
                        decision=GateDecision.ALLOW,
                        reason="Diagnostics summary provides structured evidence for downstream review.",
                        evidence={
                            "run_id": bundle.run_id,
                            "files_scanned": len(diagnostics_summary.files_scanned),
                            "ioda_groups_found": list(diagnostics_summary.ioda_groups_found),
                            "ioda_groups_missing": list(diagnostics_summary.ioda_groups_missing),
                            "minimizer_iterations": diagnostics_summary.minimizer_iterations,
                            "outer_iterations": diagnostics_summary.outer_iterations,
                            "inner_iterations": diagnostics_summary.inner_iterations,
                            "initial_cost_function": diagnostics_summary.initial_cost_function,
                            "final_cost_function": diagnostics_summary.final_cost_function,
                            "initial_gradient_norm": diagnostics_summary.initial_gradient_norm,
                            "final_gradient_norm": diagnostics_summary.final_gradient_norm,
                            "gradient_norm_reduction": diagnostics_summary.gradient_norm_reduction,
                            "observer_output_detected": diagnostics_summary.observer_output_detected,
                            "posterior_output_detected": diagnostics_summary.posterior_output_detected,
                        },
                    )
                )

        if validation.blocking_reasons:
            warnings.append(
                JediEvidenceWarning(
                    code="blocking_reasons_present",
                    message="Validation report includes blocking reasons for downstream review.",
                    evidence={"run_id": bundle.run_id, "blocking_reasons": validation.blocking_reasons},
                )
            )

        if validation.provenance_refs or validation.checkpoint_refs:
            warnings.append(
                JediEvidenceWarning(
                    code="handoff_refs_present",
                    message="Validation report already carries provenance/checkpoint handoff references.",
                    severity="info",
                    evidence={
                        "run_id": bundle.run_id,
                        "provenance_refs": validation.provenance_refs,
                        "checkpoint_refs": validation.checkpoint_refs,
                    },
                )
            )

        if incomplete:
            return JediPolicyReport(
                passed=False,
                decision="defer",
                reason="Evidence bundle is incomplete for downstream review.",
                warnings=warnings,
                gates=gates,
                evidence=self._report_evidence(bundle, validation.status),
            )

        gates.append(
            GateResult(
                gate="evidence_ready",
                decision=GateDecision.ALLOW,
                reason="Evidence bundle is complete enough for downstream consumption.",
                evidence=self._report_evidence(bundle, validation.status),
            )
        )
        return JediPolicyReport(
            passed=True,
            decision="allow",
            reason="Evidence bundle is complete enough for downstream consumption.",
            warnings=warnings,
            gates=gates,
            evidence=self._report_evidence(bundle, validation.status),
        )
