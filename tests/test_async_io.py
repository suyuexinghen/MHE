"""Tests for async file I/O helpers."""

from __future__ import annotations

import asyncio
from pathlib import Path

from metaharness.config.xml_parser import parse_graph_xml_async
from metaharness.sdk.discovery import discover_manifest_paths_async
from metaharness.sdk.loader import load_manifest_async


def test_load_manifest_async(manifest_dir: Path) -> None:
    manifest = asyncio.run(load_manifest_async(manifest_dir / "runtime.json"))
    assert manifest.name == "runtime"


def test_parse_graph_xml_async(graphs_dir: Path) -> None:
    snapshot = asyncio.run(parse_graph_xml_async(graphs_dir / "minimal-happy-path.xml"))
    assert snapshot.graph_version == 1
    assert len(snapshot.nodes) == 4


def test_discover_manifest_paths_async(manifest_dir: Path) -> None:
    paths = asyncio.run(discover_manifest_paths_async(manifest_dir))
    names = {p.stem for p in paths}
    for expected in {
        "gateway",
        "runtime",
        "executor",
        "evaluation",
        "planner",
        "policy",
        "observability",
        "memory",
    }:
        assert expected in names
