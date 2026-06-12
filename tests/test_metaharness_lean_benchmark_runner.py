from __future__ import annotations

import json
from pathlib import Path

from metaharness.benchmark_drivers.claude_cli import FakeClaudeCLIBrainProvider
from metaharness.benchmark_drivers.compare import write_comparison_outputs
from metaharness.cli import main
from metaharness_ext.lean.benchmark_cases import get_lean_proof_cases
from metaharness_ext.lean.benchmark_runner import LeanProofBenchmarkRunner


def test_lean_proof_catalog_includes_simple_true_case() -> None:
    case = get_lean_proof_cases(["simple-true-proof"])[0]

    assert case.suite == "lean-proof"
    assert case.problem_definition["target_lemma"] == "main"
    assert "theorem main" in case.problem_definition["lean_source"]


def test_lean_proof_catalog_includes_next_evidence_cases() -> None:
    cases = {case.case_id: case for case in get_lean_proof_cases()}

    assert "implication-chain-proof" in cases
    assert "conjunction-swap-proof" in cases
    assert "negation-contrapositive-proof" in cases
    assert "exists-conjunction-swap-proof" in cases
    assert "malformed-proposal-repair" in cases
    assert "underspecified-real-claude-stress" in cases
    assert "malformed-json-real-claude-stress" in cases
    assert "sorry-proof-real-claude-stress" in cases
    assert "project-helper-chain-proof" in cases
    assert "blueprint-structure-project-proof" in cases
    assert "mathlib-add-zero-sentinel" in cases
    assert (
        cases["implication-chain-proof"].metadata["challenge_kind"] == "positive_nontrivial_proof"
    )
    assert cases["negation-contrapositive-proof"].metadata["human_math_review"] == (
        "pending_external_signoff"
    )
    assert cases["negation-contrapositive-proof"].metadata["external_review_required"] is True
    assert cases["malformed-proposal-repair"].metadata["direct_fake_fallback_enabled"] is False
    assert cases["underspecified-real-claude-stress"].metadata["direct_prompt_style"] == (
        "natural_language_noncontract"
    )
    assert cases["malformed-json-real-claude-stress"].metadata["direct_prompt_style"] == (
        "json_missing_lean_source"
    )
    assert cases["sorry-proof-real-claude-stress"].metadata["direct_prompt_style"] == (
        "json_with_sorry_source"
    )
    assert "Helper.lean" in cases["project-helper-chain-proof"].problem_definition["project_files"]
    assert (
        "Blueprint/Proof.lean"
        in cases["blueprint-structure-project-proof"].problem_definition["project_files"]
    )
    assert cases["mathlib-add-zero-sentinel"].capability_gated is True
    assert cases["mathlib-add-zero-sentinel"].metadata["mathlib_scale_claim"] == (
        "dependency_gated_not_promoted"
    )


def test_lean_proof_dry_run_writes_three_lane_outputs(tmp_path: Path) -> None:
    case = get_lean_proof_cases(["simple-true-proof"])[0]
    runner = LeanProofBenchmarkRunner(runs_root=tmp_path)

    summaries = runner.run_case(case, ["extension", "direct", "agent"])
    rows = write_comparison_outputs(
        runs_root=tmp_path,
        suite="lean-proof",
        cases=[case.case_id],
        lanes=["extension", "direct", "agent"],
    )

    assert [summary.lane for summary in summaries] == ["extension", "direct", "agent"]
    assert all(summary.status == "passed" for summary in summaries)
    assert rows[0].verdict == "all_passed"
    suite_root = tmp_path / "lean-proof-benchmark"
    assert (suite_root / "extension" / case.case_id / "lean_evidence_bundle.json").exists()
    assert (suite_root / "direct" / case.case_id / "lean_proposal_contract.json").exists()
    assert (suite_root / "agent" / case.case_id / "lean_proposal_contract.json").exists()


def test_lean_proof_runner_accepts_valid_claude_proposals(tmp_path: Path) -> None:
    case = get_lean_proof_cases(["simple-true-proof"])[0]
    provider = FakeClaudeCLIBrainProvider(
        {
            "target_lemma": "main",
            "lean_source": "theorem main : True := by\n  trivial\n",
        }
    )
    runner = LeanProofBenchmarkRunner(runs_root=tmp_path, brain_provider=provider)

    summaries = runner.run_case(case, ["direct", "agent"])

    assert all(summary.proposal_contract_status == "valid" for summary in summaries)
    assert all(summary.status == "passed" for summary in summaries)


