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
        expected_outputs = ["schema.json"] if schema_path is not None else _expected_outputs(spec)
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
            expected_diagnostics=_expected_diagnostics(spec),
            expected_references=_expected_references(spec),
            required_runtime_paths=_required_runtime_paths(spec),
            scientific_check=_scientific_check(spec),
            config_text=config_text,
            executable=spec.executable,
        )


def _build_variational_config(spec: JediVariationalSpec) -> dict[str, Any]:
    observations = [*spec.observations, *[{"path": path} for path in spec.observation_paths]]
    variational = {
        "minimizer": {"algorithm": "RPCG", "iterations": 20},
        **spec.variational,
    }
    output = {"filename": "analysis.out", **spec.output}
    final = {"diagnostics": {"filename": "departures.json"}, **spec.final}
    test = {"reference": {"filename": "reference.json"}, **spec.test}
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
        "variational": variational,
        "output": output,
        "final": final,
        "test": test,
    }


def _build_local_ensemble_da_config(spec: JediLocalEnsembleDASpec) -> dict[str, Any]:
    output = {"filename": "letkf.out", **spec.output}
    final = {"diagnostics": {"filename": "posterior.out"}, **spec.final}
    test = {"reference": {"filename": "ensemble_reference.json"}, **spec.test}
    return {
        "window begin": spec.window_begin,
        "window length": spec.window_length,
        "geometry": spec.geometry,
        "background": {**spec.background, **({"path": spec.background_path} if spec.background_path else {})},
        "observations": [{"path": path} for path in spec.observation_paths],
        "driver": {"task": "local_ensemble_da", **spec.driver},
        "local ensemble DA": {**spec.ensemble, "members": spec.ensemble_paths},
        "output": output,
        "final": final,
        "test": test,
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


def _required_runtime_paths(spec: JediExperimentSpec) -> list[str]:
    if isinstance(spec, JediVariationalSpec):
        return [
            *([spec.background_path] if spec.background_path else []),
            *([spec.background_error_path] if spec.background_error_path else []),
            *spec.observation_paths,
            *spec.reference_paths,
            *spec.required_paths,
        ]
    if isinstance(spec, JediLocalEnsembleDASpec):
        return [
            *spec.ensemble_paths,
            *([spec.background_path] if spec.background_path else []),
            *spec.observation_paths,
            *spec.reference_paths,
            *spec.required_paths,
        ]
    if isinstance(spec, JediHofXSpec):
        return [*([spec.state_path] if spec.state_path else []), *spec.observation_paths, *spec.required_paths]
    return [*([spec.initial_condition_path] if spec.initial_condition_path else []), *spec.required_paths]


def _expected_outputs(spec: JediExperimentSpec) -> list[str]:
    output_filename = spec.output.get("filename")
    if isinstance(output_filename, str) and output_filename.strip():
        return [output_filename]
    defaults = {
        "variational": "analysis.out",
        "local_ensemble_da": "letkf.out",
        "hofx": "hofx.out",
        "forecast": "forecast.out",
    }
    return [defaults[spec.application_family]] if spec.executable.execution_mode == "real_run" else []


def _expected_diagnostics(spec: JediExperimentSpec) -> list[str]:
    if isinstance(spec, JediVariationalSpec):
        diagnostics = list(spec.expected_diagnostics)
        final_diagnostics = spec.final.get("diagnostics")
        if isinstance(final_diagnostics, dict):
            filename = final_diagnostics.get("filename")
            if isinstance(filename, str) and filename.strip():
                diagnostics.append(filename)
        elif spec.executable.execution_mode == "real_run":
            diagnostics.append("departures.json")
        return list(dict.fromkeys(diagnostics))
    if isinstance(spec, JediLocalEnsembleDASpec):
        diagnostics = list(spec.expected_diagnostics)
        final_diagnostics = spec.final.get("diagnostics")
        if isinstance(final_diagnostics, dict):
            filename = final_diagnostics.get("filename")
            if isinstance(filename, str) and filename.strip():
                diagnostics.append(filename)
        elif spec.executable.execution_mode == "real_run":
            diagnostics.append("posterior.out")
        return list(dict.fromkeys(diagnostics))
    return []



def _expected_references(spec: JediExperimentSpec) -> list[str]:
    if isinstance(spec, JediVariationalSpec):
        reference_files = list(spec.reference_paths)
        reference = spec.test.get("reference")
        if isinstance(reference, dict):
            filename = reference.get("filename")
            if isinstance(filename, str) and filename.strip():
                reference_files.append(filename)
        elif spec.executable.execution_mode == "real_run":
            reference_files.append("reference.json")
        return list(dict.fromkeys(reference_files))
    if isinstance(spec, JediLocalEnsembleDASpec):
        reference_files = list(spec.reference_paths)
        reference = spec.test.get("reference")
        if isinstance(reference, dict):
            filename = reference.get("filename")
            if isinstance(filename, str) and filename.strip():
                reference_files.append(filename)
        elif spec.executable.execution_mode == "real_run":
            reference_files.append("ensemble_reference.json")
        return list(dict.fromkeys(reference_files))
    return []



def _scientific_check(spec: JediExperimentSpec) -> str:
    if isinstance(spec, JediVariationalSpec | JediLocalEnsembleDASpec):
        return spec.scientific_check
    return "runtime_only"


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
