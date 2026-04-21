from __future__ import annotations

from metaharness_ext.ai4pde.contracts import PDERunArtifact


def summarize_boundary_conditions(run_artifact: PDERunArtifact) -> dict[str, float]:
    boundary_error = float(run_artifact.result_summary.get("boundary_error", 1.0))
    return {"boundary_error": boundary_error, "boundary_ok": float(boundary_error <= 0.01)}