def test_lean_proof_runner_accepts_implication_chain_proposal(tmp_path: Path) -> None:
    case = get_lean_proof_cases(["implication-chain-proof"])[0]
    provider = FakeClaudeCLIBrainProvider(
        {
            "target_lemma": "main",
            "lean_source": "theorem main (p q : Prop) (hp : p) (hpq : p -> q) : q := by\n  exact hpq hp\n",
        }
    )
    runner = LeanProofBenchmarkRunner(runs_root=tmp_path, brain_provider=provider)

    summaries = runner.run_case(case, ["direct", "agent"])

    assert all(summary.proposal_contract_status == "valid" for summary in summaries)
    assert all(summary.status == "passed" for summary in summaries)


def test_lean_proof_runner_accepts_conjunction_swap_proposal(tmp_path: Path) -> None:
    case = get_lean_proof_cases(["conjunction-swap-proof"])[0]
    provider = FakeClaudeCLIBrainProvider(
        {
            "target_lemma": "main",
            "lean_source": case.problem_definition["lean_source"],
        }
    )
    runner = LeanProofBenchmarkRunner(runs_root=tmp_path, brain_provider=provider)

    summaries = runner.run_case(case, ["direct", "agent"])

    assert all(summary.proposal_contract_status == "valid" for summary in summaries)
    assert all(summary.status == "passed" for summary in summaries)


def test_lean_proof_runner_accepts_curated_harder_proposals(tmp_path: Path) -> None:
    cases = get_lean_proof_cases(["negation-contrapositive-proof", "exists-conjunction-swap-proof"])
    for case in cases:
        provider = FakeClaudeCLIBrainProvider(
            {
                "target_lemma": "main",
                "lean_source": case.problem_definition["lean_source"],
            }
        )
        runner = LeanProofBenchmarkRunner(
            runs_root=tmp_path / case.case_id, brain_provider=provider
        )

        summaries = runner.run_case(case, ["direct", "agent"])

        assert all(summary.proposal_contract_status == "valid" for summary in summaries)
        assert all(summary.status == "passed" for summary in summaries)
        manifest = (
            tmp_path
            / case.case_id
            / "lean-proof-benchmark"
            / "direct"
            / case.case_id
            / "lean_human_review_manifest.json"
        )
        assert json.loads(manifest.read_text())["external_review_status"] == (
            "pending_external_signoff"
        )
        write_comparison_outputs(
            runs_root=tmp_path / case.case_id,
            suite="lean-proof",
            cases=[case.case_id],
            lanes=["direct", "agent"],
        )
        bundle = json.loads(
            (
                tmp_path
                / case.case_id
                / "lean-proof-benchmark"
                / "comparison"
                / "result_bundle.json"
            ).read_text()
        )
        assert (
            bundle["evidence_context"]["review_manifest_rows"][0]["external_review_status"]
            == "pending_external_signoff"
        )


def test_lean_proof_stress_prompts_expose_agent_repair_advantage(tmp_path: Path) -> None:
    cases = get_lean_proof_cases(
        [
            "underspecified-real-claude-stress",
            "malformed-json-real-claude-stress",
            "sorry-proof-real-claude-stress",
        ]
    )
    for case in cases:
        runner = LeanProofBenchmarkRunner(runs_root=tmp_path / case.case_id)

        summaries = runner.run_case(case, ["extension", "direct", "agent"])
        rows = write_comparison_outputs(
            runs_root=tmp_path / case.case_id,
            suite="lean-proof",
            cases=[case.case_id],
            lanes=["extension", "direct", "agent"],
        )

        assert [summary.status for summary in summaries] == ["passed", "failed", "passed"]
        assert summaries[1].proposal_contract_status == "invalid"
        assert summaries[2].repair_outcome == "repaired_success"
        assert rows[0].verdict == "agent_repaired_success"


def test_lean_proof_runner_accepts_project_helper_proposal(tmp_path: Path) -> None:
    case = get_lean_proof_cases(["project-helper-chain-proof"])[0]
    provider = FakeClaudeCLIBrainProvider(
        {
            "target_lemma": "main",
            "lean_source": case.problem_definition["lean_source"],
        }
    )
    runner = LeanProofBenchmarkRunner(runs_root=tmp_path, brain_provider=provider)

    summaries = runner.run_case(case, ["direct", "agent"])

    assert all(summary.proposal_contract_status == "valid" for summary in summaries)
    assert all(summary.status == "passed" for summary in summaries)


