from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


def runtime_path(name: str) -> Path:
    path = REPO_ROOT / ".demo-runs" / "qcompute" / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def hardware_enabled() -> bool:
    return os.getenv("QCOMPUTE_ENABLE_HARDWARE") == "1"
