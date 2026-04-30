from __future__ import annotations

import json
from pathlib import Path

from metaharness.benchmark_drivers.compare import write_comparison_outputs
from metaharness.benchmark_drivers.qcompute_abacus_cases import get_qcompute_abacus_cases
from metaharness.benchmark_drivers.qcompute_abacus_runner import QComputeAbacusBenchmarkRunner
from metaharness_ext.qcompute.abacus_bridge import (
    build_abacus_hs_approval_manifest,
    build_abacus_hs_bridge_status,
    build_abacus_hs_bridge_validation,
    build_abacus_hs_conversion_plan,
    build_abacus_hs_promotion_gate,
    build_abacus_hs_review_signoff,
    convert_abacus_hs_header_to_pauli_proxy,
    convert_toy_abacus_hs_fixture_to_fcidump,
    discover_abacus_hs_matrix_refs,
    parse_abacus_hs_matrix_ref,
    parse_abacus_input_ref,
    validate_abacus_hs_small_dense_eigenproblem,
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


def test_abacus_hs_matrix_metadata_records_parser_contract_blockers(tmp_path: Path) -> None:
    hs_path = tmp_path / "data-HR-sparse_SPIN0.csr"
    hs_path.write_text("2 2 3\n1 1 -1.0\n1 2 0.2\n2 2 -0.5\n")

    metadata = parse_abacus_hs_matrix_ref(str(hs_path))

    assert metadata["shape"] == [2, 2]
    assert metadata["nnz"] == 3
    assert metadata["parse_status"] == "header_parsed"
    assert metadata["parser_contract_status"] == "header_parsed"
    assert metadata["conversion_status"] == "unsupported"
    assert metadata["validation_blockers"] == ["scientific_reference_missing"]


def test_abacus_hs_real_csr_header_parser_records_dimension_and_number(tmp_path: Path) -> None:
    hs_path = tmp_path / "hrs1_nao.csr.ref"
    hs_path.write_text(
        "STEP: 0\n"
        "Matrix Dimension of H(R): 26\n"
        "Matrix number of H(R): 177\n"
        "-3 -1 1 41\n"
        " 1.22221523e-10 -7.65800183e-10 -3.87251892e-10\n"
    )

    metadata = parse_abacus_hs_matrix_ref(str(hs_path))

    assert metadata["shape"] == [26, 26]
    assert metadata["nnz"] == 177
    assert metadata["parse_status"] == "header_parsed"
    assert metadata["matrix_role"] == "H"


def test_abacus_hs_text_header_parser_records_rows_and_columns(tmp_path: Path) -> None:
    hs_path = tmp_path / "hk_nao.txt.ref"
    hs_path.write_text("# rows 26\n# columns 26\nRow 1\n -6.56277e-01 -5.05476e-03\n")

    metadata = parse_abacus_hs_matrix_ref(str(hs_path))

    assert metadata["shape"] == [26, 26]
    assert metadata["nnz"] is None
    assert metadata["format_family"] == "abacus_text_matrix"
    assert "matrix_nnz_unparsed" in metadata["validation_blockers"]


def test_abacus_hs_header_proxy_converts_h_matrix_to_qubit_hamiltonian(tmp_path: Path) -> None:
    hs_path = tmp_path / "data-HR-sparse_SPIN0.csr"
    hs_path.write_text(
        "Matrix Dimension of H(R): 4\nMatrix number of H(R): 4\n0 0 0 4\n -1.0 0.25 0.5 -0.125\n"
    )

    result = convert_abacus_hs_header_to_pauli_proxy(str(hs_path))

    assert result.status == "converted"
    assert result.target_format == "qcompute_pauli_dict"
    assert result.qubit_hamiltonian is not None
    assert result.qubit_hamiltonian.source_format == "abacus_hs_header_proxy"
    assert result.qubit_hamiltonian.mapping_method == "diagonal_z_proxy"
    assert result.metadata["scientifically_validated"] is False


def test_abacus_hs_header_proxy_rejects_overlap_matrix(tmp_path: Path) -> None:
    hs_path = tmp_path / "data-SR-sparse_SPIN0.csr"
    hs_path.write_text("Matrix Dimension of S(R): 4\nMatrix number of S(R): 4\n")

    result = convert_abacus_hs_header_to_pauli_proxy(str(hs_path))

    assert result.status == "unsupported"
    assert (
        result.unsupported_reason
        == "Only H matrix artifacts can be converted into a Hamiltonian proxy."
    )


def test_abacus_hs_small_dense_reference_validation_passes_toy_eigenproblem(
    tmp_path: Path,
) -> None:
    fixture_path = tmp_path / "validated.hsref"
    fixture_path.write_text(
        "ABACUS_HS_DENSE_REFERENCE\n"
        "tolerance 1e-12\n"
        "reference_eigenvalues 1.0 2.0\n"
        "h_matrix\n"
        "1.0 0.0\n"
        "0.0 2.0\n"
        "s_matrix\n"
        "1.0 0.0\n"
        "0.0 1.0\n"
    )

    result = validate_abacus_hs_small_dense_eigenproblem(str(fixture_path))

    assert result.status == "reference_passed"
    assert result.reference_validated is True
    assert result.scientifically_validated is False
    assert result.promotion_ready is False
    assert result.eigenvalues == [1.0, 2.0]
    assert result.max_eigenvalue_error == 0.0
    assert "production_converter_missing" in result.blockers


def test_abacus_hs_small_dense_reference_validation_fails_tolerance(
    tmp_path: Path,
) -> None:
    fixture_path = tmp_path / "invalid.hsref"
    fixture_path.write_text(
        "ABACUS_HS_DENSE_REFERENCE\n"
        "tolerance 1e-12\n"
        "reference_eigenvalues 1.0 3.0\n"
        "h_matrix\n"
        "1.0 0.0\n"
        "0.0 2.0\n"
        "s_matrix\n"
        "1.0 0.0\n"
        "0.0 1.0\n"
    )

    result = validate_abacus_hs_small_dense_eigenproblem(str(fixture_path))

    assert result.status == "reference_failed"
    assert result.reference_validated is False
    assert result.scientifically_validated is False
    assert result.max_eigenvalue_error == 1.0
    assert result.blockers[0] == "reference_eigenvalue_tolerance_failed"


def test_abacus_hs_small_dense_reference_validation_blocks_malformed_fixture(
    tmp_path: Path,
) -> None:
    fixture_path = tmp_path / "malformed.hsref"
    fixture_path.write_text(
        "ABACUS_HS_DENSE_REFERENCE\n"
        "tolerance 1e-12\n"
        "reference_eigenvalues 1.0 2.0\n"
        "h_matrix\n"
        "1.0 0.5\n"
        "0.0 2.0\n"
        "s_matrix\n"
        "1.0 0.0\n"
        "0.0 1.0\n"
    )

    result = validate_abacus_hs_small_dense_eigenproblem(str(fixture_path))

    assert result.status == "blocked"
    assert result.reference_validated is False
    assert result.scientifically_validated is False
    assert result.blockers == ["h_matrix_not_symmetric", "scientific_reviewer_signoff_missing"]


def test_abacus_hs_bridge_validation_blocks_without_reference_fixture() -> None:
    result = build_abacus_hs_bridge_validation({"abacus_hs_source_refs": []})

    assert result.status == "blocked"
    assert result.scientifically_validated is False
    assert result.promotion_ready is False
    assert result.blockers == [
        "administrator_approved_reference_fixture_missing",
        "tolerance_table_missing",
        "scientific_reviewer_signoff_missing",
        "production_converter_missing",
    ]


def test_abacus_hs_review_signoff_blocks_missing_scientific_evidence() -> None:
    bridge_status = build_abacus_hs_bridge_status(
        case_id="abacus-hs-bridge-pending",
        source_reference={"abacus_hs_source_refs": []},
    )
    bridge_validation = build_abacus_hs_bridge_validation({"abacus_hs_source_refs": []})

    signoff = build_abacus_hs_review_signoff(
        bridge_status=bridge_status,
        bridge_validation=bridge_validation,
        reviewer_backend="acp_claudecode",
    )

    assert signoff.reviewer_backend == "acp_claudecode"
    assert signoff.decision == "block"
    assert signoff.claim_boundary_ok is True
    assert signoff.reviewer_evidence_only is True
    assert signoff.replaces_human_scientific_signoff is False
    assert signoff.sentinel_must_remain_skipped is True
    assert "administrator_approved_reference_fixture_missing" in signoff.missing_evidence
    assert "abacus_hs_to_fcidump_converter" in signoff.missing_evidence


def test_abacus_hs_approval_manifest_records_missing_manifest() -> None:
    manifest = build_abacus_hs_approval_manifest({"abacus_hs_source_refs": []})

    assert manifest.status == "missing"
    assert manifest.notes == ["No abacus_hs_approval.json approval manifest was provided."]


def test_abacus_hs_approval_manifest_rejects_incomplete_manifest(tmp_path: Path) -> None:
    manifest_path = tmp_path / "abacus_hs_approval.json"
    manifest_path.write_text(json.dumps({"approved_by": "lab-admin"}))

    manifest = build_abacus_hs_approval_manifest({"abacus_hs_source_refs": [str(manifest_path)]})

    assert manifest.status == "invalid"
    assert "approval_role_missing" in manifest.notes
    assert "fixture_refs_missing" in manifest.notes
    assert "tolerance_table_ref_missing" in manifest.notes
    assert "reference_observable_missing" in manifest.notes


def test_abacus_hs_approval_manifest_accepts_complete_manifest(tmp_path: Path) -> None:
    manifest_path = tmp_path / "abacus_hs_approval.json"
    manifest_path.write_text(
        json.dumps(
            {
                "approved_by": "lab-admin",
                "approval_role": "scientific_reviewer",
                "fixture_refs": ["validated.hsref"],
                "tolerance_table_ref": "tolerances.json",
                "reference_observable": "ground_state_energy",
            }
        )
    )

    manifest = build_abacus_hs_approval_manifest({"abacus_hs_source_refs": [str(manifest_path)]})

    assert manifest.status == "approved"
    assert manifest.approved_by == "lab-admin"
    assert manifest.fixture_refs == ["validated.hsref"]


def test_abacus_hs_promotion_gate_blocks_without_human_approval() -> None:
    bridge_status = build_abacus_hs_bridge_status(
        case_id="abacus-hs-bridge-pending",
        source_reference={"abacus_hs_source_refs": []},
    )
    bridge_validation = build_abacus_hs_bridge_validation({"abacus_hs_source_refs": []})
    review_signoff = build_abacus_hs_review_signoff(
        bridge_status=bridge_status,
        bridge_validation=bridge_validation,
    )
    approval_manifest = build_abacus_hs_approval_manifest({"abacus_hs_source_refs": []})

    gate = build_abacus_hs_promotion_gate(
        bridge_status=bridge_status,
        bridge_validation=bridge_validation,
        review_signoff=review_signoff,
        approval_manifest=approval_manifest,
    )

    assert gate.status == "blocked"
    assert gate.promotion_ready is False
    assert gate.sentinel_must_remain_skipped is True
    assert "human_scientific_approval_manifest_missing" in gate.missing_evidence
    assert gate.missing_evidence_by_category["human_approval"] == [
        "human_scientific_approval_manifest_missing"
    ]
    assert (
        "administrator_approved_reference_fixture_missing"
        in gate.missing_evidence_by_category["scientific_validation"]
    )
    assert (
        "abacus_hs_to_fcidump_converter"
        in gate.missing_evidence_by_category["production_converter"]
    )
    assert gate.missing_evidence_by_category["real_repeat_evidence"] == [
        "real_mode_repeat_summary_missing"
    ]
    assert "production_converter_evidence" in gate.required_artifacts
    assert "real_mode_repeat_summary" in gate.required_artifacts


def test_abacus_hs_matrix_discovery_uses_input_suffix_out_dir(tmp_path: Path) -> None:
    input_path = tmp_path / "INPUT"
    input_path.write_text("INPUT_PARAMETERS\nsuffix silicon\nbasis_type lcao\nout_mat_hs2 1\n")
    hs_path = tmp_path / "OUT.silicon" / "data-SR-sparse_SPIN0.csr"
    hs_path.parent.mkdir()
    hs_path.write_text("real-looking sparse S artifact placeholder\n")

    input_metadata = parse_abacus_input_ref(str(input_path))
    discovered = discover_abacus_hs_matrix_refs([input_metadata])
    bridge_status = build_abacus_hs_bridge_status(
        case_id="abacus-hs-bridge-pending",
        source_reference={"abacus_hs_source_refs": [str(input_path)]},
    )

    assert discovered == [str(hs_path)]
    assert bridge_status.matrix_metadata[0]["path"] == str(hs_path)
    assert bridge_status.matrix_metadata[0]["matrix_role"] == "S"
    assert bridge_status.matrix_metadata[0]["conversion_status"] == "unsupported"
    assert bridge_status.promotion_ready is False


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
    assert bridge_status.conversion_plan.status == "ready"
    assert bridge_status.promotion_ready is False
    assert bridge_status.missing_capabilities == ["abacus_hs_to_fcidump_converter"]
    assert bridge_status.failure_code == "converter_missing"
    assert bridge_status.matrix_metadata[0]["format_family"] == "abacus_sparse_csr"
    assert bridge_status.matrix_metadata[0]["conversion_status"] == "unsupported"


def test_abacus_hs_conversion_plan_marks_proxy_target_ready() -> None:
    plan = build_abacus_hs_conversion_plan(metadata_available=True)

    assert plan.status == "ready"
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
    for lane in ["extension", "direct", "agent"]:
        output_dir = tmp_path / "qcompute-abacus-benchmark" / lane / case.case_id
        assert (output_dir / "source_refs.json").exists()
        bridge_validation = json.loads((output_dir / "bridge_validation.json").read_text())
        review_signoff = json.loads((output_dir / "review_signoff.json").read_text())
        approval_manifest = json.loads((output_dir / "approval_manifest.json").read_text())
        promotion_gate = json.loads((output_dir / "promotion_gate.json").read_text())
        assert bridge_validation["status"] == "blocked"
        assert "production_converter_missing" in bridge_validation["blockers"]
        assert bridge_validation["promotion_ready"] is False
        assert review_signoff["decision"] == "block"
        assert review_signoff["claim_boundary_ok"] is True
        assert review_signoff["reviewer_evidence_only"] is True
        assert review_signoff["replaces_human_scientific_signoff"] is False
        assert review_signoff["sentinel_must_remain_skipped"] is True
        assert approval_manifest["status"] == "missing"
        assert promotion_gate["status"] == "blocked"
        assert promotion_gate["promotion_ready"] is False
        assert "human_scientific_approval_manifest_missing" in promotion_gate["missing_evidence"]
        assert promotion_gate["missing_evidence_by_category"]["human_approval"] == [
            "human_scientific_approval_manifest_missing"
        ]
        assert (
            "tolerance_table_missing"
            in promotion_gate["missing_evidence_by_category"]["scientific_validation"]
        )
        assert (
            "abacus_hs_to_fcidump_converter"
            in promotion_gate["missing_evidence_by_category"]["production_converter"]
        )
        assert promotion_gate["missing_evidence_by_category"]["real_repeat_evidence"] == [
            "real_mode_repeat_summary_missing"
        ]
    output_dir = tmp_path / "qcompute-abacus-benchmark" / "extension" / case.case_id
    bridge_status = json.loads((output_dir / "bridge_status.json").read_text())
    assert bridge_status["status"] == "converter_missing"
    assert bridge_status["promotion_ready"] is False
    assert bridge_status["missing_capabilities"] == ["abacus_hs_to_fcidump_converter"]
    assert bridge_status["failure_code"] == "converter_missing"
    assert "matrix_metadata" in bridge_status
    assert bridge_status["readiness_gates"][0]["stage"] == "R1_parser"
    assert bridge_status["readiness_gates"][1]["status"] == "metadata_only"
    assert bridge_status["conversion_plan"]["status"] == "ready"
    assert bridge_status["conversion_plan"]["target_format"] == "qcompute_pauli_dict"
    assert any(
        "out_mat_hs" in ref["hs_output_keys"] or "out_mat_hs2" in ref["hs_output_keys"]
        for ref in bridge_status["parsed_metadata"]["input_refs"]
    )
    source_refs = json.loads((output_dir / "source_refs.json").read_text())
    assert source_refs["bridge_status"]["parsed_metadata"]["input_refs"]
    assert source_refs["approval_manifest"]["status"] == "missing"
    assert source_refs["promotion_gate"]["sentinel_must_remain_skipped"] is True
    assert source_refs["promotion_gate"]["missing_evidence_by_category"]["human_approval"] == [
        "human_scientific_approval_manifest_missing"
    ]


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
