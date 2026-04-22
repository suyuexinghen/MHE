from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.jedi.capabilities import CAP_JEDI_CASE_COMPILE
from metaharness_ext.jedi.contracts import (
    JediExperimentSpec,
    JediForecastSpec,
    JediHofXSpec,
    JediLocalEnsembleDASpec,
    JediRunPlan,
    JediVariationalSpec,
)
from metaharness_ext.jedi.slots import JEDI_CONFIG_COMPILER_SLOT


def build_jedi_config(spec: JediExperimentSpec) -> dict[str, Any]:
    if isinstance(spec, JediVariationalSpec):
        return _build_variational_config(spec)
    if isinstance(spec, JediLocalEnsembleDASpec):
        return _build_local_ensemble_da_config(spec)
    if isinstance(spec, JediHofXSpec):
        return _build_hofx_config(spec)
    return _build_forecast_config(spec)


def render_jedi_yaml(data: Any) -> str:
    lines = _render_yaml_lines(data, 0)
    return "\n".join(lines) + "\n"


class JediConfigCompilerComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(JEDI_CONFIG_COMPILER_SLOT)
        api.declare_input("task", "JediExperimentSpec")
        api.declare_output("plan", "JediRunPlan", mode="sync")
        api.provide_capability(CAP_JEDI_CASE_COMPILE)

    def build_plan(self, spec: JediExperimentSpec) -> JediRunPlan:
        run_id = f"{spec.task_id}-{uuid.uuid4().hex[:8]}"
        if spec.working_directory is not None:
            working_directory = str(Path(spec.working_directory).expanduser())
        else:
            working_directory = run_id
        config_path = str(Path(working_directory) / "config.yaml")
        schema_path = (
            str(Path(working_directory) / "schema.json")
            if spec.executable.execution_mode == "schema"
            else None
        )
        config_text = render_jedi_yaml(build_jedi_config(spec))
        command = [spec.executable.binary_name, spec.executable.execution_mode]
        expected_outputs = ["schema.json"] if schema_path is not None else []
        return JediRunPlan(
            task_id=spec.task_id,
            run_id=run_id,
            application_family=spec.application_family,
            execution_mode=spec.executable.execution_mode,
            command=command,
            working_directory=working_directory,
            config_path=config_path,
            schema_path=schema_path,
            expected_outputs=expected_outputs,
            expected_logs=["stdout.log", "stderr.log"],
            config_text=config_text,
            executable=spec.executable,
        )


def _build_variational_config(spec: JediVariationalSpec) -> dict[str, Any]:
    observations = [*spec.observations, *[{"path": path} for path in spec.observation_paths]]
    return {
        "cost function": {
            "cost type": spec.cost_type,
            "window begin": spec.window_begin,
            "window length": spec.window_length,
            "geometry": spec.geometry,
            "background": {**spec.background, **({"path": spec.background_path} if spec.background_path else {})},
            "background error": {
                **spec.background_error,
                **({"covariance path": spec.background_error_path} if spec.background_error_path else {}),
            },
            "observations": observations,
        },
        "variational": spec.variational,
        "output": spec.output,
        "final": spec.final,
        "test": spec.test,
    }


def _build_local_ensemble_da_config(spec: JediLocalEnsembleDASpec) -> dict[str, Any]:
    return {
        "local ensemble da": {
            "window begin": spec.window_begin,
            "window length": spec.window_length,
            "geometry": spec.geometry,
            "ensemble": {**spec.ensemble, "members": spec.ensemble_paths},
            "observations": [{"path": path} for path in spec.observation_paths],
        },
        "output": spec.output,
        "final": spec.final,
        "test": spec.test,
    }


def _build_hofx_config(spec: JediHofXSpec) -> dict[str, Any]:
    return {
        "geometry": spec.geometry,
        "state": {"path": spec.state_path} if spec.state_path else {},
        "observations": [{"path": path} for path in spec.observation_paths],
        "hofx": spec.hofx,
        "output": spec.output,
        "test": spec.test,
    }


def _build_forecast_config(spec: JediForecastSpec) -> dict[str, Any]:
    return {
        "geometry": spec.geometry,
        "initial condition": (
            {"path": spec.initial_condition_path} if spec.initial_condition_path else {}
        ),
        "model": spec.model,
        "forecast": spec.forecast,
        "output": spec.output,
        "test": spec.test,
    }


def _render_yaml_lines(value: Any, indent: int) -> list[str]:
    prefix = " " * indent
    if isinstance(value, dict):
        if not value:
            return [f"{prefix}{{}}"]
        lines: list[str] = []
        for key, child in value.items():
            if _is_scalar(child):
                lines.append(f"{prefix}{key}: {_render_scalar(child)}")
            else:
                lines.append(f"{prefix}{key}:")
                lines.extend(_render_yaml_lines(child, indent + 2))
        return lines
    if isinstance(value, list):
        if not value:
            return [f"{prefix}[]"]
        lines = []
        for item in value:
            if _is_scalar(item):
                lines.append(f"{prefix}- {_render_scalar(item)}")
            else:
                lines.append(f"{prefix}-")
                lines.extend(_render_yaml_lines(item, indent + 2))
        return lines
    return [f"{prefix}{_render_scalar(value)}"]


def _is_scalar(value: Any) -> bool:
    return value is None or isinstance(value, str | int | float | bool)


def _render_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return str(value)
    return json.dumps(value)
