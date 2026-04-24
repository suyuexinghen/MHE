from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.jedi.capabilities import CAP_JEDI_ENV_PROBE
from metaharness_ext.jedi.contracts import (
    JediEnvironmentReport,
    JediExperimentSpec,
    JediForecastSpec,
    JediHofXSpec,
    JediLocalEnsembleDASpec,
    JediVariationalSpec,
)
from metaharness_ext.jedi.slots import JEDI_ENVIRONMENT_SLOT


class JediEnvironmentProbeComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(JEDI_ENVIRONMENT_SLOT)
        api.declare_input("task", "JediExperimentSpec")
        api.declare_output("environment", "JediEnvironmentReport", mode="sync")
        api.provide_capability(CAP_JEDI_ENV_PROBE)

    def probe(self, spec: JediExperimentSpec) -> JediEnvironmentReport:
        messages: list[str] = []
        workspace_root = self._workspace_root(spec)
        binary_path = self._resolve_binary(spec.executable.binary_name)
        binary_available = binary_path is not None
        launcher_path: str | None = None
        launcher_available = True
        if spec.executable.launcher != "direct":
            launcher_path = self._resolve_binary(spec.executable.launcher)
            launcher_available = launcher_path is not None
            if not launcher_available:
                messages.append(f"Launcher not found: {spec.executable.launcher}")

        shared_libraries_resolved = True
        if binary_path is not None:
            shared_libraries_resolved = self._check_shared_libraries(binary_path, messages)
        else:
            messages.append(f"JEDI binary not found: {spec.executable.binary_name}")

        missing_required_paths: list[str] = []
        missing_data_paths: list[str] = []
        for path_str in self._required_paths(spec):
            path = Path(path_str).expanduser()
            if path.exists():
                continue
            normalized = str(path)
            missing_required_paths.append(normalized)
            if self._looks_like_data_path(path):
                missing_data_paths.append(normalized)
            messages.append(f"Missing required path: {path}")

        required_paths_present = not missing_required_paths
        data_paths_present = not missing_data_paths
        workspace_testinput_present = self._workspace_testinput_present(workspace_root)

        environment_prerequisites = self._environment_prerequisites(spec, workspace_root)
        ready_prerequisites, missing_prerequisites, prerequisite_evidence = (
            self._evaluate_prerequisites(spec, workspace_root, environment_prerequisites)
        )
        for prerequisite in missing_prerequisites:
            messages.append(f"Missing environment prerequisite: {prerequisite}")
        data_prerequisites_ready = not missing_prerequisites

        smoke_candidate: str | None = (
            "hofx" if isinstance(spec, JediHofXSpec) else spec.application_family
        )
        smoke_ready = (
            binary_available
            and launcher_available
            and shared_libraries_resolved
            and required_paths_present
            and workspace_testinput_present
            and data_prerequisites_ready
        )
        if smoke_ready:
            messages.append(f"Toy smoke candidate ready: {smoke_candidate}.")
        else:
            messages.append(f"Toy smoke candidate not ready: {smoke_candidate}.")

        return JediEnvironmentReport(
            binary_available=binary_available,
            launcher_available=launcher_available,
            shared_libraries_resolved=shared_libraries_resolved,
            required_paths_present=required_paths_present,
            workspace_testinput_present=workspace_testinput_present,
            data_paths_present=data_paths_present,
            data_prerequisites_ready=data_prerequisites_ready,
            binary_path=binary_path,
            launcher_path=launcher_path,
            workspace_root=workspace_root,
            missing_required_paths=missing_required_paths,
            missing_data_paths=missing_data_paths,
            missing_prerequisites=missing_prerequisites,
            ready_prerequisites=ready_prerequisites,
            prerequisite_evidence=prerequisite_evidence,
            environment_prerequisites=environment_prerequisites,
            smoke_candidate=smoke_candidate,
            smoke_ready=smoke_ready,
            messages=messages,
        )

    def _resolve_binary(self, binary_name: str) -> str | None:
        candidate = Path(binary_name).expanduser()
        if candidate.is_absolute() and candidate.exists():
            return str(candidate)
        if candidate.exists():
            return str(candidate.resolve())
        return shutil.which(binary_name)

    def _check_shared_libraries(self, binary_path: str, messages: list[str]) -> bool:
        if shutil.which("ldd") is None:
            messages.append("ldd not found; skipping shared library resolution check")
            return True
        result = subprocess.run(
            ["ldd", binary_path],
            text=True,
            capture_output=True,
            check=False,
        )
        unresolved = [line.strip() for line in result.stdout.splitlines() if "not found" in line]
        if unresolved:
            messages.extend(f"Unresolved library: {line}" for line in unresolved)
            return False
        return result.returncode == 0

    def _workspace_root(self, spec: JediExperimentSpec) -> str | None:
        candidate_paths = self._required_paths(spec)
        for path_str in candidate_paths:
            path = Path(path_str).expanduser()
            for parent in (path, *path.parents):
                testinput_dir = parent / "testinput"
                if testinput_dir.is_dir():
                    return str(parent)
        working_directory = getattr(spec, "working_directory", None)
        if working_directory:
            path = Path(working_directory).expanduser()
            for parent in (path, *path.parents):
                testinput_dir = parent / "testinput"
                if testinput_dir.is_dir():
                    return str(parent)
        return None

    def _workspace_testinput_present(self, workspace_root: str | None) -> bool:
        if workspace_root is None:
            return True
        return (Path(workspace_root) / "testinput").is_dir()

    def _looks_like_data_path(self, path: Path) -> bool:
        lowered = str(path).lower()
        suffixes = {".nc", ".ioda", ".odb", ".h5", ".hdf5"}
        if path.suffix.lower() in suffixes:
            return True
        return any(token in lowered for token in ("obs", "background", "reference", "ens."))

    def _environment_prerequisites(
        self, spec: JediExperimentSpec, workspace_root: str | None
    ) -> list[str]:
        prerequisites: list[str] = []
        if workspace_root is not None:
            prerequisites.append("workspace testinput")
        if (
            spec.observation_paths
            if isinstance(spec, (JediVariationalSpec, JediLocalEnsembleDASpec, JediHofXSpec))
            else False
        ):
            prerequisites.append("ctest -R get_ or equivalent observation data preparation")
        if isinstance(spec, (JediVariationalSpec, JediLocalEnsembleDASpec)):
            prerequisites.append("ctest -R qg_get_data or equivalent QG data preparation")
        if isinstance(spec, JediForecastSpec):
            prerequisites.append("model initial-condition data prepared")
        return list(dict.fromkeys(prerequisites))

    def _evaluate_prerequisites(
        self,
        spec: JediExperimentSpec,
        workspace_root: str | None,
        prerequisites: list[str],
    ) -> tuple[list[str], list[str], dict[str, list[str]]]:
        ready: list[str] = []
        missing: list[str] = []
        evidence: dict[str, list[str]] = {}
        for prerequisite in prerequisites:
            status, matched_evidence = self._prerequisite_status(
                prerequisite,
                spec,
                workspace_root,
            )
            if status == "ready":
                ready.append(prerequisite)
                evidence[prerequisite] = matched_evidence
            elif status == "missing":
                missing.append(prerequisite)
        return ready, missing, evidence

    def _prerequisite_status(
        self,
        prerequisite: str,
        spec: JediExperimentSpec,
        workspace_root: str | None,
    ) -> tuple[str, list[str]]:
        if prerequisite == "workspace testinput":
            if workspace_root is None:
                return "unevaluated", []
            testinput_path = str(Path(workspace_root) / "testinput")
            if self._workspace_testinput_present(workspace_root):
                return "ready", [testinput_path]
            return "missing", []
        if prerequisite == "ctest -R get_ or equivalent observation data preparation":
            return self._paths_prerequisite_status(self._observation_paths(spec))
        if prerequisite == "ctest -R qg_get_data or equivalent QG data preparation":
            return self._paths_prerequisite_status(self._qg_data_paths(spec))
        if prerequisite == "model initial-condition data prepared":
            return self._paths_prerequisite_status(self._forecast_data_paths(spec))
        return "unevaluated", []

    def _paths_prerequisite_status(self, paths: list[str]) -> tuple[str, list[str]]:
        if not paths:
            return "unevaluated", []
        existing = [str(Path(path).expanduser().resolve()) for path in paths if Path(path).expanduser().exists()]
        if len(existing) == len(paths):
            return "ready", existing
        return "missing", []

    def _observation_paths(self, spec: JediExperimentSpec) -> list[str]:
        if isinstance(spec, (JediVariationalSpec, JediLocalEnsembleDASpec, JediHofXSpec)):
            return list(spec.observation_paths)
        return []

    def _qg_data_paths(self, spec: JediExperimentSpec) -> list[str]:
        if isinstance(spec, JediVariationalSpec):
            return [
                *([spec.background_path] if spec.background_path else []),
                *([spec.background_error_path] if spec.background_error_path else []),
            ]
        if isinstance(spec, JediLocalEnsembleDASpec):
            return [
                *spec.ensemble_paths,
                *([spec.background_path] if spec.background_path else []),
                *spec.reference_paths,
            ]
        return []

    def _forecast_data_paths(self, spec: JediExperimentSpec) -> list[str]:
        if isinstance(spec, JediForecastSpec) and spec.initial_condition_path:
            return [spec.initial_condition_path]
        return []

    def _required_paths(self, spec: JediExperimentSpec) -> list[str]:
        if isinstance(spec, JediVariationalSpec):
            return [
                *([spec.background_path] if spec.background_path else []),
                *([spec.background_error_path] if spec.background_error_path else []),
                *spec.observation_paths,
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
            return [
                *([spec.state_path] if spec.state_path else []),
                *spec.observation_paths,
                *spec.required_paths,
            ]
        if isinstance(spec, JediForecastSpec):
            return [
                *([spec.initial_condition_path] if spec.initial_condition_path else []),
                *spec.required_paths,
            ]
        raise NotImplementedError(
            f"Unsupported JEDI application family for required path resolution: {spec!r}"
        )
