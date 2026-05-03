from __future__ import annotations

import pytest

from metaharness_ext.boutpp.contracts import BoutPPMpiSpec, BoutPPProblemSpec, BoutPPStudyAxis


class TestBoutPPMpiSpec:
    def test_defaults(self):
        spec = BoutPPMpiSpec()
        assert spec.launcher_mode == "mpi"
        assert spec.processes == 1

    def test_processes_validation(self):
        with pytest.raises(ValueError, match=">= 1"):
            BoutPPMpiSpec(processes=0)


class TestBoutPPProblemSpec:
    def test_minimal_defaults(self):
        spec = BoutPPProblemSpec(task_id="boutpp-test")
        assert spec.case_name == "conduction"
        assert spec.executable == "conduction"

    def test_task_id_validation(self):
        with pytest.raises(ValueError, match="simple identifier"):
            BoutPPProblemSpec(task_id="bad/path")

    def test_empty_executable_rejected(self):
        with pytest.raises(ValueError, match="must not be empty"):
            BoutPPProblemSpec(task_id="t", executable=" ")

    def test_timeout_validation(self):
        with pytest.raises(ValueError, match="positive"):
            BoutPPProblemSpec(task_id="t", timeout_seconds=0)

    def test_cli_override_format(self):
        with pytest.raises(ValueError, match="key=value"):
            BoutPPProblemSpec(task_id="t", cli_overrides=["solver:type = rk4"])


class TestBoutPPStudyAxis:
    def test_parameter_path_validation(self):
        with pytest.raises(ValueError, match="must not be empty"):
            BoutPPStudyAxis(parameter_path=" ")
