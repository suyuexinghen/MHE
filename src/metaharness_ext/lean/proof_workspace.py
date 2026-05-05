from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.lean.capabilities import CAP_LEAN_PREPARE_WORKSPACE
from metaharness_ext.lean.contracts import LeanBlueprintItem, LeanRunArtifact, LeanRunPlan
from metaharness_ext.lean.slots import LEAN_PROOF_WORKSPACE_SLOT


class LeanProofWorkspaceComponent(HarnessComponent):
    def __init__(self, workspace_root: str | None = None) -> None:
        self._workspace_root = Path(workspace_root) if workspace_root else None

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(LEAN_PROOF_WORKSPACE_SLOT)
        api.declare_input("blueprint", "LeanBlueprint")
        api.declare_output("plan", "LeanRunPlan", mode="sync")
        api.provide_capability(CAP_LEAN_PREPARE_WORKSPACE)

    def prepare(self, item: LeanBlueprintItem) -> LeanRunPlan:
        original = Path(item.file)
        workspace_dir = Path(
            tempfile.mkdtemp(
                prefix="mhe-lean-", dir=str(self._workspace_root) if self._workspace_root else None
            )
        )
        workspace_file = workspace_dir / original.name
        imports = self.extract_environment(original)
        workspace_file.write_text(
            "\n".join([*imports, f"theorem {item.lean_declaration} := by", "  sorry", ""])
        )
        return LeanRunPlan(
            plan_id=f"plan:{item.label}",
            task_ref=item.label,
            target_file=str(workspace_file),
            workspace_path=str(workspace_file),
            execution_params={
                "original_file": str(original),
                "original_hash": self._hash_file(original),
                "lean_declaration": item.lean_declaration,
                "attempts": item.attempts,
                "budget": item.budget,
                "lock_key": hashlib.sha256(str(original.resolve()).encode()).hexdigest(),
            },
        )

    def delegate_to_subagent(self, item: LeanBlueprintItem) -> LeanRunPlan:
        plan = self.prepare(item)
        plan.execution_params["delegated"] = True
        return plan

    def collect_from_subagent(self, artifact: LeanRunArtifact) -> LeanRunArtifact:
        if artifact.exit_code != 0:
            raise RuntimeError("Sub-agent Lean artifact did not validate cleanly")
        return artifact

    def extract_environment(self, target: str | Path) -> list[str]:
        path = Path(target)
        if not path.exists():
            return []
        return [line for line in path.read_text().splitlines() if line.startswith("import ")]

    def can_resume(self, plan: LeanRunPlan) -> bool:
        workspace_path = Path(plan.workspace_path or "")
        original_path = Path(plan.execution_params.get("original_file", ""))
        expected_hash = plan.execution_params.get("original_hash")
        return (
            workspace_path.exists()
            and original_path.exists()
            and expected_hash == self._hash_file(original_path)
        )

    def restore(self, plan: LeanRunPlan, proven_code: str) -> None:
        original_path = Path(plan.execution_params["original_file"])
        expected_hash = plan.execution_params.get("original_hash")
        if expected_hash != self._hash_file(original_path):
            raise RuntimeError("Original Lean file changed since workspace preparation")
        original_path.write_text(proven_code)

    def _hash_file(self, path: Path) -> str | None:
        if not path.exists():
            return None
        return hashlib.sha256(path.read_bytes()).hexdigest()
