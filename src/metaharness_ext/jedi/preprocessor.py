from __future__ import annotations

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
        return prepared_inputs
