from __future__ import annotations

from metaharness_ext.boutpp.contracts import BoutPPRunArtifact
from metaharness_ext.boutpp.postprocess import BoutPPPostprocessComponent


def test_postprocess_parses_logs_and_settings(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    settings = data_dir / "BOUT.settings"
    settings.write_text("[solver]\ntype = rk4\n")
    log = data_dir / "BOUT.log.0"
    log.write_text("Run finished\nRun time : 2 s\nStep 10 of 10\n")
    dump = data_dir / "BOUT.dmp.0.nc"
    dump.write_text("dump")
    artifact = BoutPPRunArtifact(
        artifact_id="a1",
        run_id="r1",
        task_id="t1",
        plan_ref="p1",
        status="completed",
        settings_file=str(settings),
        log_files=[str(log)],
        dump_files=[str(dump)],
    )
    report = BoutPPPostprocessComponent().postprocess(artifact)
    assert report.status in {"completed", "partial"}
    assert report.settings_summary["solver.type"] == "rk4"
    assert report.summary_metrics["runtime_seconds"] == 2.0
    assert report.summary_metrics["log_file_count"] == 1


def test_postprocess_unavailable_for_unavailable_artifact():
    artifact = BoutPPRunArtifact(artifact_id="a1", run_id="r1", task_id="t1", plan_ref="p1")
    report = BoutPPPostprocessComponent().postprocess(artifact)
    assert report.status == "unavailable"
