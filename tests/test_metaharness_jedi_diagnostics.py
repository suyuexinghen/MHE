from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from metaharness_ext.jedi.contracts import JediRunArtifact
from metaharness_ext.jedi.diagnostics import JediDiagnosticsCollectorComponent


class TestJediDiagnosticsCollectorComponent:
    def test_collects_ioda_groups_from_h5py_file(self, tmp_path: Path) -> None:
        diag_file = tmp_path / "departures.nc"
        diag_file.write_text("")  # h5py branch does not read text

        mock_file = MagicMock()
        mock_file.keys.return_value = ["MetaData", "ObsValue", "HofX", "UnknownGroup"]
        mock_h5py = MagicMock()
        mock_h5py.File.return_value.__enter__ = MagicMock(return_value=mock_file)
        mock_h5py.File.return_value.__exit__ = MagicMock(return_value=False)

        artifact = JediRunArtifact(
            task_id="task-1",
            run_id="run-1",
            application_family="hofx",
            execution_mode="real_run",
            working_directory=str(tmp_path),
            diagnostic_files=[str(diag_file)],
        )

        collector = JediDiagnosticsCollectorComponent()
        with patch.dict(sys.modules, {"h5py": mock_h5py}):
            summary = collector.collect(artifact)

        assert "MetaData" in summary.ioda_groups_found
        assert "ObsValue" in summary.ioda_groups_found
        assert "HofX" in summary.ioda_groups_found
        assert "UnknownGroup" not in summary.ioda_groups_found
        assert "EffectiveError" in summary.ioda_groups_missing
        assert summary.files_scanned == [str(diag_file)]

    def test_collects_ioda_groups_from_json_file(self, tmp_path: Path) -> None:
        diag_file = tmp_path / "departures.json"
        diag_file.write_text(
            json.dumps(
                {
                    "MetaData": {"station_id": [1, 2, 3]},
                    "ObsValue": {"temperature": [280.0, 285.0]},
                    "HofX": {"temperature": [281.0, 284.0]},
                    "ObsError": {"temperature": [1.0, 1.0]},
                }
            )
        )

        artifact = JediRunArtifact(
            task_id="task-1",
            run_id="run-1",
            application_family="hofx",
            execution_mode="real_run",
            working_directory=str(tmp_path),
            diagnostic_files=[str(diag_file)],
        )

        collector = JediDiagnosticsCollectorComponent()
        summary = collector.collect(artifact)

        assert "MetaData" in summary.ioda_groups_found
        assert "ObsValue" in summary.ioda_groups_found
        assert "HofX" in summary.ioda_groups_found
        assert "ObsError" in summary.ioda_groups_found
        assert "EffectiveError" in summary.ioda_groups_missing
        assert summary.files_scanned == [str(diag_file)]

    def test_collects_ioda_groups_from_text_file(self, tmp_path: Path) -> None:
        diag_file = tmp_path / "diag.log"
        diag_file.write_text(
            "Group MetaData found with 100 entries\n"
            "Group ObsValue found with 100 entries\n"
            "Group HofX found with 100 entries\n"
        )

        artifact = JediRunArtifact(
            task_id="task-1",
            run_id="run-1",
            application_family="hofx",
            execution_mode="real_run",
            working_directory=str(tmp_path),
            diagnostic_files=[str(diag_file)],
        )

        collector = JediDiagnosticsCollectorComponent()
        summary = collector.collect(artifact)

        assert "MetaData" in summary.ioda_groups_found
        assert "ObsValue" in summary.ioda_groups_found
        assert "HofX" in summary.ioda_groups_found
        assert "EffectiveError" in summary.ioda_groups_missing

    def test_reports_missing_files(self, tmp_path: Path) -> None:
        artifact = JediRunArtifact(
            task_id="task-1",
            run_id="run-1",
            application_family="variational",
            execution_mode="real_run",
            working_directory=str(tmp_path),
            diagnostic_files=[str(tmp_path / "missing.nc")],
        )

        collector = JediDiagnosticsCollectorComponent()
        summary = collector.collect(artifact)

        assert summary.ioda_groups_found == []
        assert any("not found" in m for m in summary.messages)

    def test_to_dict_roundtrips(self, tmp_path: Path) -> None:
        diag_file = tmp_path / "departures.json"
        diag_file.write_text(json.dumps({"MetaData": {}, "ObsValue": {}}))

        artifact = JediRunArtifact(
            task_id="task-1",
            run_id="run-1",
            application_family="hofx",
            execution_mode="real_run",
            working_directory=str(tmp_path),
            diagnostic_files=[str(diag_file)],
        )

        collector = JediDiagnosticsCollectorComponent()
        summary = collector.collect(artifact)
        d = summary.model_dump()

        assert d["ioda_groups_found"] == ["MetaData", "ObsValue"]
        assert "ioda_groups_missing" in d
        assert "files_scanned" in d
        assert "messages" in d

    def test_collects_variational_metrics_from_log_and_stdout(self, tmp_path: Path) -> None:
        diag_file = tmp_path / "departures.log"
        diag_file.write_text(
            "Outer iteration: 1\n"
            "Inner iteration: 3\n"
            "Minimizer iteration: 4\n"
            "Cost function: 12.5\n"
            "Gradient norm: 8.0\n"
            "Outer iteration: 2\n"
            "Inner iteration: 5\n"
            "Cost function: 3.125\n"
            "Gradient norm: 0.5\n"
        )
        stdout_file = tmp_path / "stdout.log"
        stdout_file.write_text("observer summary available\n")

        artifact = JediRunArtifact(
            task_id="task-1",
            run_id="run-1",
            application_family="variational",
            execution_mode="real_run",
            working_directory=str(tmp_path),
            diagnostic_files=[str(diag_file)],
            stdout_path=str(stdout_file),
        )

        collector = JediDiagnosticsCollectorComponent()
        summary = collector.collect(artifact)

        assert summary.outer_iterations == 2
        assert summary.inner_iterations == 5
        assert summary.minimizer_iterations == 4
        assert summary.initial_cost_function == 12.5
        assert summary.final_cost_function == 3.125
        assert summary.initial_gradient_norm == 8.0
        assert summary.final_gradient_norm == 0.5
        assert summary.gradient_norm_reduction == 0.0625
        assert summary.observer_output_detected is True

    def test_collects_posterior_output_signal(self, tmp_path: Path) -> None:
        diag_file = tmp_path / "posterior.out"
        diag_file.write_text("posterior diagnostics ready\n")

        artifact = JediRunArtifact(
            task_id="task-1",
            run_id="run-1",
            application_family="local_ensemble_da",
            execution_mode="real_run",
            working_directory=str(tmp_path),
            diagnostic_files=[str(diag_file)],
        )

        collector = JediDiagnosticsCollectorComponent()
        summary = collector.collect(artifact)

        assert summary.posterior_output_detected is True

    def test_empty_diagnostic_files_returns_empty_summary(self, tmp_path: Path) -> None:
        artifact = JediRunArtifact(
            task_id="task-1",
            run_id="run-1",
            application_family="variational",
            execution_mode="real_run",
            working_directory=str(tmp_path),
            diagnostic_files=[],
        )

        collector = JediDiagnosticsCollectorComponent()
        summary = collector.collect(artifact)

        assert summary.ioda_groups_found == []
        assert summary.ioda_groups_missing == sorted(collector.IODA_GROUPS)
        assert summary.files_scanned == []
        assert summary.gradient_norm_reduction is None
        assert summary.posterior_output_detected is False
        assert summary.observer_output_detected is False
