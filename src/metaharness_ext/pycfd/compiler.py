from __future__ import annotations

import hashlib
import json

from metaharness_ext.pycfd.contracts import PyCFDProblemSpec, PyCFDRunPlan
from metaharness_ext.pycfd.types import PyCFDCaseType

_TEMPLATE_HEADER = '''"""Auto-generated PyCFD solver script — MHE PyCFD Compiler."""
import json, os, sys, time

_pycfd_src = {pycfd_src!r}
if _pycfd_src not in sys.path:
    sys.path.insert(0, _pycfd_src)

from Solvers import Solvers, run_pycfd_case  # noqa: E402

_config = {config_json}

if __name__ == "__main__":
    _result = run_pycfd_case(_config)
'''

_CASE_DEFAULTS: dict[PyCFDCaseType, dict] = {
    "vortex": {
        "mesh_xb": -10.0,
        "mesh_xe": 10.0,
        "mesh_yb": -10.0,
        "mesh_ye": 10.0,
        "M_inf": 0.3,
        "t_final": 1.0,
        "dt": 0.01,
        "flowtype": "vortex",
    },
    "airfoil": {
        "mesh_xb": -5.0,
        "mesh_xe": 15.0,
        "mesh_yb": -5.0,
        "mesh_ye": 5.0,
        "M_inf": 0.80,
        "aoa": 1.25,
        "t_final": 100.0,
        "dt": 0.1,
        "flowtype": "freestream",
    },
    "cylinder": {
        "mesh_xb": -10.0,
        "mesh_xe": 20.0,
        "mesh_yb": -10.0,
        "mesh_ye": 10.0,
        "M_inf": 0.3,
        "t_final": 100.0,
        "dt": 0.1,
        "flowtype": "freestream",
    },
    "mms": {
        "mesh_xb": -1.0,
        "mesh_xe": 1.0,
        "mesh_yb": -1.0,
        "mesh_ye": 1.0,
        "M_inf": 0.3,
        "t_final": 1.0,
        "dt": 0.01,
        "flowtype": "mms",
        "compute_te_mms": True,
    },
    "shock_diffraction": {
        "mesh_xb": 0.0,
        "mesh_xe": 1.0,
        "mesh_yb": 0.0,
        "mesh_ye": 1.0,
        "M_inf": 5.09,
        "t_final": 0.7,
        "dt": 0.01,
        "flowtype": "shock-diffraction",
    },
}


class PyCFDCompilerComponent:
    """Compiles a PyCFDProblemSpec into a self-contained solver script."""

    def __init__(self, pycfd_src_path: str | None = None):
        self._pycfd_src_path = pycfd_src_path

    def _resolve_src_path(self) -> str:
        if self._pycfd_src_path:
            return self._pycfd_src_path
        import os

        return os.environ.get("PYCFD_SRC_PATH", ".")

    @staticmethod
    def _build_plan_id(spec: PyCFDProblemSpec) -> str:
        payload = spec.model_dump_json(
            exclude={"promotion_metadata", "graph_metadata", "evidence_refs"}
        )
        return hashlib.sha256(payload.encode()).hexdigest()[:16]

    def compile(self, spec: PyCFDProblemSpec, run_id: str, workspace_dir: str) -> PyCFDRunPlan:
        plan_id = self._build_plan_id(spec)
        script_source = self._render_script(spec)
        return PyCFDRunPlan(
            plan_id=plan_id,
            task_id=spec.task_id,
            run_id=run_id,
            spec=spec,
            workspace_dir=str(workspace_dir),
            script_source=script_source,
        )

    def _render_script(self, spec: PyCFDProblemSpec) -> str:
        config = self._build_config(spec)
        pycfd_src = self._resolve_src_path()
        config_json = json.dumps(config, indent=2)
        return _TEMPLATE_HEADER.format(pycfd_src=pycfd_src, config_json=config_json)

    def _build_config(self, spec: PyCFDProblemSpec) -> dict:
        config: dict = {
            "case_type": spec.case_type,
            "project_name": spec.task_id.replace("-", "_"),
            "mesh_type": spec.mesh.mesh_type,
            "mesh_nx": spec.mesh.nx,
            "mesh_ny": spec.mesh.ny,
            "mesh_xb": spec.mesh.xb,
            "mesh_xe": spec.mesh.xe,
            "mesh_yb": spec.mesh.yb,
            "mesh_ye": spec.mesh.ye,
            "M_inf": spec.flow.M_inf,
            "aoa": spec.flow.aoa,
            "gamma": spec.flow.gamma,
            "rho_inf": spec.flow.rho_inf,
            "CFL": spec.solver.CFL,
            "second_order": spec.solver.second_order,
            "use_limiter": spec.solver.use_limiter,
            "inviscid_flux": spec.solver.inviscid_flux,
            "eig_limiting_factor": spec.solver.eig_limiting_factor,
            "t_final": spec.t_final,
            "dt": spec.dt,
            "solver_type": spec.solver_type,
            "flowtype": spec.flowtype,
            "max_steps": spec.solver.max_steps,
        }
        if spec.case_type == "mms":
            config["compute_te_mms"] = True
        if spec.flow.p_inf is not None:
            config["p_inf"] = spec.flow.p_inf
        return config