def test_lean_proof_malformed_proposal_exposes_agent_repair_advantage(
    tmp_path: Path,
) -> None:
    case = get_lean_proof_cases(["malformed-proposal-repair"])[0]
    runner = LeanProofBenchmarkRunner(runs_root=tmp_path)

    summaries = runner.run_case(case, ["extension", "direct", "agent"])
    rows = write_comparison_outputs(
        runs_root=tmp_path,
        suite="lean-proof",
        cases=[case.case_id],
        lanes=["extension", "direct", "agent"],
    )

    assert [summary.status for summary in summaries] == ["passed", "failed", "passed"]
    assert summaries[1].proposal_contract_status == "invalid"
    assert summaries[1].failure_category == "proposal_contract_failed"
    assert summaries[2].proposal_contract_status == "valid"
    assert summaries[2].repair_count == 1
    assert summaries[2].repair_outcome == "repaired_success"
    assert rows[0].verdict == "agent_repaired_success"

    bundle = json.loads(
        (tmp_path / "lean-proof-benchmark" / "comparison" / "result_bundle.json").read_text()
    )
    repair_row = bundle["evidence_context"]["repair_rows"][0]
    assert repair_row["repair_advantage"] == "agent_repaired_direct_failure"
    assert bundle["evidence_context"]["proposal_sources"][case.case_id]["agent"] == (
        "agent_repair_from_case_defaults"
    )


def test_lean_proof_runner_accepts_blueprint_project_proposal(tmp_path: Path) -> None:
    case = get_lean_proof_cases(["blueprint-structure-project-proof"])[0]
    provider = FakeClaudeCLIBrainProvider(
        {
            "target_lemma": "main",
            "lean_source": case.problem_definition["lean_source"],
        }
    )
    runner = LeanProofBenchmarkRunner(runs_root=tmp_path, brain_provider=provider)

    summaries = runner.run_case(case, ["direct", "agent"])

    assert all(summary.proposal_contract_status == "valid" for summary in summaries)
    assert all(summary.status == "passed" for summary in summaries)


def test_lean_proof_mathlib_sentinel_writes_dependency_gate(tmp_path: Path) -> None:
    case = get_lean_proof_cases(["mathlib-add-zero-sentinel"])[0]
    runner = LeanProofBenchmarkRunner(runs_root=tmp_path)

    summaries = runner.run_case(case, ["extension", "direct", "agent"])
    rows = write_comparison_outputs(
        runs_root=tmp_path,
        suite="lean-proof",
        cases=[case.case_id],
        lanes=["extension", "direct", "agent"],
    )

    assert [summary.status for summary in summaries] == ["skipped", "skipped", "skipped"]
    assert all(summary.preflight_status == "blocked" for summary in summaries)
    assert rows[0].verdict == "capability_skip"
    case_root = tmp_path / "lean-proof-benchmark" / "extension" / case.case_id
    gate = json.loads((case_root / "capability_status.json").read_text())
    source_refs = json.loads((case_root / "source_refs.json").read_text())
    assert gate["missing_capabilities"] == ["mathlib_dependency_gate"]
    assert gate["promotion_ready"] is False
    assert source_refs["requires_mathlib"] is True
    bundle = json.loads(
        (tmp_path / "lean-proof-benchmark" / "comparison" / "result_bundle.json").read_text()
    )
    family_rows = bundle["evidence_context"]["theorem_family_repeat_rows"]
    by_family_lane = {(row["theorem_family"], row["lane"]): row for row in family_rows}
    assert by_family_lane[("mathlib_sentinel", "direct")]["skipped_count"] == 1
    assert by_family_lane[("mathlib_sentinel", "direct")]["failed_count"] == 0


def test_lean_proof_real_extension_lane_executes_when_allowed(tmp_path: Path) -> None:
    case = get_lean_proof_cases(["simple-true-proof"])[0]
    runner = LeanProofBenchmarkRunner(runs_root=tmp_path, allow_real_tools=True)

    summary = runner.run_extension(case)

    if summary.status == "skipped":
        capability = json.loads(
            (
                tmp_path
                / "lean-proof-benchmark"
                / "extension"
                / case.case_id
                / "capability_status.json"
            ).read_text()
        )
        assert capability["promotion_ready"] is False
        assert capability["missing_capabilities"]
    else:
        assert summary.status == "passed"
        assert summary.preflight_status == "passed"
        assert summary.metrics["proof_status"] == 1.0


