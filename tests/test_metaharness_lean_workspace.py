from __future__ import annotations

import pytest

from metaharness_ext.lean.contracts import LeanBlueprintItem, LeanRunArtifact
from metaharness_ext.lean.proof_workspace import LeanProofWorkspaceComponent


def test_workspace_prepare_extracts_imports(tmp_path) -> None:
    source = tmp_path / "Main.lean"
    source.write_text("import Mathlib\n\ntheorem main : True := by\n  trivial\n")
    item = LeanBlueprintItem(
        label="main",
        lean_declaration="main",
        file=str(source),
        attempts=1,
        budget=3,
    )

    plan = LeanProofWorkspaceComponent(str(tmp_path)).prepare(item)

    workspace = tmp_path / plan.workspace_path
    assert workspace.exists()
    assert "import Mathlib" in workspace.read_text()
    assert plan.execution_params["original_file"] == str(source)
    assert plan.execution_params["budget"] == 3


def test_workspace_can_resume_when_original_unchanged(tmp_path) -> None:
    source = tmp_path / "Main.lean"
    source.write_text("import Mathlib\n")
    item = LeanBlueprintItem(label="main", lean_declaration="main", file=str(source))
    workspace = LeanProofWorkspaceComponent(str(tmp_path))

    plan = workspace.prepare(item)

    assert workspace.can_resume(plan) is True


def test_workspace_resume_rejects_changed_original(tmp_path) -> None:
    source = tmp_path / "Main.lean"
    source.write_text("import Mathlib\n")
    item = LeanBlueprintItem(label="main", lean_declaration="main", file=str(source))
    workspace = LeanProofWorkspaceComponent(str(tmp_path))
    plan = workspace.prepare(item)
    source.write_text("import Std\n")

    assert workspace.can_resume(plan) is False
    with pytest.raises(RuntimeError, match="changed"):
        workspace.restore(plan, "theorem main : True := by trivial\n")


def test_workspace_restore_writes_proven_code(tmp_path) -> None:
    source = tmp_path / "Main.lean"
    source.write_text("import Mathlib\n")
    item = LeanBlueprintItem(label="main", lean_declaration="main", file=str(source))
    workspace = LeanProofWorkspaceComponent(str(tmp_path))
    plan = workspace.prepare(item)

    workspace.restore(plan, "theorem main : True := by trivial\n")

    assert source.read_text() == "theorem main : True := by trivial\n"


def test_workspace_delegates_to_subagent(tmp_path) -> None:
    source = tmp_path / "Main.lean"
    source.write_text("import Mathlib\n")
    item = LeanBlueprintItem(label="main", lean_declaration="main", file=str(source))
    workspace = LeanProofWorkspaceComponent(str(tmp_path))

    plan = workspace.delegate_to_subagent(item)

    assert plan.execution_params["delegated"] is True
    assert "lock_key" in plan.execution_params


def test_workspace_collects_clean_subagent_artifact() -> None:
    artifact = LeanRunArtifact(artifact_id="a", plan_ref="p", exit_code=0)

    collected = LeanProofWorkspaceComponent().collect_from_subagent(artifact)

    assert collected is artifact


def test_workspace_rejects_failed_subagent_artifact() -> None:
    artifact = LeanRunArtifact(artifact_id="a", plan_ref="p", exit_code=1)

    with pytest.raises(RuntimeError, match="Sub-agent"):
        LeanProofWorkspaceComponent().collect_from_subagent(artifact)
