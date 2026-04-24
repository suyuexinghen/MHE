from __future__ import annotations

import json
from pathlib import Path

from metaharness import cli
from metaharness.config.xml_parser import parse_graph_xml
from metaharness.core.models import PendingConnectionSet
from metaharness_ext.ai4pde.demo import AI4PDECaseDemoHarness

CASE_XML = Path(__file__).parent.parent / "docs" / "xml-demo" / "cylinder-flow-re100.xml"


def test_ai4pde_case_demo_harness_runs_through_runtime_boot_and_commit(monkeypatch) -> None:
    harness = AI4PDECaseDemoHarness(root=Path(__file__).resolve().parents[1])
    boot_calls: list[str] = []
    commit_calls: list[tuple[str, PendingConnectionSet]] = []

    original_boot = harness.runtime.boot
    original_commit_graph = harness.runtime.commit_graph

    def boot_wrapper():
        boot_calls.append("boot")
        return original_boot()

    def commit_wrapper(pending: PendingConnectionSet, *, candidate_id: str = "boot-graph") -> int:
        commit_calls.append((candidate_id, pending))
        return original_commit_graph(pending, candidate_id=candidate_id)

    monkeypatch.setattr(harness.runtime, "boot", boot_wrapper)
    monkeypatch.setattr(harness.runtime, "commit_graph", commit_wrapper)

    result = harness.run_case(CASE_XML)

    expected_snapshot = parse_graph_xml(harness.graphs_dir / "ai4pde-expanded.xml")

    assert boot_calls == ["boot"]
    assert len(commit_calls) == 1
    candidate_id, pending = commit_calls[0]
    assert candidate_id == "ai4pde-expanded"
    assert pending.nodes == expected_snapshot.nodes
    assert pending.edges == expected_snapshot.edges
    assert result.graph_version == 1
    assert result.task.task_id == "cylinder-flow-re100"
    assert result.plan.selected_method.value == "classical_hybrid"
    assert result.run_artifact.result_summary["backend"] == "nektar++"
    assert result.validation_bundle.reference_comparison["status"] == "better_or_equal"
    assert (
        result.evidence_bundle.graph_metadata["graph_family"] == "template::forward-fluid-mechanics"
    )
    assert result.memory_record["benchmark_snapshots"] == "1"


def test_ai4pde_case_cli_command_outputs_json(capsys) -> None:
    exit_code = cli.main(["ai4pde-case", str(CASE_XML)])

    assert exit_code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["task"]["task_id"] == "cylinder-flow-re100"
    assert payload["plan"]["selected_method"] == "classical_hybrid"
    assert payload["run_artifact"]["result_summary"]["backend"] == "nektar++"
    assert payload["validation_bundle"]["reference_comparison"]["status"] == "better_or_equal"


def test_validate_case_cli_command_outputs_summary(capsys) -> None:
    exit_code = cli.main(["validate-case", str(CASE_XML)])

    assert exit_code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["status"] == "ok"
    assert payload["task_id"] == "cylinder-flow-re100"
    assert payload["selected_method"] == "classical_hybrid"
    assert payload["graph_family"] == "template::forward-fluid-mechanics"


def test_validate_case_cli_command_reports_parser_errors(tmp_path: Path, capsys) -> None:
    broken_case = tmp_path / "broken-case.xml"
    broken_case.write_text(CASE_XML.read_text().replace("<Problem", "<ProblemX", 1))

    exit_code = cli.main(["validate-case", str(broken_case)])

    assert exit_code == 2
    captured = capsys.readouterr()
    assert "case validation failed:" in captured.err
