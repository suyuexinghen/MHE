from __future__ import annotations

from pathlib import Path

from metaharness_ext.octave.contracts import (
    OctaveEnvironmentReport,
    OctaveEvidenceBundle,
    OctaveEvidenceWarning,
    OctaveRunArtifact,
    OctaveRunPlan,
    OctaveValidationReport,
)


def build_evidence_bundle(
    run: OctaveRunArtifact,
    validation: OctaveValidationReport | None = None,
    environment: OctaveEnvironmentReport | None = None,
    plan: OctaveRunPlan | None = None,
) -> OctaveEvidenceBundle:
    evidence_files = list(
        dict.fromkeys(
            [
                *(validation.evidence_files if validation is not None else []),
                *run.wrapper_files,
                *run.input_files,
                *run.output_files,
                *run.figure_files,
                *run.log_files,
                *([run.stdout_path] if run.stdout_path else []),
                *([run.stderr_path] if run.stderr_path else []),
                *([run.status_path] if run.status_path else []),
            ]
        )
    )
    scored_evidence = validation.scored_evidence if validation is not None else run.scored_evidence
    evidence_refs = list(
        dict.fromkeys(
            [
                f"octave://run/{run.task_id}/{run.run_id}",
                f"octave://artifact/{run.artifact_id}",
                *(plan.evidence_refs if plan is not None else []),
                *run.evidence_refs,
                *(validation.evidence_refs if validation is not None else []),
                *(environment.evidence_refs if environment is not None else []),
                *([] if scored_evidence is None else scored_evidence.evidence_refs),
                *(f"octave://file/{Path(path).name}" for path in evidence_files),
            ]
        )
    )
    warnings: list[OctaveEvidenceWarning] = []
    if run.stdout_path is None:
        warnings.append(
            OctaveEvidenceWarning(
                code="stdout_missing",
                message="Run artifact does not include stdout evidence.",
                evidence={"run_id": run.run_id},
            )
        )
    if run.stderr_path is None:
        warnings.append(
            OctaveEvidenceWarning(
                code="stderr_missing",
                message="Run artifact does not include stderr evidence.",
                evidence={"run_id": run.run_id},
            )
        )
    if validation is None:
        warnings.append(
            OctaveEvidenceWarning(
                code="validation_missing",
                message="Evidence bundle does not include a validation report.",
                evidence={"run_id": run.run_id},
            )
        )
    if environment is not None:
        for prerequisite in environment.prerequisite_errors:
            warnings.append(
                OctaveEvidenceWarning(
                    code="environment_prerequisite_error",
                    message=f"Environment prerequisite error: {prerequisite}.",
                    evidence={"task_id": run.task_id, "prerequisite": prerequisite},
                )
            )
        for package in environment.missing_packages:
            warnings.append(
                OctaveEvidenceWarning(
                    code="package_missing",
                    message=f"Required Octave package is missing: {package}.",
                    evidence={"task_id": run.task_id, "package": package},
                )
            )

    return OctaveEvidenceBundle(
        bundle_id=f"octave-{run.task_id}-{run.run_id}",
        task_id=run.task_id,
        run_id=run.run_id,
        plan_ref=plan.plan_id if plan is not None else run.plan_ref,
        artifact_ref=run.artifact_id,
        validation_ref=(
            f"octave://validation/{validation.task_id}/{validation.artifact_ref}"
            if validation is not None
            else None
        ),
        environment=environment,
        plan=plan,
        artifact=run,
        validation=validation,
        evidence_files=evidence_files,
        evidence_refs=evidence_refs,
        warnings=warnings,
        scored_evidence=scored_evidence,
        governance_state=validation.governance_state if validation is not None else "defer",
        provenance={
            "task_id": run.task_id,
            "run_id": run.run_id,
            "plan_ref": run.plan_ref,
            "artifact_id": run.artifact_id,
            "validation_status": validation.status.value if validation is not None else None,
        },
        metadata={
            "run_status": run.status,
            "return_code": run.return_code,
            "validation_status": validation.status.value if validation is not None else None,
            "governance_state": validation.governance_state if validation is not None else None,
            "environment_status": environment.status if environment is not None else None,
        },
    )
