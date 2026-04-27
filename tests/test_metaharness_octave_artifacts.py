from metaharness_ext.octave.artifacts import OctaveArtifactDetector, OctaveMATFileParser
from metaharness_ext.octave.contracts import OctaveOutputSpec
from metaharness_ext.octave.scheduler.workspace_sync import build_workspace_sync_plan


def test_octave_artifact_detector_reports_found_missing_and_unexpected(tmp_path) -> None:
    outputs = tmp_path / "outputs"
    outputs.mkdir()
    (outputs / "result.txt").write_text("1")
    (outputs / "extra.csv").write_text("x,y")
    specs = [
        OctaveOutputSpec(name="result", variable_name="result"),
        OctaveOutputSpec(name="figure", kind="figure", file_name="plot.png"),
    ]

    discovery = OctaveArtifactDetector().detect(tmp_path, specs)

    assert discovery.found == [str(outputs / "result.txt")]
    assert discovery.missing == ["plot.png"]
    assert discovery.unexpected == [str(outputs / "extra.csv")]


def test_octave_mat_parser_degrades_without_required_runtime_failure(tmp_path) -> None:
    mat_path = tmp_path / "sample.mat"
    mat_path.write_text("not a real mat file")

    try:
        summary = OctaveMATFileParser().parse(mat_path)
    except Exception as error:
        assert error.__class__.__name__ in {"MatReadError", "ValueError", "IndexError"}
    else:
        assert summary.path == str(mat_path)


def test_octave_workspace_sync_plan_lists_relative_files(tmp_path) -> None:
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "input.dat").write_text("data")

    plan = build_workspace_sync_plan(tmp_path, "/cluster/work")

    assert plan.files == ["a/input.dat"]
    assert plan.destination == "/cluster/work"
