from __future__ import annotations

from metaharness_ext.lean.contracts import LeanExecutionPolicy, LeanProjectSpec, LeanTaskSpec
from metaharness_ext.lean.environment import LeanEnvironmentComponent, find_lean_project_root


def test_dry_run_environment_probe_without_project() -> None:
    task = LeanTaskSpec(target_file="Proofs/Main.lean")

    report = LeanEnvironmentComponent().probe(task)

    assert report.lean_available is True
    assert report.lake_available is True
    assert report.blocks_promotion is False


def test_dry_run_environment_probe_with_project() -> None:
    task = LeanTaskSpec(
        target_file="Proofs/Main.lean",
        project=LeanProjectSpec(
            project_root="/tmp/lean-project",
            toolchain_version="leanprover/lean4:v4.15.0",
        ),
    )

    report = LeanEnvironmentComponent().probe(task)

    assert report.project_root_found is True
    assert report.toolchain_version == "leanprover/lean4:v4.15.0"


def test_real_lean_requires_explicit_gate(monkeypatch) -> None:
    monkeypatch.delenv("MHE_RUN_REAL_LEAN", raising=False)
    task = LeanTaskSpec(
        target_file="Proofs/Main.lean",
        execution_policy=LeanExecutionPolicy(mode="real_lean"),
    )

    report = LeanEnvironmentComponent().probe(task)

    assert report.blocks_promotion is True
    assert report.lean_available is False


def test_find_lean_project_root(tmp_path) -> None:
    (tmp_path / "lean-toolchain").write_text("leanprover/lean4:v4.15.0")
    (tmp_path / "lakefile.lean").write_text("import Lake")
    source = tmp_path / "Proofs" / "Main.lean"
    source.parent.mkdir()
    source.write_text("#check Nat")

    assert find_lean_project_root(source) == tmp_path
