from __future__ import annotations

from pathlib import Path

from metaharness_ext.boutpp.compiler import BoutPPCompilerComponent
from metaharness_ext.boutpp.contracts import BoutPPProblemSpec
from metaharness_ext.boutpp.executor import BoutPPExecutorComponent


def _make_script(path: Path) -> Path:
    path.write_text(
        "#!/usr/bin/env python3\n"
        "from pathlib import Path\n"
        "data = Path('data')\n"
        "data.mkdir(exist_ok=True)\n"
        "(data / 'BOUT.settings').write_text('[solver]\\ntype = rk4\\n')\n"
        "(data / 'BOUT.log.0').write_text('Run finished\\nRun time : 1 s\\n')\n"
        "(data / 'BOUT.dmp.0.nc').write_text('dump')\n"
        "(data / 'BOUT.restart.0.nc').write_text('restart')\n"
    )
    path.chmod(0o755)
    return path


def test_execute_success(tmp_path):
    script = _make_script(tmp_path / "conduction")
    spec = BoutPPProblemSpec(task_id="exec", executable=str(script), mpi={"launcher_mode": "direct"})
    compiler = BoutPPCompilerComponent()
    plan = compiler.compile(spec, run_id="run-1", workspace_dir=str(tmp_path / "ws"))
    executor = BoutPPExecutorComponent(workspace_root=str(tmp_path / "runs"))
    artifact = executor.execute(plan)
    assert artifact.status == "completed"
    assert artifact.settings_file is not None
    assert artifact.log_files
    assert artifact.dump_files
    assert artifact.restart_files


def test_execute_unavailable_when_executable_missing(tmp_path):
    spec = BoutPPProblemSpec(task_id="exec2", executable="missing-binary", mpi={"launcher_mode": "direct"})
    plan = BoutPPCompilerComponent().compile(spec, run_id="run-2", workspace_dir=str(tmp_path / "ws"))
    artifact = BoutPPExecutorComponent(workspace_root=str(tmp_path / "runs")).execute(plan)
    assert artifact.status == "unavailable"
    assert artifact.error_message
