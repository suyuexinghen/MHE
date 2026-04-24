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
        metadata={
            "status": run.status,
            "return_code": run.return_code,
            "validation_status": validation.status if validation is not None else None,
            "policy_decision": validation.policy_decision if validation is not None else None,
        },
    )
