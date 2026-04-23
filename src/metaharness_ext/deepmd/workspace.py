from __future__ import annotations

import shutil
from pathlib import Path

from metaharness_ext.deepmd.contracts import DeepMDRunPlan


class WorkspacePreparationError(RuntimeError):
    pass


class DeepMDWorkspacePreparer:
    def prepare(self, plan: DeepMDRunPlan, run_dir: Path) -> list[str]:
        workspace_files: list[str] = []
        for source in plan.workspace_sources:
            source_path = Path(source).expanduser()
            if not source_path.exists():
                raise WorkspacePreparationError(f"Workspace source missing: {source_path}")
            destination = run_dir / source_path.name
            if source_path.is_dir():
                shutil.copytree(source_path, destination, dirs_exist_ok=True)
                for copied in sorted(destination.rglob("*")):
                    if copied.is_file():
                        workspace_files.append(str(copied))
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, destination)
                workspace_files.append(str(destination))

        for relative_path, content in plan.workspace_inline_files.items():
            destination = run_dir / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content)
            workspace_files.append(str(destination))

        return sorted(set(workspace_files))
