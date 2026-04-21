from __future__ import annotations

from metaharness_ext.ai4pde.contracts import (
    PDERunArtifact,
    ScientificEvidenceBundle,
    ValidationBundle,
)


def run_candidate_benchmark(
    *,
    active_run: PDERunArtifact,
    candidate_run: PDERunArtifact,
    validation_bundle: ValidationBundle,
    evidence_bundle: ScientificEvidenceBundle,
) -> dict[str, object]:
    active_residual = float(active_run.result_summary.get("residual_l2", 1.0))
    candidate_residual = float(candidate_run.result_summary.get("residual_l2", 1.0))
    improved = candidate_residual <= active_residual
    return {
        "active_run_id": active_run.run_id,
        "candidate_run_id": candidate_run.run_id,
        "active_residual_l2": active_residual,
        "candidate_residual_l2": candidate_residual,
        "improved": improved,
        "evaluation_snapshot": f"evaluation://{candidate_run.task_id}/{candidate_run.run_id}",
        "graph_family": evidence_bundle.graph_metadata.get("graph_family", validation_bundle.summary.get("status", "unknown")),
    }
