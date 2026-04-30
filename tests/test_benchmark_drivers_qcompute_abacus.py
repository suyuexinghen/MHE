from __future__ import annotations

import json
from pathlib import Path

from metaharness.benchmark_drivers.compare import write_comparison_outputs
from metaharness.benchmark_drivers.qcompute_abacus_cases import get_qcompute_abacus_cases
from metaharness.benchmark_drivers.qcompute_abacus_runner import QComputeAbacusBenchmarkRunner
from metaharness_ext.qcompute.abacus_bridge import (
    build_abacus_hs_bridge_status,
    build_abacus_hs_conversion_plan,
    convert_toy_abacus_hs_fixture_to_fcidump,
    parse_abacus_hs_matrix_ref,
    parse_abacus_input_ref,
)


def test_qcompute_abacus_catalog_includes_proxy_and_bridge_cases() -> None:
    cases = {case.case_id: case for case in get_qcompute_abacus_cases()}

    assert set(cases) == {
        "h2-fcidump-vqe-proxy",
        "h2-fcidump-jw-vs-bk",
        "abacus-hs-bridge-pending",
    }
    assert cases["h2-fcidump-vqe-proxy"].suite == "qcompute-abacus"
    assert cases["abacus-hs-bridge-pending"].capability_gated is True
    assert "abacus_hs_to_fcidump_bridge" in cases["abacus-hs-bridge-pending"].required_capabilities


def test_qcompute_abacus_dry_run_writes_three_lane_outputs(tmp_path: Path) -> None:
    case = get_qcompute_abacus_cases(["h2-fcidump-vqe-proxy"])[0]
    runner = QComputeAbacusBenchmarkRunner(runs_root=tmp_path)

    summaries = runner.run_case(case, ["extension", "direct", "agent"])

    assert [summary.lane for summary in summaries] == ["extension", "direct", "agent"]
    assert all(summary.status == "passed" for summary in summaries)
    suite_root = tmp_path / "qcompute-abacus-benchmark"
    assert (suite_root / "extension" / case.case_id / "summary.json").exists()
    assert (suite_root / "extension" / case.case_id / "hamiltonian.fcidump").exists()
    assert (suite_root / "direct" / case.case_id / "claude_prompt.txt").exists()
    assert (suite_root / "agent" / case.case_id / "proposal.json").exists()


def test_qcompute_abacus_mapping_case_writes_dry_run_summaries(tmp_path: Path) -> None:
    case = get_qcompute_abacus_cases(["h2-fcidump-jw-vs-bk"])[0]
    runner = QComputeAbacusBenchmarkRunner(runs_root=tmp_path)

    summaries = runner.run_case(case, ["extension", "direct", "agent"])

    assert all(summary.status == "passed" for summary in summaries)
    extension_summary = json.loads(
        (
            tmp_path / "qcompute-abacus-benchmark" / "extension" / case.case_id / "summary.json"
        ).read_text()
    )
    assert extension_summary["metrics"]["jw_num_qubits"] == 2.0
    assert extension_summary["metrics"]["bk_num_qubits"] == 2.0


def test_abacus_input_parser_records_hs_metadata(tmp_path: Path) -> None:
    input_path = tmp_path / "INPUT"
    input_path.write_text(
        "INPUT_PARAMETERS\n"
        "calculation scf\n"
        "basis_type lcao\n"
        "gamma_only 0\n"
        "out_mat_hs 1 3\n"
        "ks_solver scalapack_gvx\n"
    )

    metadata = parse_abacus_input_ref(str(input_path))

    assert metadata["exists"] is True
    assert metadata["parameters"]["basis_type"] == ["lcao"]
    assert metadata["parameters"]["out_mat_hs"] == ["1", "3"]
    assert metadata["hs_output_keys"] == ["out_mat_hs"]
    assert metadata["bridge_parse_status"] == "metadata_parsed"


def test_real_looking_abacus_hs_matrix_ref_records_artifact_metadata(tmp_path: Path) -> None:
    hs_path = tmp_path / "hrs1_nao.csr.ref"
    hs_path.write_text("real-looking sparse H/S artifact placeholder\n")

    metadata = parse_abacus_hs_matrix_ref(str(hs_path))

    assert metadata["exists"] is True
    assert metadata["kind"] == "abacus_hs_matrix"
    assert metadata["format_family"] == "abacus_sparse_csr"
    assert metadata["matrix_role"] == "H"
    assert metadata["parse_status"] == "metadata_only"
    assert metadata["conversion_status"] == "unsupported"
    assert metadata["bytes"] > 0


