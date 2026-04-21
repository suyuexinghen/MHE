"""Shared SDK records used by registration and validation flows."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from metaharness.sdk.contracts import (
    CapabilityRequirement,
    EventPort,
    InputPort,
    OutputPort,
    SlotIntent,
)


class HookRecord(BaseModel):
    """Registered hook declaration."""

    name: str
    target: str


class ServiceRecord(BaseModel):
    """Registered background service declaration."""

    name: str
    entrypoint: str


class ValidatorRecord(BaseModel):
    """Registered semantic validator declaration."""

    name: str
    target: str


class ConnectionHandlerRecord(BaseModel):
    """Registered runtime connection handler declaration."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    target: str
    handler: object  # stored as opaque callable to avoid pydantic coercion


class MigrationAdapterRecord(BaseModel):
    """Registered state-migration adapter declaration."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    from_version: int
    to_version: int
    adapter: object  # opaque callable


class PendingDeclarations(BaseModel):
    """Collected declarations before atomic registration."""

    inputs: list[InputPort] = Field(default_factory=list)
    outputs: list[OutputPort] = Field(default_factory=list)
    events: list[EventPort] = Field(default_factory=list)
    provides: list[CapabilityRequirement] = Field(default_factory=list)
    requires: list[CapabilityRequirement] = Field(default_factory=list)
    slots: list[SlotIntent] = Field(default_factory=list)
    hooks: list[HookRecord] = Field(default_factory=list)
    services: list[ServiceRecord] = Field(default_factory=list)
    validators: list[ValidatorRecord] = Field(default_factory=list)
    connection_handlers: list[ConnectionHandlerRecord] = Field(default_factory=list)
    migration_adapters: list[MigrationAdapterRecord] = Field(default_factory=list)
    committed: bool = False
