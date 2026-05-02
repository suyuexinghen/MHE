from __future__ import annotations

import json
from pathlib import Path

from metaharness.cli import main

FIXTURES = Path(__file__).parent / "fixtures" / "research"
QUESTION = Path("examples/research/fealpy_poisson_question.json")


def test_research_run_cli_writes_traceable_artifacts(tmp_path: Path, capsys) -> None:
    status = main(
        [
            "research-run",
            "--question",
            str(QUESTION),
            "--summary",
            str(FIXTURES / "fealpy_poisson_summary_passed.json"),
            "--runs-root",
            str(tmp_path),
        ]
    )

    assert status == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["question_id"] == "rq-fealpy-poisson-l2-threshold"
    assert payload["decision"] == "ADVANCE"
    assert (tmp_path / "research_trace.jsonl").exists()
    assert (tmp_path / "research_question.json").exists()
    assert (tmp_path / "hypothesis.json").exists()
    assert (tmp_path / "experiment_plan.json").exists()
    assert (tmp_path / "evidence_bundle.json").exists()
    assert (tmp_path / "decision.json").exists()
    assert (tmp_path / "conclusion.json").exists()

    evidence = json.loads((tmp_path / "evidence_bundle.json").read_text())
    assert evidence["supports"] == ["h-rq-fealpy-poisson-l2-threshold"]
    assert evidence["refutes"] == []
    assert evidence["artifact_refs"] == [str(FIXTURES / "fealpy_poisson_summary_passed.json")]


def test_research_run_cli_preserves_execution_failure_without_refuting(
    tmp_path: Path, capsys
) -> None:
    status = main(
        [
            "research-run",
            "--question",
            str(QUESTION),
            "--summary",
            str(FIXTURES / "fealpy_poisson_summary_failed.json"),
            "--runs-root",
            str(tmp_path),
        ]
    )

    assert status == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["decision"] == "REFINE"
    evidence = json.loads((tmp_path / "evidence_bundle.json").read_text())
    assert evidence["status"] == "failed"
    assert evidence["failure_category"] == "runner_error"
    assert evidence["supports"] == []
    assert evidence["refutes"] == []


def test_research_run_cli_rejects_invalid_question(tmp_path: Path, capsys) -> None:
    bad_question = tmp_path / "bad-question.json"
    bad_question.write_text('{"question_id": "rq"}\n')

    status = main(
        [
            "research-run",
            "--question",
            str(bad_question),
            "--summary",
            str(FIXTURES / "fealpy_poisson_summary_passed.json"),
            "--runs-root",
            str(tmp_path / "out"),
        ]
    )

    captured = capsys.readouterr()
    assert status == 2
    assert "research-run input error" in captured.err
    assert not (tmp_path / "out" / "conclusion.json").exists()