def test_real_looking_abacus_hs_fixture_records_metadata_without_conversion(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "INPUT"
    input_path.write_text(
        "INPUT_PARAMETERS\n"
        "suffix silicon\n"
        "calculation scf\n"
        "basis_type lcao\n"
        "gamma_only 0\n"
        "nbands 8\n"
        "out_mat_hs2 1\n"
        "ks_solver genelpa\n"
    )
    hs_path = tmp_path / "OUT.silicon" / "data-HR-sparse_SPIN0.csr"
    hs_path.parent.mkdir()
    hs_path.write_text("real-looking sparse H/S artifact placeholder\n")

    metadata = parse_abacus_input_ref(str(input_path))
    bridge_status = build_abacus_hs_bridge_status(
        case_id="abacus-hs-bridge-pending",
        source_reference={"abacus_hs_source_refs": [str(input_path), str(hs_path)]},
    )

    assert metadata["parameters"]["suffix"] == ["silicon"]
    assert metadata["parameters"]["nbands"] == ["8"]
    assert metadata["hs_output_keys"] == ["out_mat_hs2"]
    assert bridge_status.status == "converter_missing"
    assert bridge_status.conversion_plan.status == "metadata_only"
    assert bridge_status.promotion_ready is False
    assert bridge_status.missing_capabilities == ["abacus_hs_to_fcidump_converter"]
    assert bridge_status.failure_code == "converter_missing"
    assert bridge_status.matrix_metadata[0]["format_family"] == "abacus_sparse_csr"
    assert bridge_status.matrix_metadata[0]["conversion_status"] == "unsupported"


def test_abacus_hs_conversion_plan_remains_metadata_only() -> None:
    plan = build_abacus_hs_conversion_plan(metadata_available=True)

    assert plan.status == "metadata_only"
    assert plan.target_format == "qcompute_pauli_dict"
    assert "out_mat_hs" in plan.accepted_artifacts
    assert "converted operator validated by QCompute parser" in plan.validation_requirements


def test_toy_abacus_hs_fixture_converts_to_fcidump_contract() -> None:
    result = convert_toy_abacus_hs_fixture_to_fcidump(
        "ABACUS_HS_TOY\nnorb 2\nnelec 2\nh_matrix\n1.0 0.2\n0.2 0.5\n"
    )

    assert result.status == "converted"
    assert result.fcidump_text is not None
    assert "NORB=2" in result.fcidump_text
    assert " 1.000000000000  1  1  0  0" in result.fcidump_text
    assert result.metadata["scientifically_validated"] is False


def test_real_abacus_hs_conversion_remains_unsupported() -> None:
    result = convert_toy_abacus_hs_fixture_to_fcidump("not a supported ABACUS matrix")

    assert result.status == "unsupported"
    assert result.unsupported_reason == "Only ABACUS_HS_TOY fixture conversion is implemented."


def test_qcompute_abacus_bridge_case_is_explicitly_skipped(tmp_path: Path) -> None:
    case = get_qcompute_abacus_cases(["abacus-hs-bridge-pending"])[0]
    runner = QComputeAbacusBenchmarkRunner(runs_root=tmp_path)

    summaries = runner.run_case(case, ["extension", "direct", "agent"])

    assert all(summary.status == "skipped" for summary in summaries)
    assert all("unsupported_source_format" in (summary.skip_reason or "") for summary in summaries)
    output_dir = tmp_path / "qcompute-abacus-benchmark" / "extension" / case.case_id
    assert (output_dir / "source_refs.json").exists()
    bridge_status = json.loads((output_dir / "bridge_status.json").read_text())
    assert bridge_status["status"] == "converter_missing"
    assert bridge_status["promotion_ready"] is False
    assert bridge_status["missing_capabilities"] == ["abacus_hs_to_fcidump_converter"]
    assert bridge_status["failure_code"] == "converter_missing"
    assert "matrix_metadata" in bridge_status
    assert bridge_status["conversion_plan"]["status"] == "metadata_only"
    assert bridge_status["conversion_plan"]["target_format"] == "qcompute_pauli_dict"
    assert any(
        "out_mat_hs" in ref["hs_output_keys"] or "out_mat_hs2" in ref["hs_output_keys"]
        for ref in bridge_status["parsed_metadata"]["input_refs"]
    )
    source_refs = json.loads((output_dir / "source_refs.json").read_text())
    assert source_refs["bridge_status"]["parsed_metadata"]["input_refs"]


def test_qcompute_abacus_real_mode_skips_when_qiskit_missing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "metaharness.benchmark_drivers.qcompute_abacus_runner.find_spec",
        lambda _: None,
    )
    case = get_qcompute_abacus_cases(["h2-fcidump-vqe-proxy"])[0]
    runner = QComputeAbacusBenchmarkRunner(runs_root=tmp_path, allow_real_tools=True)

    summary = runner.run_extension(case)

    assert summary.status == "skipped"
    assert summary.skip_reason == "qiskit and qiskit_aer are required for real qcompute-abacus runs"


def test_qcompute_abacus_compare_reuses_generic_comparator(tmp_path: Path) -> None:
    case = get_qcompute_abacus_cases(["h2-fcidump-vqe-proxy"])[0]
    QComputeAbacusBenchmarkRunner(runs_root=tmp_path).run_case(
        case, ["extension", "direct", "agent"]
    )

    rows = write_comparison_outputs(runs_root=tmp_path, suite="qcompute-abacus")

    assert len(rows) == 1
    assert rows[0].case_id == "h2-fcidump-vqe-proxy"
    assert rows[0].verdict == "all_passed"
    assert (tmp_path / "qcompute-abacus-benchmark" / "comparison" / "result_bundle.json").exists()
