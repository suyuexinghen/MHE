from __future__ import annotations

from typing import Any

from metaharness.core.models import ScoredEvidence
from metaharness_ext.ai4pde.contracts import (
    PDERunArtifact,
    ReferenceResult,
    ScientificEvidenceBundle,
    ValidationBundle,
)


def build_evidence_bundle(
    run_artifact: PDERunArtifact,
    validation: ValidationBundle,
    *,
    graph_metadata: dict[str, Any] | None = None,
    reference_result: ReferenceResult | None = None,
) -> ScientificEvidenceBundle:
    benchmark_snapshot_refs = (
        list(reference_result.benchmark_snapshot_refs) if reference_result is not None else []
    )
    baseline_metadata = reference_result.summary if reference_result is not None else {}
    reference_comparison_refs = (
        [f"reference://{reference_result.reference_id}"] if reference_result is not None else []
    )
    scored_evidence = validation.scored_evidence or ScoredEvidence(
        score=0.0,
        evidence_refs=[f"validation://{validation.validation_id}"],
    )
    provenance_refs = list(
        dict.fromkeys(
            [
                *validation.telemetry_refs,
                *([f"provenance://{run_artifact.task_id}"] if not validation.provenance else []),
                *scored_evidence.evidence_refs,
            ]
        )
    )
    if validation.provenance:
        provenance_refs.append(f"provenance://ai4pde/validation/{run_artifact.task_id}")
    return ScientificEvidenceBundle(
        bundle_id=f"bundle-{run_artifact.task_id}",
        task_id=run_artifact.task_id,
        graph_version_id=validation.graph_version_id,
        solver_config={"solver_family": run_artifact.solver_family.value},
        validation_summary=validation.summary,
        artifact_hashes=[f"sha256:{run_artifact.task_id}"],
        checkpoint_refs=run_artifact.checkpoint_refs,
        provenance_refs=list(dict.fromkeys(provenance_refs)),
        reference_comparison_refs=reference_comparison_refs,
        benchmark_snapshot_refs=benchmark_snapshot_refs,
        baseline_metadata=baseline_metadata,
        graph_metadata=graph_metadata or {},
        promotion_metadata=validation.promotion_metadata,
        candidate_identity=validation.candidate_identity,
        safety_evaluation=validation.safety_evaluation,
        rollback_context=validation.rollback_context,
        scored_evidence=scored_evidence,
        session_events=list(validation.session_events),
        provenance={
            **dict(validation.provenance),
            "validation_bundle": validation.model_dump(mode="json"),
        },
    )
