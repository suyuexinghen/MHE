from __future__ import annotations

import os
import tempfile
from unittest.mock import patch

from metaharness_ext.pycfd.environment import PyCFDEnvironmentProbeComponent


class TestPyCFDEnvironmentProbe:
    def test_no_pycfd_path_returns_unavailable(self):
        probe = PyCFDEnvironmentProbeComponent(pycfd_src_path="/nonexistent/path")
        report = probe.probe(task_id="test")
        assert not report.available
        assert "not_found" in report.status
        assert report.blocks_promotion

    def test_env_var_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a minimal Solvers.py
            solvers_path = os.path.join(tmpdir, "Solvers.py")
            with open(solvers_path, "w") as f:
                f.write("# placeholder\n")

            with patch.dict(os.environ, {"PYCFD_SRC_PATH": tmpdir}):
                probe = PyCFDEnvironmentProbeComponent()
                report = probe.probe(task_id="test")
                assert report.available or report.status == "partial"
                assert report.pycfd_src_path == os.path.abspath(tmpdir)

    def test_reports_python_version(self):
        probe = PyCFDEnvironmentProbeComponent(pycfd_src_path="/nonexistent/path")
        report = probe.probe(task_id="test")
        assert report.python_version is not None
