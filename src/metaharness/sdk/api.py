"""Declaration API used by components during static registration."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from metaharness.sdk.contracts import (
    CapabilityRequirement,
    EventPort,
    InputPort,
    OutputPort,
    RouteMode,
    SlotBinding,
    SlotIntent,
)
from metaharness.sdk.models import (
    ConnectionHandlerRecord,
    HookRecord,
    MigrationAdapterRecord,
    PendingDeclarations,
    ServiceRecord,
    ValidatorRecord,
)
from metaharness.sdk.runtime import ComponentRuntime

Handler = Callable[[Any], Any] | Callable[[Any], Awaitable[Any]]
MigrationAdapter = (
    Callable[[Mapping[str, Any], Mapping[str, Any]], Mapping[str, Any]]
    | Callable[[Mapping[str, Any], Mapping[str, Any]], Awaitable[Mapping[str, Any]]]
)


class HarnessAPI:
    """Collects declarations before atomic registration."""

    def __init__(
        self,
        component_id: str,
        version: str,
        config: Mapping[str, Any],
        runtime: ComponentRuntime,
    ) -> None:
        self._component_id = component_id
        self._version = version
        self._config = dict(config)
        self._runtime = runtime
        self._pending = PendingDeclarations()

    @property
    def id(self) -> str:
        return self._component_id

    @property
    def version(self) -> str:
        return self._version

    @property
    def config(self) -> Mapping[str, Any]:
        return self._config

    @property
    def runtime(self) -> ComponentRuntime:
        return self._runtime

    @property
    def is_committed(self) -> bool:
        """Return whether ``_commit`` has frozen the declarations."""

        return self._pending.committed

    def declare_input(
        self,
        name: str,
        type: str,
        *,
        required: bool = True,
        description: str = "",
        cardinality: str = "one",
    ) -> None:
        self._check_open()
        self._pending.inputs.append(
            InputPort(
                name=name,
                type=type,
                required=required,
                description=description,
                cardinality=cardinality,
            )
        )

    def declare_output(
        self,
        name: str,
        type: str,
        *,
        mode: RouteMode | str = RouteMode.SYNC,
        description: str = "",
    ) -> None:
        self._check_open()
        normalized = mode if isinstance(mode, RouteMode) else RouteMode(mode)
        self._pending.outputs.append(
            OutputPort(name=name, type=type, mode=normalized, description=description)
        )

    def declare_event(self, name: str, payload_type: str, *, description: str = "") -> None:
        self._check_open()
        self._pending.events.append(
            EventPort(name=name, payloadType=payload_type, description=description)
        )

    def provide_capability(self, name: str, *, description: str = "") -> None:
        self._check_open()
        self._pending.provides.append(CapabilityRequirement(name=name, description=description))

    def require_capability(self, name: str, *, description: str = "") -> None:
        self._check_open()
        self._pending.requires.append(CapabilityRequirement(name=name, description=description))

    def bind_slot(
        self,
        slot: str,
        *,
        binding: SlotBinding | str = SlotBinding.PRIMARY,
        required: bool = True,
    ) -> None:
        self._check_open()
        normalized = binding if isinstance(binding, SlotBinding) else SlotBinding(binding)
        self._pending.slots.append(SlotIntent(slot=slot, binding=normalized, required=required))

    def reserve_slot(
        self,
        slot: str,
        *,
        binding: SlotBinding | str = SlotBinding.SECONDARY,
    ) -> None:
        self._check_open()
        normalized = binding if isinstance(binding, SlotBinding) else SlotBinding(binding)
        self._pending.slots.append(SlotIntent(slot=slot, binding=normalized, required=False))

    def register_hook(self, name: str, target: str) -> None:
        self._check_open()
        self._pending.hooks.append(HookRecord(name=name, target=target))

    def register_service(self, name: str, entrypoint: str) -> None:
        self._check_open()
        self._pending.services.append(ServiceRecord(name=name, entrypoint=entrypoint))

    def register_validator(self, name: str, target: str) -> None:
        self._check_open()
        self._pending.validators.append(ValidatorRecord(name=name, target=target))

    def register_connection_handler(self, target: str, handler: Handler) -> None:
        """Register a runtime handler for a target port.

        Handlers are attached to the :class:`ConnectionEngine` by the
        HarnessRuntime boot orchestrator after ``_commit``.
        """

        self._check_open()
        self._pending.connection_handlers.append(
            ConnectionHandlerRecord(target=target, handler=handler)
        )

    def register_migration_adapter(
        self, *, from_version: int, to_version: int, adapter: MigrationAdapter
    ) -> None:
        """Register a migration adapter between two state schema versions."""

        self._check_open()
        self._pending.migration_adapters.append(
            MigrationAdapterRecord(
                from_version=from_version, to_version=to_version, adapter=adapter
            )
        )

    def snapshot(self) -> PendingDeclarations:
        """Return a copy of the current pending declaration set."""

        return self._pending.model_copy(deep=True)

    def _commit(self) -> PendingDeclarations:
        """Freeze declarations and return an immutable snapshot.

        After ``_commit`` further declaration mutations raise. The returned
        snapshot is the authoritative declaration set consumed by the
        registry.
        """

        if self._pending.committed:
            raise RuntimeError(f"HarnessAPI for '{self._component_id}' already committed")
        self._pending.committed = True
        return self._pending.model_copy(deep=True)

    def _check_open(self) -> None:
        if self._pending.committed:
            raise RuntimeError(
                f"HarnessAPI for '{self._component_id}' is committed; cannot mutate declarations"
            )
