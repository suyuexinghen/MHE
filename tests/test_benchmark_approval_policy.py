from __future__ import annotations

import json
from pathlib import Path

from metaharness.benchmark_drivers.compare import evaluate_approval_gate
from metaharness.cli import main


def _write_policy_root(config_root: Path) -> None:
    approvals_root = config_root / "approvals"
    benchmarks_root = config_root / "benchmarks"
    approvals_root.mkdir(parents=True)
    benchmarks_root.mkdir()
    (config_root / "config.json").write_text(
        json.dumps(
            {
                "approval": {
                    "profiles": {
                        "benchmark_promotion_admin_approval": {
                            "manifest": ".mhe/approvals/comparison_benchmark_approval.json",
                            "required_fields": [
                                "approved_by",
                                "approval_role",
                                "approved_scope",
                                "evidence_refs",
                                "approval_decision",
                            ],
                        },
                        "qcompute_abacus_benchmark_admin_approval": {
                            "manifest": ".mhe/approvals/qcompute_abacus_benchmark_approval.json",
                            "required_fields": [
                                "approved_by",
                                "approval_role",
                                "approved_scope",
                                "evidence_refs",
                                "approval_decision",
                            ],
                        },
                        "abacus_hs_scientific": {
                            "manifest": ".mhe/approvals/abacus_hs_approval.json",
                            "required_fields": [
                                "approved_by",
                                "approval_role",
                                "fixture_refs",
                                "tolerance_table_ref",
                                "reference_observable",
                            ],
                        },
                    }
                }
            }
        )
    )
    (benchmarks_root / "comparison-approval.json").write_text(
        json.dumps(
            {
                "policy_id": "comparison_benchmarks_require_admin_approval",
                "required_approval_profiles": ["benchmark_promotion_admin_approval"],
                "conditional_approval_profiles": [
                    {
                        "when": {"suite": "qcompute-abacus"},
                        "requires": ["qcompute_abacus_benchmark_admin_approval"],
                    },
                    {
                        "when": {
                            "suite": "qcompute-abacus",
                            "case_id": "abacus-hs-bridge-pending",
                        },
                        "requires": ["abacus_hs_scientific"],
                    },
                ],
            }
        )
    )
    _write_admin_manifest(approvals_root / "comparison_benchmark_approval.json")
    _write_admin_manifest(
        approvals_root / "qcompute_abacus_benchmark_approval.json",
        excluded_claims=["production_abacus_hs_conversion_available"],
    )
    (approvals_root / "abacus_hs_approval.json").write_text(
        json.dumps(
            {
                "status": "invalid",
                "approved_by": None,
                "approval_role": None,
                "fixture_refs": [],
                "tolerance_table_ref": None,
                "reference_observable": None,
            }
        )
    )


def _write_admin_manifest(path: Path, excluded_claims: list[str] | None = None) -> None:
    path.write_text(
        json.dumps(
            {
                "status": "approved_with_limitations",
                "approved_by": "admin@example.test",
                "approval_role": "project_lead_authorized_admin",
                "approved_scope": {
                    "suite": "qcompute-abacus",
                    "excluded_claims": excluded_claims or ["numerical_solver_superiority"],
                },
                "evidence_refs": ["comparison/result_bundle.json"],
                "approval_decision": "approved_with_limitations",
            }
        )
    )


def test_evaluate_approval_gate_accepts_limited_admin_approval(tmp_path: Path) -> None:
    config_root = tmp_path / ".mhe"
    _write_policy_root(config_root)

    gate = evaluate_approval_gate(config_root=config_root, suite="qcompute-abacus")

    assert gate["status"] == "approved_with_limitations"
    assert gate["approval_ready"] is True
    assert gate["approved_profiles"] == [
        "benchmark_promotion_admin_approval",
        "qcompute_abacus_benchmark_admin_approval",
    ]
    assert gate["blocked_profiles"] == []
    assert "production_abacus_hs_conversion_available" in gate["excluded_claims"]


def test_evaluate_approval_gate_keeps_abacus_scientific_profile_blocked(
    tmp_path: Path,
) -> None:
    config_root = tmp_path / ".mhe"
    _write_policy_root(config_root)

    gate = evaluate_approval_gate(
        config_root=config_root,
        suite="qcompute-abacus",
        case_ids=["abacus-hs-bridge-pending"],
    )

    assert gate["status"] == "blocked"
    assert gate["approval_ready"] is False
    assert "abacus_hs_scientific" in gate["blocked_profiles"]
    assert (
        "abacus_hs_scientific_not_approved"
        in gate["missing_evidence_by_category"]["scientific_validation"]
    )


