from __future__ import annotations

import json
from pathlib import Path

from metaharness_ext.jedi.contracts import JediRunPlan


class JediRunPreprocessor:
    def prepare(self, plan: JediRunPlan, run_dir: Path) -> list[str]:
        config_path = run_dir / "config.yaml"
        config_path.write_text(plan.config_text)

        prepared_inputs: list[str] = []
        for path_str in plan.required_runtime_paths:
            path = Path(path_str).expanduser()
            if not path.exists():
                raise ValueError(f"Missing required runtime path: {path}")
            prepared_inputs.append(str(path.resolve()))

        self._write_preparation_manifest(plan, run_dir, prepared_inputs)
        return prepared_inputs

    def _write_preparation_manifest(
        self,
        plan: JediRunPlan,
        run_dir: Path,
        prepared_inputs: list[str],
    ) -> None:
        manifest_path = run_dir / "preprocessor_manifest.json"
        manifest = {
            "task_id": plan.task_id,
            "run_id": plan.run_id,
            "working_directory": str(run_dir),
            "config_path": str(run_dir / "config.yaml"),
            "prepared_inputs": prepared_inputs,
            "required_runtime_paths": list(plan.required_runtime_paths),
        }
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
