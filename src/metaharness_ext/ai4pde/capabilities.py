from __future__ import annotations

CAP_PINN_STRONG = "ai4pde.solver.pinn_strong"
CAP_REFERENCE_BASELINE = "ai4pde.solver.reference_baseline"
CAP_RESIDUAL_VALIDATION = "ai4pde.validation.residual"
CAP_BOUNDARY_VALIDATION = "ai4pde.validation.boundary"
CAP_EVIDENCE_BUNDLING = "ai4pde.evidence.bundle"

CANONICAL_CAPABILITIES = frozenset(
    {
        CAP_PINN_STRONG,
        CAP_REFERENCE_BASELINE,
        CAP_RESIDUAL_VALIDATION,
        CAP_BOUNDARY_VALIDATION,
        CAP_EVIDENCE_BUNDLING,
    }
)
