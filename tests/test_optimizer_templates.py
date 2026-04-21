"""Tests for template registry, slot-filling, codegen, and migration adapters."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from metaharness.optimizer.templates.codegen import CodegenPipeline
from metaharness.optimizer.templates.migration import (
    MigrationAdapter,
    MigrationAdapterSystem,
)
from metaharness.optimizer.templates.registry import (
    ComponentTemplate,
    TemplateRegistry,
)
from metaharness.optimizer.templates.slots import SlotFillingEngine
from metaharness.sdk.manifest import ComponentManifest, ComponentType, ContractSpec


def _template(template_id: str = "tpl") -> ComponentTemplate:
    manifest = ComponentManifest(
        name=template_id,
        version="0.1.0",
        kind=ComponentType.TEMPLATE,
        entry=f"generated.{template_id}:{template_id.title()}Component",
        contracts=ContractSpec(),
    )
    return ComponentTemplate(
        template_id=template_id,
        manifest=manifest,
        slots={"retries": "max retry count", "bucket": "cache bucket name"},
        defaults={"retries": 3},
        description="demo template",
    )


def test_template_registry_register_and_lookup() -> None:
    registry = TemplateRegistry()
    template = _template()
    registry.register(template)
    assert len(registry) == 1
    assert "tpl" in registry
    assert registry.get("tpl") is template
    assert registry.find_by_kind("template") == [template]


def test_template_registry_duplicate_raises() -> None:
    registry = TemplateRegistry()
    template = _template()
    registry.register(template)
    with pytest.raises(ValueError):
        registry.register(template)


def test_slot_filling_engine_uses_defaults_and_bindings() -> None:
    template = _template()
    engine = SlotFillingEngine()
    bindings = engine.bind(template, {"bucket": "ws-1"})
    by_slot = {b.slot: b.value for b in bindings}
    assert by_slot == {"retries": 3, "bucket": "ws-1"}


def test_slot_filling_engine_raises_on_missing_binding() -> None:
    template = _template()
    engine = SlotFillingEngine()
    with pytest.raises(ValueError):
        engine.bind(template, {})  # 'bucket' has no default


def test_slot_filling_engine_instantiates_manifest() -> None:
    template = _template()
    engine = SlotFillingEngine()
    manifest, bindings = engine.instantiate(template, {"bucket": "ws-1"})
    assert manifest.resolved_id() == "tpl.primary"
    assert any(b.slot == "bucket" and b.value == "ws-1" for b in bindings)


def test_codegen_pipeline_emits_expected_artifacts(tmp_path: Path) -> None:
    template = _template()
    engine = SlotFillingEngine()
    manifest, bindings = engine.instantiate(template, {"bucket": "ws-1"})
    pipeline = CodegenPipeline()
    artifacts = pipeline.render(template, manifest, bindings, root=tmp_path)
    kinds = {a.kind for a in artifacts}
    assert kinds == {"manifest", "module", "graph_fragment"}
    pipeline.write_all(artifacts)
    manifest_path = tmp_path / "manifests" / "tpl.primary.json"
    assert manifest_path.exists()
    loaded = json.loads(manifest_path.read_text())
    assert loaded["id"] == "tpl.primary"


def test_migration_adapter_system_chains_adapters() -> None:
    system = MigrationAdapterSystem()
    system.register(
        MigrationAdapter(
            component_id="runtime",
            from_version=1,
            to_version=2,
            adapter=lambda state, delta: {**state, "v": 2},
        )
    )
    system.register(
        MigrationAdapter(
            component_id="runtime",
            from_version=2,
            to_version=3,
            adapter=lambda state, delta: {**state, "v": 3, "extra": True},
        )
    )
    result = system.migrate("runtime", 1, 3, {"v": 1})
    assert result == {"v": 3, "extra": True}
    assert system.steps("runtime", 1, 3) == [(1, 2), (2, 3)]


def test_migration_adapter_system_raises_on_missing_path() -> None:
    system = MigrationAdapterSystem()
    with pytest.raises(LookupError):
        system.migrate("runtime", 1, 5, {"v": 1})
