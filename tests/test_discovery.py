"""Multi-source component discovery tests."""

from __future__ import annotations

import json
from pathlib import Path

from metaharness.sdk.discovery import ComponentDiscovery, DiscoverySource


def _write_manifest(path: Path, name: str, version: str, kind: str = "core") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "id": name,
                "name": name,
                "version": version,
                "kind": kind,
                "entry": "metaharness.components.runtime:RuntimeComponent",
                "harness_version": ">=0.0.1",
                "contracts": {
                    "inputs": [],
                    "outputs": [],
                    "events": [],
                    "provides": [],
                    "requires": [],
                    "slots": [],
                },
            }
        )
    )


def test_four_source_scan_and_priority_resolution(tmp_path: Path) -> None:
    bundled = tmp_path / "bundled"
    templates = tmp_path / "templates"
    market = tmp_path / "market"
    custom = tmp_path / "custom"

    _write_manifest(bundled / "runtime.json", "runtime", "1.0.0")
    _write_manifest(templates / "runtime.json", "runtime", "1.1.0")
    _write_manifest(market / "runtime.json", "runtime", "1.2.0")
    _write_manifest(custom / "runtime.json", "runtime", "1.3.0")
    _write_manifest(market / "gateway.json", "gateway", "2.0.0")

    disco = ComponentDiscovery(bundled=bundled, templates=templates, market=market, custom=custom)

    all_found = disco.scan_all()
    assert {f.source for f in all_found} == {
        DiscoverySource.BUNDLED,
        DiscoverySource.TEMPLATE,
        DiscoverySource.MARKET,
        DiscoverySource.CUSTOM,
    }

    resolution = disco.resolve()
    winners_by_id = {w.identity: w for w in resolution.winners}
    assert winners_by_id["runtime"].source == DiscoverySource.CUSTOM
    assert winners_by_id["runtime"].manifest.version == "1.3.0"
    assert winners_by_id["gateway"].source == DiscoverySource.MARKET
    assert len(resolution.overridden) == 3  # three lower-priority runtime copies


def test_missing_roots_are_silently_empty(tmp_path: Path) -> None:
    disco = ComponentDiscovery(bundled=tmp_path / "does-not-exist")
    assert disco.scan_all() == []
    assert disco.resolve().winners == []


def test_scan_individual_sources(tmp_path: Path) -> None:
    _write_manifest(tmp_path / "a" / "m.json", "a", "0.1.0")
    _write_manifest(tmp_path / "b" / "m.json", "b", "0.1.0")
    disco = ComponentDiscovery(bundled=tmp_path / "a", custom=tmp_path / "b")
    assert {m.identity for m in disco.scan_bundled()} == {"a"}
    assert {m.identity for m in disco.scan_custom()} == {"b"}
    assert disco.scan_templates() == []
    assert disco.scan_market() == []
