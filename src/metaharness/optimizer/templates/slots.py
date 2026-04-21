"""Slot-filling engine.

Given a :class:`ComponentTemplate` declaring named slots, produce a
concrete manifest by filling each slot with a caller-supplied value.
Unfilled slots with defaults are auto-populated.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from metaharness.optimizer.templates.registry import ComponentTemplate
from metaharness.sdk.manifest import ComponentManifest


@dataclass(slots=True)
class SlotBinding:
    """A slot name bound to a value."""

    slot: str
    value: Any


class SlotFillingEngine:
    """Fills template slots and produces instantiated manifests."""

    def bind(
        self,
        template: ComponentTemplate,
        bindings: dict[str, Any],
    ) -> list[SlotBinding]:
        out: list[SlotBinding] = []
        for slot, _description in template.slots.items():
            if slot in bindings:
                value = bindings[slot]
            elif slot in template.defaults:
                value = template.defaults[slot]
            else:
                raise ValueError(f"slot {slot!r} has no binding and no default")
            out.append(SlotBinding(slot=slot, value=value))
        return out

    def instantiate(
        self,
        template: ComponentTemplate,
        bindings: dict[str, Any],
        *,
        instance_suffix: str = ".primary",
    ) -> tuple[ComponentManifest, list[SlotBinding]]:
        """Return a materialised manifest plus resolved slot bindings.

        The manifest is a copy of ``template.manifest`` with ``id`` rewritten
        to include ``instance_suffix``; slot bindings are returned separately
        because :class:`ComponentManifest` intentionally does not store
        per-instance config (that is runtime-only).
        """

        resolved = self.bind(template, bindings)
        data = template.manifest.model_dump()
        data["id"] = f"{template.template_id}{instance_suffix}"
        data.setdefault("name", template.template_id)
        manifest = ComponentManifest.model_validate(data)
        return manifest, resolved


@dataclass(slots=True)
class SlotRuntimeBindings:
    """Small helper holding runtime-provided slot values."""

    values: dict[str, Any] = field(default_factory=dict)

    def set(self, slot: str, value: Any) -> None:
        self.values[slot] = value

    def as_dict(self) -> dict[str, Any]:
        return dict(self.values)
