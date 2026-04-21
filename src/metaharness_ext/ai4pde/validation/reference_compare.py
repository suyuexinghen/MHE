from __future__ import annotations

from metaharness_ext.ai4pde.contracts import PDERunArtifact, ReferenceResult


def compare_against_reference(
    run_artifact: PDERunArtifact,
    reference_result: ReferenceResult,
) -> dict[str, float | str]:
    candidate_residual = float(run_artifact.result_summary.get("residual_l2", 1.0))
    baseline_residual = float(reference_result.summary.get("residual_l2", 1.0))
    divergence = candidate_residual - baseline_residual
    return {
        "candidate_residual_l2": candidate_residual,
        "baseline_residual_l2": baseline_residual,
        "divergence": divergence,
        "status": "better_or_equal" if divergence <= 0 else "worse_than_baseline",
    }
