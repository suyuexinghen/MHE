from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.deepmd.capabilities import CAP_DEEPMD_ENV_PROBE
from metaharness_ext.deepmd.contracts import (
    DeepMDEnvironmentReport,
    DeepMDExperimentSpec,
    DeepMDTrainSpec,
    DPGenAutotestSpec,
    DPGenRunSpec,
    DPGenSimplifySpec,
)
from metaharness_ext.deepmd.slots import DEEPMD_ENVIRONMENT_SLOT

HPC_FALLBACK_REASONS = {
    "machine.local_root": "missing_machine_root",
    "machine.remote_root": "missing_remote_root",
    "machine.command": "missing_scheduler_command",
    "machine.python_path": "missing_python_runtime",
}


class DeepMDEnvironmentProbeComponent(HarnessComponent):
    probe_timeout_seconds = 10

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(DEEPMD_ENVIRONMENT_SLOT)
        api.declare_input("task", "DeepMDExperimentSpec")
        api.declare_output("environment", "DeepMDEnvironmentReport", mode="sync")
        api.provide_capability(CAP_DEEPMD_ENV_PROBE)

    def probe(self, spec: DeepMDExperimentSpec) -> DeepMDEnvironmentReport:
        messages: list[str] = []
        missing_required_paths: list[str] = []
        environment_prerequisites: list[str] = []
        missing_prerequisites: list[str] = []
        evidence_refs: list[str] = [f"deepmd://environment/{spec.task_id}"]

        resolved_binary = self._resolve_binary(spec.executable.binary_name)
        dp_available = resolved_binary is not None
        dpgen_available = dp_available if spec.application_family.startswith("dpgen_") else False
        dp_probe_supported = False
        dp_probe_succeeded = False
        dp_probe_output: str | None = None
        dpgen_probe_supported = False
        dpgen_probe_succeeded = False
        dpgen_probe_output: str | None = None
        python_binary = self._python_binary(spec)
        python_available = python_binary is not None
        machine_spec_valid = True
        fallback_reason: str | None = None

        if dp_available and resolved_binary is not None:
            if spec.application_family.startswith("dpgen_"):
                dpgen_probe_supported = True
                dpgen_probe_output = self._probe_binary(resolved_binary, ["--help"])
                dpgen_probe_succeeded = dpgen_probe_output is not None
                if not dpgen_probe_succeeded:
                    messages.append("dpgen --help probe failed")
                else:
                    evidence_refs.append(f"deepmd://binary/{Path(resolved_binary).name}")
            else:
                dp_probe_supported = True
                dp_probe_output = self._probe_binary(resolved_binary, ["--help"])
                dp_probe_succeeded = dp_probe_output is not None
                if not dp_probe_succeeded:
                    messages.append("dp --help probe failed")
                else:
                    evidence_refs.append(f"deepmd://binary/{Path(resolved_binary).name}")

        for path_str in self._required_paths(spec):
            path = Path(path_str).expanduser()
            if path.exists():
                continue
            missing_required_paths.append(str(path))
            label = "dataset path" if isinstance(spec, DeepMDTrainSpec) else "workspace path"
            messages.append(f"Missing {label}: {path}")

        required_paths_present = not missing_required_paths
        workspace_ready = required_paths_present

        if spec.working_directory is not None:
            workdir = Path(spec.working_directory).expanduser()
            if workdir.exists() and not workdir.is_dir():
                required_paths_present = False
                workspace_ready = False
                missing_required_paths.append(str(workdir))
                messages.append(f"Working directory is not a directory: {workdir}")

        machine_root_ready = True
        remote_root_configured = True
        scheduler_command_configured = True

        if isinstance(spec, DPGenRunSpec | DPGenSimplifySpec | DPGenAutotestSpec):
            environment_prerequisites = self._environment_prerequisites(spec)
            local_root = Path(spec.machine.local_root).expanduser()
            if not local_root.exists() or not local_root.is_dir():
                machine_root_ready = False
                workspace_ready = False
                missing_prerequisites.append("machine.local_root")
                messages.append(f"Machine local root is not a directory: {local_root}")
            if spec.machine.context_type != "local" and not spec.machine.remote_root:
                remote_root_configured = False
                missing_prerequisites.append("machine.remote_root")
                messages.append("Missing environment prerequisite: machine.remote_root")
            if spec.machine.batch_type != "shell" and not spec.machine.command:
                scheduler_command_configured = False
                missing_prerequisites.append("machine.command")
                messages.append("Missing environment prerequisite: machine.command")
            if spec.machine.python_path and self._resolve_binary(spec.machine.python_path) is None:
                missing_prerequisites.append("machine.python_path")
                messages.append(
                    f"Configured Python interpreter not found: {spec.machine.python_path}"
                )
                python_available = False
            machine_spec_valid = (
                machine_root_ready
                and remote_root_configured
                and scheduler_command_configured
                and python_available
            )

        if isinstance(spec, DeepMDTrainSpec):
            environment_prerequisites = self._environment_prerequisites(spec)

        missing_prerequisites.extend(
            prerequisite
            for prerequisite in environment_prerequisites
            if prerequisite == "python" and not python_available
        )

        if not dp_available:
            binary_label = "DP-GEN" if spec.application_family.startswith("dpgen_") else "DeepMD"
            messages.append(f"{binary_label} binary not found: {spec.executable.binary_name}")
            missing_prerequisites.append(spec.executable.binary_name)
            fallback_reason = "binary_not_found"
        if not python_available:
            messages.append("Python interpreter not found on PATH")
            fallback_reason = fallback_reason or "missing_python_runtime"

        if fallback_reason is None:
            for prerequisite, candidate_reason in HPC_FALLBACK_REASONS.items():
                if prerequisite in missing_prerequisites:
                    fallback_reason = candidate_reason
                    break

        evidence_refs.extend(
            f"deepmd://missing-path/{Path(path).name}" for path in missing_required_paths
        )
        evidence_refs.extend(
            f"deepmd://missing-prerequisite/{item}" for item in dict.fromkeys(missing_prerequisites)
        )

        return DeepMDEnvironmentReport(
            application_family=spec.application_family,
            execution_mode=spec.executable.execution_mode,
            dp_available=dp_available,
            dpgen_available=dpgen_available,
            python_available=python_available,
            required_paths_present=required_paths_present,
            workspace_ready=workspace_ready,
            machine_root_ready=machine_root_ready,
            remote_root_configured=remote_root_configured,
            scheduler_command_configured=scheduler_command_configured,
            machine_spec_valid=machine_spec_valid,
            dp_probe_supported=dp_probe_supported,
            dp_probe_succeeded=dp_probe_succeeded,
            dp_probe_output=dp_probe_output,
            dpgen_probe_supported=dpgen_probe_supported,
            dpgen_probe_succeeded=dpgen_probe_succeeded,
            dpgen_probe_output=dpgen_probe_output,
            missing_required_paths=missing_required_paths,
            environment_prerequisites=environment_prerequisites,
            missing_prerequisites=list(dict.fromkeys(missing_prerequisites)),
            messages=messages,
            evidence_refs=list(dict.fromkeys(evidence_refs)),
            fallback_reason=fallback_reason,
        )

    def _required_paths(self, spec: DeepMDExperimentSpec) -> list[str]:
        if isinstance(spec, DeepMDTrainSpec):
            return [*spec.dataset.train_systems, *spec.dataset.validation_systems]
        return list(spec.workspace_files)

    def _environment_prerequisites(self, spec: DeepMDExperimentSpec) -> list[str]:
        prerequisites = ["python"]
        if isinstance(spec, DPGenRunSpec | DPGenSimplifySpec | DPGenAutotestSpec):
            prerequisites.append("machine.local_root")
            if spec.machine.context_type != "local":
                prerequisites.append("machine.remote_root")
            if spec.machine.batch_type != "shell":
                prerequisites.append("machine.command")
            if spec.machine.python_path:
                prerequisites.append("machine.python_path")
        return prerequisites

    def _python_binary(self, spec: DeepMDExperimentSpec) -> str | None:
        if isinstance(spec, DPGenRunSpec | DPGenSimplifySpec | DPGenAutotestSpec):
            if spec.machine.python_path:
                return self._resolve_binary(spec.machine.python_path)
        return self._resolve_binary("python") or self._resolve_binary("python3")

    def _resolve_binary(self, binary_name: str) -> str | None:
        candidate = Path(binary_name).expanduser()
        if candidate.is_absolute() and candidate.exists():
            return str(candidate)
        if candidate.exists():
            return str(candidate.resolve())
        return shutil.which(binary_name)

    def _probe_binary(self, binary_path: str, args: list[str]) -> str | None:
        try:
            try:
                result = subprocess.run(
                    [binary_path, *args],
                    cwd=Path("."),
                    text=True,
                    capture_output=True,
                    check=False,
                    timeout=self.probe_timeout_seconds,
                )
            except TypeError:
                result = subprocess.run(
                    [binary_path, *args],
                    text=True,
                    capture_output=True,
                    check=False,
                    timeout=self.probe_timeout_seconds,
                )
        except (OSError, subprocess.TimeoutExpired):
            return None
        if result.returncode != 0:
            return None
        output = result.stdout.strip()
        return output or None
