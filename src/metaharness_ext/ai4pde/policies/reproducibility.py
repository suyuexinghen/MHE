from __future__ import annotations

from metaharness_ext.ai4pde.contracts import ValidationBundle


def check_reproducibility(validation_bundle: ValidationBundle) -> dict[str, float | bool]:
    residual = float(validation_bundle.residual_metrics.get("residual_l2", 1.0))
    boundary = float(validation_bundle.bc_ic_metrics.get("boundary_error", 1.0))
    score = max(0.0, 1.0 - residual - boundary)
    return {
        "score": score,
        "meets_threshold": score >= 0.9,
    }
