from __future__ import annotations

import importlib.util
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


def _module_available(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def build_run_manifest(
    *,
    suite: BenchmarkSuite,
    lanes: list[BenchmarkLane],
    cases: list[str],
    runs_root: Path,
    brain_provider: str = "claude-cli",
    claude_binary: str = "claude",
    claude_model: str | None = None,
    claude_max_turns: int = 5,
    claude_permission_mode: str = "auto",
    claude_extra_args: list[str] | None = None,
    real_claude: bool = False,
    real_tools: bool = False,
    repeat_count: int = 1,
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
        claude_cli={
            "brain_provider": brain_provider,
            "binary": claude_binary,
            "version": _version(claude_binary),
            "model": claude_model,
            "max_turns": claude_max_turns,
            "permission_mode": claude_permission_mode,
            "extra_args": claude_extra_args or [],
            "real_claude": real_claude,
            "real_tools": real_tools,
            "repeat_count": repeat_count,
        },
        tools={
            "octave-cli": _version("octave-cli"),
            "ADRSolver": _version("ADRSolver"),
            "IncNavierStokesSolver": _version("IncNavierStokesSolver"),
            "DiffusionSolver": _version("DiffusionSolver"),
            "CompressibleFlowSolver": _version("CompressibleFlowSolver"),
            "abacus": _version("abacus"),
            "qiskit": {"available": _module_available("qiskit")},
            "qiskit_aer": {"available": _module_available("qiskit_aer")},
            "pennylane": {"available": _module_available("pennylane")},
        },
    )
