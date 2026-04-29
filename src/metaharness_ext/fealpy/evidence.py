from __future__ import annotations

from metaharness_ext.fealpy.contracts import (
    FealpyEnvironmentReport,
    FealpyEvidenceBundle,
    FealpyEvidenceWarning,
    FealpyRunArtifact,
    FealpyRunPlan,
    FealpyValidationReport,
)


def build_evidence_bundle(
    run: FealpyRunArtifact,
    validation: FealpyValidationReport | None = None,
    environment: FealpyEnvironmentReport | None = None,
    plan: FealpyRunPlan | None = None,
) -> FealpyEvidenceBundle:
    evidence_refs = list(
        dict.fromkeys(
            [
                f"fealpy://run/{run.task_id}/{run.run_id}",
                f"fealpy://artifact/{run.artifact_id}",
                *(plan.evidence_refs if plan is not None else []),
                *run.evidence_refs,
                *(validation.evidence_refs if validation is not None else []),
                *(environment.evidence_refs if environment is not None else []),
            ]
        )
    )

    warnings: list[FealpyEvidenceWarning] = []
    if validation is None:
        warnings.append(
            FealpyEvidenceWarning(
                code="validation_missing",
                message="Evidence bundle does not include a validation report.",
                evidence={"run_id": run.run_id},
            )
        )
    if environment is not None:
        for prereq in environment.missing_prerequisites:
            warnings.append(
                FealpyEvidenceWarning(
                    code="environment_prerequisite_error",
                    message=f"Environment prerequisite missing: {prereq}.",
                    evidence={"task_id": run.task_id, "prerequisite": prereq},
                )
            )

    return FealpyEvidenceBundle(
        bundle_id=f"fealpy-{run.task_id}-{run.run_id}",
        task_id=run.task_id,
        run_id=run.run_id,
        plan_ref=plan.plan_id if plan is not None else run.plan_ref,
        artifact_ref=run.artifact_id,
        validation_ref=(
            f"fealpy://validation/{validation.task_id}/{validation.artifact_ref}"
            if validation is not None
            else None
        ),
        environment=environment,
        plan=plan,
        artifact=run,
        validation=validation,
        evidence_refs=evidence_refs,
        warnings=warnings,
        provenance={
            "task_id": run.task_id,
            "run_id": run.run_id,
            "plan_ref": run.plan_ref,
            "artifact_id": run.artifact_id,
            "validation_status": validation.status.value if validation is not None else None,
        },
        metadata={
            "run_status": run.status,
            "validation_status": validation.status.value if validation is not None else None,
            "environment_status": environment.status if environment is not None else None,
        },
    )
