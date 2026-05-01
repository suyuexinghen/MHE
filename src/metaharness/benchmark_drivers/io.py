from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from metaharness.benchmark_drivers.models import BenchmarkLane, BenchmarkSuite

SUITE_DIRS: dict[BenchmarkSuite, str] = {
    "octave-native": "octave-native-benchmark",
    "nektar-pde": "nektar-pde-benchmark",
    "qcompute-abacus": "qcompute-abacus-benchmark",
    "fealpy-pde": "fealpy-pde-benchmark",
    "pycfd-pde": "pycfd-pde-benchmark",
}


def suite_root(runs_root: Path, suite: BenchmarkSuite) -> Path:
    return runs_root / SUITE_DIRS[suite]


def case_dir(runs_root: Path, suite: BenchmarkSuite, lane: BenchmarkLane, case_id: str) -> Path:
    return suite_root(runs_root, suite) / lane / case_id


def specs_dir(runs_root: Path, suite: BenchmarkSuite) -> Path:
    return suite_root(runs_root, suite) / "specs"


def comparison_dir(runs_root: Path, suite: BenchmarkSuite) -> Path:
    return suite_root(runs_root, suite) / "comparison"


def reports_dir(runs_root: Path, suite: BenchmarkSuite) -> Path:
    return suite_root(runs_root, suite) / "reports"


def to_jsonable(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    return value


def write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(to_jsonable(payload), indent=2, sort_keys=True) + "\n")
    return path


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def write_text(path: Path, payload: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload)
    return path


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return path
