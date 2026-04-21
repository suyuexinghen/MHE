from __future__ import annotations

CAP_NEKTAR_CASE_COMPILE = "nektar.compile.case"
CAP_NEKTAR_MESH_PREPARE = "nektar.mesh.prepare"
CAP_NEKTAR_SOLVE_ADR = "nektar.solver.adr"
CAP_NEKTAR_SOLVE_INCNS = "nektar.solver.incns"
CAP_NEKTAR_POSTPROCESS = "nektar.postprocess.fieldconvert"
CAP_NEKTAR_VALIDATE = "nektar.validation.check"
CAP_NEKTAR_CONVERGENCE_STUDY = "nektar.study.convergence"

CANONICAL_CAPABILITIES = frozenset(
    {
        CAP_NEKTAR_CASE_COMPILE,
        CAP_NEKTAR_MESH_PREPARE,
        CAP_NEKTAR_SOLVE_ADR,
        CAP_NEKTAR_SOLVE_INCNS,
        CAP_NEKTAR_POSTPROCESS,
        CAP_NEKTAR_VALIDATE,
        CAP_NEKTAR_CONVERGENCE_STUDY,
    }
)
