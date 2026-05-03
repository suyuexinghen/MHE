from __future__ import annotations

import json
from pathlib import Path

from metaharness_ext.boutpp import (
    BOUTPP_EVIDENCE_POLICY_SLOT,
    BOUTPP_VALIDATOR_SLOT,
    PROTECTED_SLOTS,
)


def test_manifests_exist_and_reference_slots():
    manifest_dir = Path("examples/manifests/boutpp")
    expected = {
        "boutpp_gateway.json",
        "boutpp_environment.json",
        "boutpp_compiler.json",
        "boutpp_executor.json",
        "boutpp_postprocess.json",
        "boutpp_validator.json",
        "boutpp_policy.json",
        "boutpp_study.json",
    }
    assert expected.issubset({path.name for path in manifest_dir.glob("*.json")})
    validator_manifest = json.loads((manifest_dir / "boutpp_validator.json").read_text())
    policy_manifest = json.loads((manifest_dir / "boutpp_policy.json").read_text())
    assert validator_manifest["contracts"]["slots"][0]["slot"] == BOUTPP_VALIDATOR_SLOT
    assert policy_manifest["contracts"]["slots"][0]["slot"] == BOUTPP_EVIDENCE_POLICY_SLOT
    assert BOUTPP_VALIDATOR_SLOT in PROTECTED_SLOTS
    assert BOUTPP_EVIDENCE_POLICY_SLOT in PROTECTED_SLOTS
