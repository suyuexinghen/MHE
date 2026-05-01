from __future__ import annotations

import os
import uuid
from pathlib import Path

from metaharness_ext.pycfd.benchmark_cases import pycfd_case_catalog
from metaharness_ext.pycfd.compiler import PyCFDCompilerComponent
from metaharness_ext.pycfd.contracts import (
    PyCFDProblemSpec,
)
from metaharness_ext.pycfd.environment import PyCFDEnvironmentProbeComponent
from metaharness_ext.pycfd.evidence import build_evidence_bundle
from metaharness_ext.pycfd.executor import PyCFDExecutorComponent
from metaharness_ext.pycfd.policy import PyCFDEvidencePolicy
from metaharness_ext.pycfd.validator import PyCFDValidatorComponent


class PyCFDBenchmarkRunner:
    """Three-lane benchmark comparing PyCFD approaches.

    Lanes:
    - extension: full MHE pipeline (compile -> execute -> validate -> evidence -> policy)
    - direct: Claude generates a raw script, runs via subprocess
    - agent: Claude proposes a spec, routed through extension pipeline
    """

    def __init__(
        self,
        pycfd_src_path: str | None = None,
        workspace_root: str = ".runs/pycfd-benchmarks",
        allow_real_tools: bool = False,
    ):
        self._pycfd_src_path = pycfd_src_path or os.environ.get("PYCFD_SRC_PATH", ".")
        self._workspace = Path(workspace_root)
        self._workspace.mkdir(parents=True, exist_ok=True)
        self._allow_real = allow_real_tools
        self._compiler = PyCFDCompilerComponent(pycfd_src_path=self._pycfd_src_path)
        self._executor = PyCFDExecutorComponent(workspace_root=workspace_root)
        self._validator = PyCFDValidatorComponent()
        self._policy = PyCFDEvidencePolicy()
        self._env_probe = PyCFDEnvironmentProbeComponent(pycfd_src_path=self._pycfd_src_path)

    def run_all_cases(
        self, case_ids: list[str] | None = None, lanes: list[str] | None = None
    ) -> list[dict]:
        """Run all (or selected) cases across all (or selected) lanes."""
        catalog = pycfd_case_catalog()
        if case_ids:
            catalog = {k: v for k, v in catalog.items() if k in case_ids}

        lanes = lanes or ["extension", "direct", "agent"]
        results: list[dict] = []

        for case_id, spec in catalog.items():
            for lane in lanes:
                result = self.run_case(case_id, spec, lane)
                results.append(result)

        return results

    def run_case(self, case_id: str, spec: PyCFDProblemSpec, lane: str) -> dict:
        run_id = f"pycfd-bm-{case_id}-{lane}-{uuid.uuid4().hex[:8]}"

        if lane == "extension":
            return self._run_extension_lane(case_id, spec, run_id)
        elif lane == "direct":
            return self._run_direct_lane(case_id, spec, run_id)
        elif lane == "agent":
            return self._run_agent_lane(case_id, spec, run_id)
        else:
            return {
                "case_id": case_id,
                "lane": lane,
                "run_id": run_id,
                "status": "unknown_lane",
                "error": f"Unknown lane: {lane}",
            }

    def _run_extension_lane(self, case_id: str, spec: PyCFDProblemSpec, run_id: str) -> dict:
        """Full MHE extension pipeline."""
        if not self._allow_real:
            return self._dry_run_result(case_id, "extension", run_id, "dry_run")

        env = self._env_probe.probe(task_id=f"env-{case_id}")
        if not env.available:
            return {
                "case_id": case_id,
                "lane": "extension",
                "run_id": run_id,
                "status": "environment_unavailable",
                "error": "PyCFD environment not available.",
            }

        try:
            plan = self._compiler.compile(
                spec, run_id=run_id, workspace_dir=str(self._workspace / run_id)
            )
            artifact = self._executor.execute(plan)
            validation = self._validator.validate(artifact, plan_ref=plan.plan_id)
            evidence = build_evidence_bundle(
                task_id=case_id,
                environment=env,
                plan=plan,
                artifact=artifact,
                validation=validation,
            )
            policy = self._policy.evaluate(evidence)

            return {
                "case_id": case_id,
                "lane": "extension",
                "run_id": run_id,
                "status": artifact.status,
                "residual_l1": artifact.residual_l1,
                "residual_l2": artifact.residual_l2,
                "wall_time_seconds": artifact.wall_time_seconds,
                "validation_passed": validation.passed,
                "policy_decision": policy.decision,
            }
        except Exception as e:
            return {
                "case_id": case_id,
                "lane": "extension",
                "run_id": run_id,
                "status": "error",
                "error": str(e),
            }

    def _run_direct_lane(self, case_id: str, spec: PyCFDProblemSpec, run_id: str) -> dict:
        """Direct lane: Claude generates a raw script (placeholder for now)."""
        return {
            "case_id": case_id,
            "lane": "direct",
            "run_id": run_id,
            "status": "not_implemented",
            "note": "Direct lane requires Claude CLI integration — placeholder.",
        }

    def _run_agent_lane(self, case_id: str, spec: PyCFDProblemSpec, run_id: str) -> dict:
        """Agent lane: Claude proposes spec modifications (placeholder for now)."""
        return {
            "case_id": case_id,
            "lane": "agent",
            "run_id": run_id,
            "status": "not_implemented",
            "note": "Agent lane requires Claude CLI brain provider — placeholder.",
        }

    def _dry_run_result(self, case_id: str, lane: str, run_id: str, status: str) -> dict:
        return {
            "case_id": case_id,
            "lane": lane,
            "run_id": run_id,
            "status": status,
            "residual_l1": None,
            "residual_l2": None,
            "wall_time_seconds": None,
            "validation_passed": None,
            "policy_decision": None,
        }
