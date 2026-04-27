from __future__ import annotations

import shutil
from pathlib import Path

from metaharness_ext.octave.contracts import OctaveInputAssetSpec, OctaveRunPlan


class OctaveWorkspaceManager:
    def materialize_plan(self, plan: OctaveRunPlan, run_dir: Path) -> tuple[str, list[str]]:
        run_dir.mkdir(parents=True, exist_ok=True)
        self._validate_relative_name(plan.execution_params.output_directory)
        outputs_dir = run_dir / plan.execution_params.output_directory
        outputs_dir.mkdir(exist_ok=True)

        wrapper_path = run_dir / plan.wrapper_name
        wrapper_path.write_text(plan.wrapper_source)
        input_paths = self.stage_inputs(plan.input_assets, run_dir)
        return str(wrapper_path), input_paths

    def stage_inputs(self, inputs: list[OctaveInputAssetSpec], run_dir: Path) -> list[str]:
        staged: list[str] = []
        for asset in inputs:
            source = Path(asset.source_path).expanduser()
            if not source.exists():
                raise FileNotFoundError(f"Octave input asset not found: {asset.source_path}")
            target_name = asset.target_name or source.name
            self._validate_relative_name(target_name)
            target = run_dir / target_name
            if source.is_dir():
                raise ValueError("Octave input assets must be files")
            shutil.copy2(source, target)
            staged.append(str(target))
        return staged

    def discover_outputs(
        self, run_dir: Path, plan: OctaveRunPlan
    ) -> tuple[list[str], list[str], list[str]]:
        output_files: list[str] = []
        figure_files: list[str] = []
        log_files: list[str] = []
        for output in plan.expected_outputs:
            if output.file_name is None:
                continue
            self._validate_relative_name(output.file_name)
            candidate = run_dir / output.file_name
            if candidate.exists():
                path = str(candidate)
                if output.kind == "figure":
                    figure_files.append(path)
                elif output.kind == "log":
                    log_files.append(path)
                else:
                    output_files.append(path)
        for candidate in sorted((run_dir / plan.execution_params.output_directory).glob("*")):
            if candidate.is_file():
                output_files.append(str(candidate))
        status_path = run_dir / "mhe_status.txt"
        if status_path.exists():
            log_files.append(str(status_path))
        return sorted(set(output_files)), sorted(set(figure_files)), sorted(set(log_files))

    def _validate_relative_name(self, name: str) -> None:
        path = Path(name)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"Octave workspace path must be relative: {name!r}")
