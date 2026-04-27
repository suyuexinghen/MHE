from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class OctaveWorkspaceSyncPlan(BaseModel):
    source: str
    destination: str
    files: list[str] = Field(default_factory=list)


def build_workspace_sync_plan(
    source: str | Path, destination: str | Path
) -> OctaveWorkspaceSyncPlan:
    source_path = Path(source)
    files = sorted(
        str(path.relative_to(source_path)) for path in source_path.rglob("*") if path.is_file()
    )
    return OctaveWorkspaceSyncPlan(
        source=str(source_path), destination=str(destination), files=files
    )
