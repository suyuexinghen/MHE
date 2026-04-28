from __future__ import annotations

import platform
import shutil
import subprocess
from pathlib import Path

from metaharness.benchmark_drivers.models import BenchmarkLane, BenchmarkSuite, RunManifest


def _git_revision(cwd: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
            timeout=5,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _version(binary: str) -> str | None:
    path = shutil.which(binary)
    if not path:
        return None
    try:
        result = subprocess.run(
            [path, "--version"],
            text=True,
            capture_output=True,
            check=False,
            timeout=5,
        )
    except OSError:
        return None
    output = result.stdout.strip() or result.stderr.strip()
    return output.splitlines()[0] if output else None


def build_run_manifest(
    *,
    suite: BenchmarkSuite,
    lanes: list[BenchmarkLane],
    cases: list[str],
    runs_root: Path,
    claude_binary: str = "claude",
    cwd: Path | None = None,
) -> RunManifest:
    root = cwd or Path.cwd()
    return RunManifest(
        suite=suite,
        lanes=lanes,
        cases=cases,
        runs_root=str(runs_root),
        git_revision=_git_revision(root),
        python_version=platform.python_version(),
        claude_cli={"binary": claude_binary, "version": _version(claude_binary)},
        tools={
            "octave-cli": _version("octave-cli"),
            "ADRSolver": _version("ADRSolver"),
            "IncNavierStokesSolver": _version("IncNavierStokesSolver"),
            "DiffusionSolver": _version("DiffusionSolver"),
            "CompressibleFlowSolver": _version("CompressibleFlowSolver"),
        },
    )
