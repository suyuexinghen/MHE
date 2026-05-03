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
    assert (tmp_path / "review.json").exists()
    assert (tmp_path / "research_dossier.json").exists()
    assert (tmp_path / "conclusion.json").exists()
    assert (tmp_path / "artifact_manifest.json").exists()
    assert payload["scope"] == "deterministic benchmark-backed MVP research loop"
    assert "solver superiority" in payload["non_claims"]

    evidence = json.loads((tmp_path / "evidence_bundle.json").read_text())
    assert evidence["supports"] == ["h-rq-fealpy-poisson-l2-threshold"]
    assert evidence["refutes"] == []
    assert evidence["artifact_refs"] == [str(FIXTURES / "fealpy_poisson_summary_passed.json")]
    review = json.loads((tmp_path / "review.json").read_text())
    assert review["recommendation"] == "ADVANCE"
    assert review["reasoning"] == "evidence supports the hypothesis metric threshold"
    dossier = json.loads((tmp_path / "research_dossier.json").read_text())
    assert dossier["claims"][0]["evidence_bundle_ids"] == [evidence["bundle_id"]]
    assert dossier["claims"][0]["reproducibility_tier"] == "deterministic"
    manifest = json.loads((tmp_path / "artifact_manifest.json").read_text())
    assert manifest["source_inputs"]["benchmark_summary"] == str(
        FIXTURES / "fealpy_poisson_summary_passed.json"
    )
    assert manifest["derived_records"]["review_id"] == review["review_id"]
    assert manifest["artifacts"]["dossier"] == str(tmp_path / "research_dossier.json")


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
    review = json.loads((tmp_path / "review.json").read_text())
    assert review["recommendation"] == "REFINE"
    assert review["reasoning"] == "evidence is inconclusive for the hypothesis"
    conclusion = json.loads((tmp_path / "conclusion.json").read_text())
    assert conclusion["supported_hypotheses"] == []
    assert conclusion["refuted_hypotheses"] == []
    assert conclusion["status"] == "active"
    dossier = json.loads((tmp_path / "research_dossier.json").read_text())
    assert dossier["claims"] == []
    assert dossier["conclusion"]["supported_hypotheses"] == []
    assert dossier["conclusion"]["refuted_hypotheses"] == []
    assert dossier["conclusion"]["status"] == "active"
    assert dossier["negative_result_clusters"][0]["failure_category"] == "runner_error"
    manifest = json.loads((tmp_path / "artifact_manifest.json").read_text())
    assert "open-ended discovery loop" in manifest["non_claims"]


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


def test_research_run_cli_supports_multi_summary_and_sidecars(tmp_path: Path, capsys) -> None:
    status = main(
        [
            "research-run",
            "--question",
            str(QUESTION),
            "--summary",
            str(FIXTURES / "fealpy_poisson_summary_passed.json"),
            "--summary",
            str(FIXTURES / "fealpy_poisson_summary_failed.json"),
            "--runs-root",
            str(tmp_path),
        ]
    )

    assert status == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["decision"] == "ADVANCE"
    assert payload["decisions"] == ["ADVANCE", "REFINE"]
    assert (tmp_path / "hypotheses.json").exists()
    assert (tmp_path / "experiment_plans.json").exists()
    assert (tmp_path / "evidence_bundles.json").exists()
    assert (tmp_path / "decisions.json").exists()
    assert (tmp_path / "reviews.json").exists()
    assert (tmp_path / "metric_schema.json").exists()
    assert (tmp_path / "sota_baselines.json").exists()
    assert (tmp_path / "reproducibility_summary.json").exists()
    manifest = json.loads((tmp_path / "artifact_manifest.json").read_text())
    assert len(manifest["source_inputs"]["benchmark_summaries"]) == 2
    assert len(manifest["derived_records"]["hypothesis_ids"]) == 2


def test_research_run_cli_can_handoff_from_benchmark_output(tmp_path: Path, capsys) -> None:
    benchmark_runs_root = tmp_path / "benchmark"
    summary_dir = benchmark_runs_root / "fealpy-pde-benchmark" / "extension" / "poisson-2d-numpy"
    summary_dir.mkdir(parents=True, exist_ok=True)
    summary_path = summary_dir / "summary.json"
    summary_path.write_text((FIXTURES / "fealpy_poisson_summary_passed.json").read_text())

    status = main(
        [
            "research-run",
            "--question",
            str(QUESTION),
            "--benchmark-runs-root",
            str(benchmark_runs_root),
            "--suite",
            "fealpy-pde",
            "--cases",
            "poisson-2d-numpy",
            "--lanes",
            "extension",
            "--runs-root",
            str(tmp_path / "handoff"),
        ]
    )

    assert status == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["decision"] == "ADVANCE"
    manifest = json.loads((tmp_path / "handoff" / "artifact_manifest.json").read_text())
    assert manifest["source_inputs"]["benchmark_handoff"] is True
    assert manifest["source_inputs"]["benchmark_runs_roots"] == [str(benchmark_runs_root)]
    assert manifest["source_inputs"]["benchmark_summary"] == str(summary_path)


def test_research_run_cli_supports_text_output_and_trace_printing(tmp_path: Path, capsys) -> None:
    status = main(
        [
            "research-run",
            "--question",
            str(QUESTION),
            "--summary",
            str(FIXTURES / "fealpy_poisson_summary_passed.json"),
            "--runs-root",
            str(tmp_path),
            "--output-format",
            "text",
            "--print-trace",
        ]
    )

    assert status == 0
    output = capsys.readouterr().out
    assert "ADVANCE" in output
    assert "rq-fealpy-poisson-l2-threshold" in output
    manifest = json.loads((tmp_path / "artifact_manifest.json").read_text())
    assert manifest["derived_records"]["review_id"]


def test_research_run_cli_merges_negative_memory_sidecars(tmp_path: Path, capsys) -> None:
    negative_memory = tmp_path / "negative_result_memory.json"
    negative_memory.write_text(
        json.dumps(
            {
                "schema": "metaharness.negative_result_memory.v1",
                "clusters": [
                    {
                        "cluster_id": "negative-shared",
                        "question_ids": ["rq-prior"],
                        "domain_tags": {"suite": "fealpy-pde"},
                        "metric_schema": "l2_error",
                        "failure_category": "runner_error",
                        "evidence_bundle_ids": ["ev-prior"],
                        "refuted_hypothesis_ids": ["h-prior"],
                        "repeated_dead_end": False,
                    }
                ],
            }
        )
        + "\n"
    )

    status = main(
        [
            "research-run",
            "--question",
            str(QUESTION),
            "--summary",
            str(FIXTURES / "fealpy_poisson_summary_failed.json"),
            "--runs-root",
            str(tmp_path / "out"),
            "--negative-memory",
            str(negative_memory),
        ]
    )

    assert status == 0
    capsys.readouterr()
    memory = json.loads((tmp_path / "out" / "negative_result_memory.json").read_text())
    assert memory["schema"] == "metaharness.negative_result_memory.v1"
    shared = next(
        cluster for cluster in memory["clusters"] if cluster["cluster_id"] == "negative-shared"
    )
    assert "rq-prior" in shared["question_ids"]
    assert shared["repeated_dead_end"] is False
