"""Sandbox tier and risk-selector tests."""

from __future__ import annotations

import pytest

from metaharness.safety.sandbox_tiers import (
    InProcessAdapter,
    RiskTier,
    RiskTierSelector,
    SandboxTier,
    firecracker_adapter,
    gvisor_adapter,
    v8_wasm_adapter,
)


def test_default_adapters_have_expected_tiers() -> None:
    assert v8_wasm_adapter().tier == SandboxTier.V8_WASM
    assert gvisor_adapter().tier == SandboxTier.GVISOR
    assert firecracker_adapter().tier == SandboxTier.FIRECRACKER


def test_risk_selector_picks_minimum_required_tier() -> None:
    selector = RiskTierSelector(
        adapters=[v8_wasm_adapter(), gvisor_adapter(), firecracker_adapter()]
    )
    assert selector.select(RiskTier.LOW).tier == SandboxTier.V8_WASM
    assert selector.select(RiskTier.MEDIUM).tier == SandboxTier.GVISOR
    assert selector.select(RiskTier.HIGH).tier == SandboxTier.FIRECRACKER
    assert selector.select(RiskTier.CRITICAL).tier == SandboxTier.FIRECRACKER


def test_risk_selector_upgrades_when_only_stronger_available() -> None:
    selector = RiskTierSelector(adapters=[gvisor_adapter(), firecracker_adapter()])
    adapter = selector.select(RiskTier.LOW)
    # v8_wasm floor but only gvisor+firecracker available -> picks gvisor (cheapest
    # that satisfies the floor).
    assert adapter.tier == SandboxTier.GVISOR


def test_risk_selector_raises_when_no_adapter_qualifies() -> None:
    selector = RiskTierSelector(adapters=[v8_wasm_adapter()])
    with pytest.raises(LookupError):
        selector.select(RiskTier.HIGH)


def test_run_dispatches_through_selected_adapter() -> None:
    selector = RiskTierSelector(adapters=[v8_wasm_adapter()])
    result = selector.run(RiskTier.LOW, lambda x: x * 2, 3)
    assert result.success is True
    assert result.output == 6
    assert result.tier == SandboxTier.V8_WASM


def test_inprocess_adapter_captures_errors() -> None:
    def bad() -> None:
        raise ValueError("nope")

    result = InProcessAdapter(tier=SandboxTier.GVISOR).execute(bad)
    assert result.success is False
    assert "nope" in (result.error or "")
