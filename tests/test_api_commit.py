"""HarnessAPI _commit, connection handler, and migration adapter tests."""

from __future__ import annotations

from metaharness.hotreload import MigrationAdapterRegistry
from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.runtime import ComponentRuntime


def test_api_commit_freezes_declarations() -> None:
    api = HarnessAPI(component_id="x", version="0.1.0", config={}, runtime=ComponentRuntime())
    api.declare_input("in", "T")
    snapshot = api._commit()
    assert snapshot.committed is True
    assert api.is_committed
    import pytest

    with pytest.raises(RuntimeError):
        api.declare_input("later", "T")


def test_api_register_connection_handler_and_migration_adapter() -> None:
    api = HarnessAPI(component_id="x", version="0.1.0", config={}, runtime=ComponentRuntime())

    def handler(_: object) -> int:
        return 1

    api.register_connection_handler("x.task", handler)
    api.register_migration_adapter(
        from_version=1, to_version=2, adapter=lambda old, delta: {**old, **delta}
    )

    snapshot = api.snapshot()
    assert snapshot.connection_handlers[0].target == "x.task"
    assert snapshot.migration_adapters[0].from_version == 1


def test_migration_registry_registers_api_declarations() -> None:
    api = HarnessAPI(component_id="x", version="0.1.0", config={}, runtime=ComponentRuntime())
    api.register_migration_adapter(
        from_version=1,
        to_version=2,
        adapter=lambda old, delta: {**old, "migrated": True, **(delta or {})},
    )

    registry = MigrationAdapterRegistry()
    registry.register_declarations(component_id="x", declarations=api.snapshot())

    resolved = registry.resolve(
        source_type="x",
        source_version=1,
        target_type="x",
        target_version=2,
    )
    assert resolved is not None
