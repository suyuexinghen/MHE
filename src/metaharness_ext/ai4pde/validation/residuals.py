from __future__ import annotations

from metaharness_ext.ai4pde.contracts import PDERunArtifact


def summarize_residuals(run_artifact: PDERunArtifact) -> dict[str, float]:
    residual_l2 = float(run_artifact.result_summary.get("residual_l2", 1.0))
    return {"residual_l2": residual_l2, "residual_ok": float(residual_l2 <= 0.05)}
