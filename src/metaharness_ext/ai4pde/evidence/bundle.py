from __future__ import annotations

from typing import Any

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
    return ScientificEvidenceBundle(
        bundle_id=f"bundle-{run_artifact.task_id}",
        task_id=run_artifact.task_id,
        graph_version_id=validation.graph_version_id,
        solver_config={"solver_family": run_artifact.solver_family.value},
        validation_summary=validation.summary,
        artifact_hashes=[f"sha256:{run_artifact.task_id}"],
        checkpoint_refs=run_artifact.checkpoint_refs,
        provenance_refs=[f"provenance://{run_artifact.task_id}"],
        reference_comparison_refs=reference_comparison_refs,
        benchmark_snapshot_refs=benchmark_snapshot_refs,
        baseline_metadata=baseline_metadata,
        graph_metadata=graph_metadata or {},
    )
