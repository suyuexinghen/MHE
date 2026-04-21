"""Shared pytest fixtures and path helpers for MHE tests."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
EXAMPLES_DIR = ROOT / "examples"
MANIFEST_DIR = EXAMPLES_DIR / "manifests" / "baseline"
GRAPHS_DIR = EXAMPLES_DIR / "graphs"


@pytest.fixture(scope="session")
def examples_dir() -> Path:
    return EXAMPLES_DIR


@pytest.fixture(scope="session")
def manifest_dir() -> Path:
    return MANIFEST_DIR


@pytest.fixture(scope="session")
def graphs_dir() -> Path:
    return GRAPHS_DIR


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    required_bins = ("ADRSolver", "FieldConvert")
    if all(shutil.which(name) for name in required_bins):
        return
    skip_nektar = pytest.mark.skip(reason="Nektar++ not available")
    for item in items:
        if "nektar" in item.keywords:
            item.add_marker(skip_nektar)
