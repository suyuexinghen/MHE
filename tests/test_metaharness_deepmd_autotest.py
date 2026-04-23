from __future__ import annotations

from pathlib import Path

import pytest

from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.deepmd.contracts import (
    DeepMDDiagnosticSummary,
    DeepMDExecutableSpec,
    DeepMDRunArtifact,
    DeepMDValidationReport,
    DPGenAutotestSpec,
    DPGenMachineSpec,
)
from metaharness_ext.deepmd.diagnostics import parse_autotest_results
from metaharness_ext.deepmd.executor import DeepMDExecutorComponent
from metaharness_ext.deepmd.train_config_compiler import DeepMDTrainConfigCompilerComponent
from metaharness_ext.deepmd.validator import DeepMDValidatorComponent


class _FakeCompletedProcess:
    def __init__(self, *, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _build_autotest_spec(
    task_id: str = "autotest-task",
    properties: list[str] | None = None,
) -> DPGenAutotestSpec:
    return DPGenAutotestSpec(
        task_id=task_id,
        executable=DeepMDExecutableSpec(binary_name="dpgen", execution_mode="dpgen_autotest"),
        param={"type": "eos"},
        machine=DPGenMachineSpec(),
        properties=properties or ["eos"],
    )


def test_autotest_spec_requires_dpgen_autotest_mode() -> None:
    with pytest.raises(ValueError, match="dpgen_autotest"):
        DPGenAutotestSpec(
            task_id="bad",
            executable=DeepMDExecutableSpec(binary_name="dpgen", execution_mode="dpgen_run"),
            param={"type": "eos"},
        )


def test_autotest_spec_requires_non_empty_param() -> None:
    with pytest.raises(ValueError, match="param must not be empty"):
        DPGenAutotestSpec(
            task_id="bad",
            executable=DeepMDExecutableSpec(binary_name="dpgen", execution_mode="dpgen_autotest"),
        )


def test_compiler_builds_autotest_plan() -> None:
    spec = _build_autotest_spec()
    compiler = DeepMDTrainConfigCompilerComponent()
    plan = compiler.build_plan(spec)

    assert plan.execution_mode == "dpgen_autotest"
    assert plan.command == ["dpgen", "autotest", "param.json", "machine.json"]
    assert plan.expected_outputs == ["result.out", "result.json"]
    assert plan.expected_diagnostics == ["result.out", "result.json"]
    assert plan.param_json_path is not None
    assert plan.machine_json_path is not None


@pytest.mark.asyncio
async def test_executor_builds_autotest_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = _build_autotest_spec()
    plan = DeepMDTrainConfigCompilerComponent().build_plan(spec)
    executor = DeepMDExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr(
        "metaharness_ext.deepmd.executor.shutil.which", lambda binary: f"/usr/bin/{binary}"
    )

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        return _FakeCompletedProcess(returncode=0, stdout="autotest ok", stderr="")

    monkeypatch.setattr("metaharness_ext.deepmd.executor.subprocess.run", fake_run)

    artifact = executor.execute_plan(plan)

    assert artifact.command == ["/usr/bin/dpgen", "autotest", "param.json", "machine.json"]
    assert artifact.status == "completed"


def test_parse_autotest_result_json(tmp_path: Path) -> None:
    result_file = tmp_path / "result.json"
    result_file.write_text(
        '{"eos": {"a": 3.5, "b": 4.2}, "elastic": {"c11": 120.5}, "summary": {"pass": 1}}'
    )
    summary = DeepMDDiagnosticSummary()
    parse_autotest_results(result_file, summary)

    assert "eos" in summary.autotest_properties
    assert summary.autotest_properties["eos"]["a"] == pytest.approx(3.5)
    assert summary.autotest_properties["elastic"]["c11"] == pytest.approx(120.5)


def test_parse_autotest_result_out(tmp_path: Path) -> None:
    result_file = tmp_path / "result.out"
    result_file.write_text("# eos\na  3.5\nb  4.2\n# elastic\nc11  120.5\n")
    summary = DeepMDDiagnosticSummary()
    parse_autotest_results(result_file, summary)

    assert "eos" in summary.autotest_properties
    assert summary.autotest_properties["eos"]["a"] == pytest.approx(3.5)
    assert summary.autotest_properties["elastic"]["c11"] == pytest.approx(120.5)


def test_validator_passes_with_autotest_properties() -> None:
    artifact = DeepMDRunArtifact(
        task_id="task-1",
        run_id="run-1",
        execution_mode="dpgen_autotest",
        command=["dpgen", "autotest"],
        return_code=0,
        stdout_path="/tmp/stdout.log",
        stderr_path="/tmp/stderr.log",
        working_directory="/tmp/run",
        summary=DeepMDDiagnosticSummary(autotest_properties={"eos": {"a": 3.5}}),
        status="completed",
        result_summary={"exit_code": 0},
    )

    report = DeepMDValidatorComponent().validate_run(artifact)

    assert report.passed is True
    assert report.status == "autotest_validated"
    assert report.summary_metrics["eos_a"] == pytest.approx(3.5)
    assert "Autotest produced structured property results" in report.messages[0]


def test_validator_fails_without_autotest_properties() -> None:
    artifact = DeepMDRunArtifact(
        task_id="task-1",
        run_id="run-1",
        execution_mode="dpgen_autotest",
        command=["dpgen", "autotest"],
        return_code=0,
        stdout_path="/tmp/stdout.log",
        stderr_path="/tmp/stderr.log",
        working_directory="/tmp/run",
        summary=DeepMDDiagnosticSummary(),
        status="completed",
        result_summary={"exit_code": 0},
    )

    report = DeepMDValidatorComponent().validate_run(artifact)

    assert report.passed is False
    assert report.status == "validation_failed"


def test_parse_autotest_result_json_filters_by_properties(tmp_path: Path) -> None:
    result_file = tmp_path / "result.json"
    result_file.write_text('{"eos": {"a": 3.5}, "elastic": {"c11": 120.5}, "bulk": {"b": 2.0}}')
    summary = DeepMDDiagnosticSummary()
    parse_autotest_results(result_file, summary, properties=["eos"])

    assert "eos" in summary.autotest_properties
    assert "elastic" not in summary.autotest_properties
    assert "bulk" not in summary.autotest_properties


def test_parse_autotest_result_json_deep_nesting(tmp_path: Path) -> None:
    result_file = tmp_path / "result.json"
    result_file.write_text('{"eos": {"lattice": {"a": 3.5, "b": 4.2}, "energy": 1.2}}')
    summary = DeepMDDiagnosticSummary()
    parse_autotest_results(result_file, summary)

    assert "eos" in summary.autotest_properties
    assert summary.autotest_properties["eos"]["lattice_a"] == pytest.approx(3.5)
    assert summary.autotest_properties["eos"]["lattice_b"] == pytest.approx(4.2)
    assert summary.autotest_properties["eos"]["energy"] == pytest.approx(1.2)


def test_parse_autotest_result_out_presummary_lines(tmp_path: Path) -> None:
    result_file = tmp_path / "result.out"
    result_file.write_text("overall  99.5\n# eos\na  3.5\n")
    summary = DeepMDDiagnosticSummary()
    parse_autotest_results(result_file, summary)

    assert "summary" in summary.autotest_properties
    assert summary.autotest_properties["summary"]["overall"] == pytest.approx(99.5)
    assert summary.autotest_properties["eos"]["a"] == pytest.approx(3.5)


def test_validation_report_status_literal_includes_autotest() -> None:
    report = DeepMDValidationReport(
        task_id="t",
        run_id="r",
        passed=True,
        status="autotest_validated",
    )
    assert report.status == "autotest_validated"