def test_lean_proof_project_fixtures_write_dependency_files_for_real_lane(
    tmp_path: Path,
) -> None:
    cases = get_lean_proof_cases(
        ["project-helper-chain-proof", "blueprint-structure-project-proof"]
    )
    for case in cases:
        runner = LeanProofBenchmarkRunner(runs_root=tmp_path / case.case_id, allow_real_tools=True)

        summary = runner.run_extension(case)

        case_root = tmp_path / case.case_id / "lean-proof-benchmark" / "extension" / case.case_id
        if summary.status == "skipped":
            capability = json.loads((case_root / "capability_status.json").read_text())
            assert capability["promotion_ready"] is False
        else:
            assert summary.status == "passed"
            for relative_path in case.problem_definition["project_files"]:
                assert (case_root / "lean_project" / relative_path).exists()
            assert summary.metrics["proof_status"] == 1.0


def test_lean_proof_cli_runs_dry_run_suite(tmp_path: Path, capsys) -> None:
    status = main(
        [
            "benchmark-run",
            "--suite",
            "lean-proof",
            "--lanes",
            "extension,direct,agent",
            "--cases",
            "simple-true-proof",
            "--runs-root",
            str(tmp_path),
        ]
    )

    assert status == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["suite"] == "lean-proof"
    assert payload["cases"] == ["simple-true-proof"]
    assert (
        tmp_path / "lean-proof-benchmark" / "extension" / "simple-true-proof" / "summary.json"
    ).exists()


def test_lean_proof_cli_compare_reports_theorem_family_rates(tmp_path: Path, capsys) -> None:
    run_status = main(
        [
            "benchmark-run",
            "--suite",
            "lean-proof",
            "--lanes",
            "extension,direct,agent",
            "--cases",
            "malformed-proposal-repair,underspecified-real-claude-stress",
            "--runs-root",
            str(tmp_path),
            "--repeat",
            "2",
        ]
    )
    capsys.readouterr()
    compare_status = main(
        [
            "benchmark-compare",
            "--suite",
            "lean-proof",
            "--runs-root",
            str(tmp_path),
            "--repeat",
            "2",
        ]
    )

    assert run_status == 0
    assert compare_status == 0
    capsys.readouterr()
    bundle = json.loads(
        (tmp_path / "lean-proof-benchmark" / "comparison" / "result_bundle.json").read_text()
    )
    family_rows = bundle["evidence_context"]["theorem_family_repeat_rows"]
    by_family_lane = {(row["theorem_family"], row["lane"]): row for row in family_rows}
    assert by_family_lane[("stress_prompt", "direct")]["invalid_contract_rate"] == 1.0
    assert by_family_lane[("stress_prompt", "agent")]["valid_contract_rate"] == 1.0
    assert by_family_lane[("contract_repair", "agent")]["repair_rate"] == 1.0
    report = (tmp_path / "lean-proof-benchmark" / "comparison" / "comparison_report.md").read_text()
    assert "Theorem-family proposal statistics" in report


def test_lean_proof_cli_compare_accepts_config_root(tmp_path: Path, capsys) -> None:
    run_status = main(
        [
            "benchmark-run",
            "--suite",
            "lean-proof",
            "--lanes",
            "extension,direct,agent",
            "--cases",
            "simple-true-proof",
            "--runs-root",
            str(tmp_path),
        ]
    )
    capsys.readouterr()
    config_root = tmp_path / "custom-mhe"
    approvals_root = config_root / "approvals"
    benchmarks_root = config_root / "benchmarks"
    approvals_root.mkdir(parents=True)
    benchmarks_root.mkdir()
    (config_root / "config.json").write_text(
        json.dumps(
            {
                "approval": {
                    "profiles": {
                        "lean_workflow_approval": {
                            "manifest": str(approvals_root / "lean_approval.json"),
                            "required_fields": ["approved_by", "approval_decision"],
                        }
                    }
                }
            }
        )
    )
    (benchmarks_root / "comparison-approval.json").write_text(
        json.dumps({"required_approval_profiles": ["lean_workflow_approval"]})
    )
    (approvals_root / "lean_approval.json").write_text(
        json.dumps(
            {
                "status": "approved_with_limitations",
                "approved_by": "lean-reviewer@example.test",
                "approval_decision": "approved_with_limitations",
            }
        )
    )

    compare_status = main(
        [
            "benchmark-compare",
            "--suite",
            "lean-proof",
            "--runs-root",
            str(tmp_path),
            "--config-root",
            str(config_root),
        ]
    )

    assert run_status == 0
    assert compare_status == 0
    capsys.readouterr()
    gate = json.loads(
        (tmp_path / "lean-proof-benchmark" / "comparison" / "approval_gate.json").read_text()
    )
    assert gate["status"] == "approved_with_limitations"
    assert gate["approval_ready"] is True
