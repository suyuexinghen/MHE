"""Contract and vocabulary models for Meta-Harness."""

from enum import Enum

from pydantic import BaseModel, Field


class SlotBinding(str, Enum):
    """Supported slot binding roles."""

    PRIMARY = "primary"
    SECONDARY = "secondary"


class RouteMode(str, Enum):
    """Supported connection routing modes."""

    SYNC = "sync"
    ASYNC = "async"
    EVENT = "event"
    SHADOW = "shadow"


class ConnectionPolicy(str, Enum):
    """Connection-level policy semantics."""

    REQUIRED = "required"
    OPTIONAL = "optional"
    SHADOW = "shadow"


class InputPort(BaseModel):
    """Declared input contract for a component."""

    name: str
    type: str
    required: bool = True
    description: str = ""
    cardinality: str = "one"


class OutputPort(BaseModel):
    """Declared output contract for a component."""

    name: str
    type: str
    mode: RouteMode = RouteMode.SYNC
    description: str = ""


class EventPort(BaseModel):
    """Declared event contract for a component."""

    name: str
    payload_type: str = Field(alias="payloadType")
    description: str = ""

    model_config = {"populate_by_name": True}


class SlotIntent(BaseModel):
    """Requested slot binding for a component."""

    slot: str
    binding: SlotBinding = SlotBinding.PRIMARY
    required: bool = True


class CapabilityRequirement(BaseModel):
    """Capability provided or required by a component."""

    name: str
    description: str = ""
