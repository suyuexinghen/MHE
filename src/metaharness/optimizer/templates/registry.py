"""Template registry.

A :class:`ComponentTemplate` describes a parameterised component
configuration the optimizer can instantiate. Templates live in a
:class:`TemplateRegistry` so callers can list / find / register /
unregister them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from metaharness.sdk.manifest import ComponentManifest


@dataclass(slots=True)
class ComponentTemplate:
    """A declarative component template."""

    template_id: str
    manifest: ComponentManifest
    slots: dict[str, str] = field(default_factory=dict)
    defaults: dict[str, Any] = field(default_factory=dict)
    description: str = ""


class TemplateRegistry:
    """Keeps component templates and exposes search helpers."""

    def __init__(self) -> None:
        self._templates: dict[str, ComponentTemplate] = {}

    # --------------------------------------------------------- registration

    def register(self, template: ComponentTemplate) -> None:
        if template.template_id in self._templates:
            raise ValueError(f"template {template.template_id!r} already registered")
        self._templates[template.template_id] = template

    def unregister(self, template_id: str) -> None:
        self._templates.pop(template_id, None)

    # -------------------------------------------------------------- lookup

    def get(self, template_id: str) -> ComponentTemplate | None:
        return self._templates.get(template_id)

    def list(self) -> list[ComponentTemplate]:
        return list(self._templates.values())

    def find_by_kind(self, kind: str) -> list[ComponentTemplate]:
        return [t for t in self._templates.values() if t.manifest.kind.value == kind]

    def __contains__(self, template_id: str) -> bool:
        return template_id in self._templates

    def __len__(self) -> int:
        return len(self._templates)
