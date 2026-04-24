from __future__ import annotations

from metaharness_ext.jedi.contracts import (
    JediDiagnosticSummary,
    JediEvidenceBundle,
    JediEvidenceWarning,
    JediRunArtifact,
    JediValidationReport,
)


def build_evidence_bundle(
    run: JediRunArtifact,
    validation: JediValidationReport | None = None,
    summary: JediDiagnosticSummary | None = None,
) -> JediEvidenceBundle:
    evidence_files = list(
        dict.fromkeys(
            [
                *(validation.evidence_files if validation is not None else []),
                run.config_path,
                run.stdout_path,
                run.stderr_path,
                run.schema_path,
                *run.prepared_inputs,
                *run.output_files,
                *run.diagnostic_files,
                *run.reference_files,
                *(summary.files_scanned if summary is not None else []),
            ]
        )
    )
    evidence_files = [path for path in evidence_files if path]

    warnings: list[JediEvidenceWarning] = []
    if not run.stdout_path:
        warnings.append(
            JediEvidenceWarning(
                code="stdout_missing",
                message="Run artifact does not include a stdout log path.",
                evidence={"run_id": run.run_id},
            )
        )
    if not run.stderr_path:
        warnings.append(
            JediEvidenceWarning(
                code="stderr_missing",
                message="Run artifact does not include a stderr log path.",
                evidence={"run_id": run.run_id},
            )
        )
    if run.execution_mode == "real_run" and not run.output_files:
        warnings.append(
            JediEvidenceWarning(
                code="primary_output_missing",
                message="Real run is missing a primary output artifact.",
                evidence={"run_id": run.run_id, "execution_mode": run.execution_mode},
            )
        )
    if run.execution_mode == "real_run" and not run.diagnostic_files and not run.reference_files:
        warnings.append(
            JediEvidenceWarning(
                code="runtime_evidence_incomplete",
                message="Real run is missing diagnostics or reference evidence.",
                evidence={"run_id": run.run_id, "execution_mode": run.execution_mode},
            )
        )

    return JediEvidenceBundle(
        task_id=run.task_id,
        run_id=run.run_id,
        application_family=run.application_family,
        execution_mode=run.execution_mode,
        run=run,
        validation=validation,
        summary=summary,
        evidence_files=evidence_files,
        warnings=warnings,
        candidate_id=(validation.candidate_id if validation is not None else None) or run.run_id,
        graph_version_id=validation.graph_version_id if validation is not None else None,
        session_id=(validation.session_id if validation is not None else None) or run.task_id,
        session_events=list(validation.session_events) if validation is not None else [],
        audit_refs=list(validation.audit_refs) if validation is not None else [],
        metadata={
            "status": run.status,
            "return_code": run.return_code,
            "validation_status": validation.status if validation is not None else None,
            "policy_decision": validation.policy_decision if validation is not None else None,
            "diagnostics_present": summary is not None,
            "diagnostic_files_scanned": len(summary.files_scanned) if summary is not None else 0,
            "ioda_groups_found": list(summary.ioda_groups_found) if summary is not None else [],
            "ioda_groups_missing": list(summary.ioda_groups_missing) if summary is not None else [],
            "minimizer_iterations": (
                summary.minimizer_iterations if summary is not None else None
            ),
            "outer_iterations": summary.outer_iterations if summary is not None else None,
            "inner_iterations": summary.inner_iterations if summary is not None else None,
            "initial_cost_function": (
                summary.initial_cost_function if summary is not None else None
            ),
            "final_cost_function": summary.final_cost_function if summary is not None else None,
            "initial_gradient_norm": (
                summary.initial_gradient_norm if summary is not None else None
            ),
            "final_gradient_norm": summary.final_gradient_norm if summary is not None else None,
            "gradient_norm_reduction": (
                summary.gradient_norm_reduction if summary is not None else None
            ),
            "observer_output_detected": (
                summary.observer_output_detected if summary is not None else False
            ),
            "posterior_output_detected": (
                summary.posterior_output_detected if summary is not None else False
            ),
        },
    )
