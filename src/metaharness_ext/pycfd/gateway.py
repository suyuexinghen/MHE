from __future__ import annotations

import uuid

from metaharness_ext.pycfd.contracts import PyCFDProblemSpec
from metaharness_ext.pycfd.types import PyCFDCaseType

_VALID_CASE_TYPES: frozenset[str] = frozenset(
    {
        "vortex",
        "airfoil",
        "cylinder",
        "mms",
        "shock_diffraction",
    }
)


class PyCFDGatewayComponent:
    """Task intake gateway for PyCFD. Validates case types and issues task specs."""

    def issue_task(
        self, task_id: str, case_type: PyCFDCaseType = "vortex", overrides: dict | None = None
    ) -> PyCFDProblemSpec:
        if case_type not in _VALID_CASE_TYPES:
            raise ValueError(f"Unknown case_type '{case_type}'. Valid: {sorted(_VALID_CASE_TYPES)}")

        spec = PyCFDProblemSpec(task_id=task_id, case_type=case_type)
        if overrides:
            for key, value in overrides.items():
                if hasattr(spec, key):
                    setattr(spec, key, value)
                elif "." in key:
                    # Dotted path for nested models
                    parts = key.split(".")
                    obj = spec
                    for part in parts[:-1]:
                        obj = getattr(obj, part)
                    setattr(obj, parts[-1], value)
        return spec

    def compile_experiment(
        self,
        spec: PyCFDProblemSpec,
        compiler,
        run_id: str | None = None,
        workspace_dir: str = ".runs/pycfd",
    ):
        """Shorthand: issue -> compile."""
        if run_id is None:
            run_id = f"pycfd-run-{uuid.uuid4().hex[:12]}"
        return compiler.compile(spec, run_id=run_id, workspace_dir=workspace_dir)

    def run_baseline(
        self,
        spec: PyCFDProblemSpec,
        compiler,
        executor,
        run_id: str | None = None,
        workspace_dir: str = ".runs/pycfd",
    ):
        """Shorthand: issue -> compile -> execute."""
        plan = self.compile_experiment(spec, compiler, run_id=run_id, workspace_dir=workspace_dir)
        artifact = executor.execute(plan)
        return plan, artifact