def test_benchmark_approval_check_cli_reports_blocked_scientific_gate(
    tmp_path: Path,
    capsys,
) -> None:
    config_root = tmp_path / ".mhe"
    _write_policy_root(config_root)

    status = main(
        [
            "benchmark-approval-check",
            "--suite",
            "qcompute-abacus",
            "--cases",
            "abacus-hs-bridge-pending",
            "--config-root",
            str(config_root),
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert status == 0
    assert payload["status"] == "blocked"
    assert "abacus_hs_scientific" in payload["blocked_profiles"]


def test_benchmark_approval_check_strict_fails_for_blocked_scientific_gate(
    tmp_path: Path,
    capsys,
) -> None:
    config_root = tmp_path / ".mhe"
    _write_policy_root(config_root)

    status = main(
        [
            "benchmark-approval-check",
            "--suite",
            "qcompute-abacus",
            "--cases",
            "abacus-hs-bridge-pending",
            "--config-root",
            str(config_root),
            "--strict",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert status == 1
    assert payload["approval_ready"] is False


def test_benchmark_approval_check_fails_missing_profile(tmp_path: Path, capsys) -> None:
    config_root = tmp_path / ".mhe"
    _write_policy_root(config_root)
    config = json.loads((config_root / "config.json").read_text())
    del config["approval"]["profiles"]["qcompute_abacus_benchmark_admin_approval"]
    (config_root / "config.json").write_text(json.dumps(config))

    status = main(
        [
            "benchmark-approval-check",
            "--suite",
            "qcompute-abacus",
            "--config-root",
            str(config_root),
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert status == 1
    assert payload["status"] == "blocked"
    assert "qcompute_abacus_benchmark_admin_approval" in payload["blocked_profiles"]


def test_checked_in_approval_policy_references_existing_profiles_and_manifests() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    config_root = repo_root / ".mhe"
    config = json.loads((config_root / "config.json").read_text())
    policy = json.loads((config_root / "benchmarks" / "comparison-approval.json").read_text())
    profiles = config["approval"]["profiles"]
    referenced_profiles = [
        *policy["required_approval_profiles"],
        *[
            profile
            for conditional in policy["conditional_approval_profiles"]
            for profile in conditional["requires"]
        ],
    ]

    for profile_name in referenced_profiles:
        profile = profiles[profile_name]
        manifest_path = repo_root / profile["manifest"]
        assert manifest_path.exists(), profile_name
        manifest = json.loads(manifest_path.read_text())
        if profile_name == "abacus_hs_scientific":
            assert manifest["status"] == "invalid"
            continue
        missing_fields = [
            field for field in profile["required_fields"] if manifest.get(field) in (None, "", [])
        ]
        assert missing_fields == []
        assert manifest["approval_decision"] == "approved_with_limitations"
        for evidence_ref in manifest["evidence_refs"]:
            if evidence_ref.startswith(".runs/"):
                continue
            assert (repo_root / evidence_ref).exists(), evidence_ref


def test_checked_in_evidence_bundles_are_claim_limited() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    evidence_root = repo_root / ".mhe" / "evidence"
    bundle_paths = sorted(evidence_root.glob("*_evidence_bundle.json"))

    assert {path.name for path in bundle_paths} >= {
        "comparison_benchmark_evidence_bundle.json",
        "octave_native_evidence_bundle.json",
        "nektar_pde_evidence_bundle.json",
        "fealpy_pde_evidence_bundle.json",
        "pycfd_pde_evidence_bundle.json",
        "qcompute_abacus_evidence_bundle.json",
    }
    for bundle_path in bundle_paths:
        bundle = json.loads(bundle_path.read_text())
        assert bundle["excluded_claims"]
        if bundle_path.name != "comparison_benchmark_evidence_bundle.json":
            assert bundle["required_before_stronger_claims"]
        for artifact in bundle.get("observed_artifacts", []):
            assert artifact["claim_boundary"]
            assert artifact["checked_in"] is False


def test_checked_in_qcompute_abacus_sentinel_gate_remains_scientifically_blocked() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    gate = evaluate_approval_gate(
        config_root=repo_root / ".mhe",
        suite="qcompute-abacus",
        case_ids=["abacus-hs-bridge-pending"],
    )

    assert gate["status"] == "blocked"
    assert gate["approval_ready"] is False
    assert "qcompute_abacus_benchmark_admin_approval" in gate["approved_profiles"]
    assert gate["blocked_profiles"] == ["abacus_hs_scientific"]
