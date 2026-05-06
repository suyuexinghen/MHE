from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import Any

from metaharness_ext.boutpp.contracts import BoutPPPostprocessReport, BoutPPRunArtifact


class BoutPPPostprocessComponent:
    def postprocess(self, artifact: BoutPPRunArtifact) -> BoutPPPostprocessReport:
        report = BoutPPPostprocessReport(
            report_id=f"boutpp-postprocess-{uuid.uuid4().hex[:12]}",
            task_id=artifact.task_id,
            artifact_ref=artifact.artifact_id,
            log_files=list(artifact.log_files),
            settings_file=artifact.settings_file,
            dump_files=list(artifact.dump_files),
            restart_files=list(artifact.restart_files),
            evidence_refs=list(artifact.evidence_refs),
        )
        if artifact.status not in {"completed", "failed", "timeout"}:
            report.status = "unavailable"
            report.error_message = artifact.error_message
            return report
        report.settings_summary = self._parse_settings(artifact.settings_file)
        report.summary_metrics.update(self._parse_logs(artifact.log_files))
        netcdf_metadata = self._collect_netcdf_metadata(artifact.dump_files)
        if netcdf_metadata is None:
            report.warnings.append("netCDF4 not available or dump files unreadable")
        else:
            report.variable_names = sorted(netcdf_metadata["variable_dimensions"])
            report.dimension_sizes = netcdf_metadata["dimension_sizes"]
            report.variable_dimensions = netcdf_metadata["variable_dimensions"]
        report.summary_metrics.update(
            {
                "log_file_count": len(artifact.log_files),
                "dump_file_count": len(artifact.dump_files),
                "restart_file_count": len(artifact.restart_files),
            }
        )
        report.status = "completed" if artifact.status == "completed" else "partial"
        return report

    def _parse_settings(self, settings_file: str | None) -> dict[str, Any]:
        if not settings_file or not Path(settings_file).exists():
            return {}
        summary: dict[str, Any] = {}
        current_section = "root"
        for raw_line in Path(settings_file).read_text(errors="replace").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or line.startswith(";"):
                continue
            if line.startswith("[") and line.endswith("]"):
                current_section = line[1:-1]
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                summary[f"{current_section}.{key.strip()}"] = value.strip()
        return summary

    def _parse_logs(self, log_files: list[str]) -> dict[str, Any]:
        metrics: dict[str, Any] = {}
        for log_file in log_files:
            path = Path(log_file)
            if not path.exists():
                continue
            text = path.read_text(errors="replace")
            if "Run finished" in text:
                metrics["run_finished"] = True
            runtime = re.search(r"Run time\s*:\s*([0-9.]+)\s*s", text)
            if runtime:
                metrics["runtime_seconds"] = float(runtime.group(1))
            step_matches = re.findall(r"Step\s+([0-9]+)\s+of\s+([0-9]+)", text)
            if step_matches:
                last_step, total_steps = step_matches[-1]
                metrics["last_step"] = int(last_step)
                metrics["total_steps"] = int(total_steps)
        return metrics

    def _collect_netcdf_metadata(self, dump_files: list[str]) -> dict[str, Any] | None:
        if not dump_files:
            return {"dimension_sizes": {}, "variable_dimensions": {}}
        try:
            from netCDF4 import Dataset
        except Exception:
            return None
        dimension_sizes: dict[str, int] = {}
        variable_dimensions: dict[str, list[str]] = {}
        for dump_file in dump_files:
            try:
                with Dataset(dump_file) as dataset:
                    for name, dimension in dataset.dimensions.items():
                        dimension_sizes[str(name)] = len(dimension)
                    for name, variable in dataset.variables.items():
                        variable_dimensions[str(name)] = list(variable.dimensions)
            except Exception:
                return None
        return {"dimension_sizes": dimension_sizes, "variable_dimensions": variable_dimensions}
