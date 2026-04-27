from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from metaharness_ext.octave.contracts import OctaveOutputSpec

SUPPORTED_ARTIFACT_SUFFIXES = {".mat", ".txt", ".json", ".csv", ".png", ".pdf", ".svg"}


class OctaveMATFileSummary(BaseModel):
    path: str
    available: bool
    variables: dict[str, dict[str, Any]] = Field(default_factory=dict)
    message: str | None = None


class OctaveArtifactDiscovery(BaseModel):
    found: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    unexpected: list[str] = Field(default_factory=list)


class OctaveMATFileParser:
    def parse(self, path: str | Path) -> OctaveMATFileSummary:
        mat_path = Path(path)
        try:
            from scipy.io import loadmat
        except ImportError:
            return OctaveMATFileSummary(
                path=str(mat_path), available=False, message="scipy.io.loadmat is unavailable"
            )
        data = loadmat(mat_path)
        variables: dict[str, dict[str, Any]] = {}
        for name, value in data.items():
            if name.startswith("__"):
                continue
            variables[name] = {
                "shape": list(getattr(value, "shape", ())),
                "dtype": str(getattr(value, "dtype", type(value).__name__)),
            }
        return OctaveMATFileSummary(path=str(mat_path), available=True, variables=variables)


class OctaveArtifactDetector:
    def detect(
        self, working_dir: str | Path, output_spec: list[OctaveOutputSpec]
    ) -> OctaveArtifactDiscovery:
        root = Path(working_dir)
        discovered = sorted(
            path
            for path in root.rglob("*")
            if path.is_file() and path.suffix.lower() in SUPPORTED_ARTIFACT_SUFFIXES
        )
        by_name = {path.name: str(path) for path in discovered}
        expected = {_expected_file_name(output) for output in output_spec}
        expected = {name for name in expected if name}
        found = [by_name[name] for name in sorted(expected) if name in by_name]
        missing = sorted(name for name in expected if name not in by_name)
        unexpected = sorted(str(path) for path in discovered if path.name not in expected)
        return OctaveArtifactDiscovery(found=found, missing=missing, unexpected=unexpected)


def _expected_file_name(output: OctaveOutputSpec) -> str:
    if output.file_name:
        return Path(output.file_name).name
    if output.kind == "variable":
        return f"{output.variable_name or output.name}.txt"
    return ""
