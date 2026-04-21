"""Public port and route lookup structures compiled from a graph snapshot."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Literal

from metaharness.core.models import GraphSnapshot
from metaharness.sdk.contracts import ConnectionPolicy, RouteMode
from metaharness.sdk.registry import ComponentRegistry


@dataclass(slots=True, frozen=True)
class PortRef:
    """A fully-qualified component port reference."""

    component_id: str
    port: str
    payload_type: str
    direction: Literal["input", "output", "event"]

    @property
    def fqid(self) -> str:
        return f"{self.component_id}.{self.port}"


@dataclass(slots=True, frozen=True)
class RouteEntry:
    """A compiled route entry describing one edge."""

    connection_id: str
    source: PortRef
    target: PortRef
    mode: RouteMode
    policy: ConnectionPolicy


class PortIndex:
    """Fast lookup for component ports declared in the registry."""

    def __init__(self) -> None:
        self._by_fqid: dict[str, PortRef] = {}
        self._inputs: dict[str, list[PortRef]] = defaultdict(list)
        self._outputs: dict[str, list[PortRef]] = defaultdict(list)
        self._events: dict[str, list[PortRef]] = defaultdict(list)

    @classmethod
    def from_registry(cls, registry: ComponentRegistry) -> PortIndex:
        index = cls()
        for component_id, registered in registry.components.items():
            for port in registered.declarations.inputs:
                ref = PortRef(
                    component_id=component_id,
                    port=port.name,
                    payload_type=port.type,
                    direction="input",
                )
                index._by_fqid[ref.fqid] = ref
                index._inputs[component_id].append(ref)
            for port in registered.declarations.outputs:
                ref = PortRef(
                    component_id=component_id,
                    port=port.name,
                    payload_type=port.type,
                    direction="output",
                )
                index._by_fqid[ref.fqid] = ref
                index._outputs[component_id].append(ref)
            for port in registered.declarations.events:
                ref = PortRef(
                    component_id=component_id,
                    port=port.name,
                    payload_type=port.payload_type,
                    direction="event",
                )
                index._by_fqid[ref.fqid] = ref
                index._events[component_id].append(ref)
        return index

    def lookup(self, fqid: str) -> PortRef | None:
        return self._by_fqid.get(fqid)

    def inputs_of(self, component_id: str) -> list[PortRef]:
        return list(self._inputs.get(component_id, []))

    def outputs_of(self, component_id: str) -> list[PortRef]:
        return list(self._outputs.get(component_id, []))

    def events_of(self, component_id: str) -> list[PortRef]:
        return list(self._events.get(component_id, []))

    def all_outputs(self) -> list[PortRef]:
        return [ref for ports in self._outputs.values() for ref in ports]

    def all_inputs(self) -> list[PortRef]:
        return [ref for ports in self._inputs.values() for ref in ports]


class RouteTable:
    """Compiled route table built from a :class:`GraphSnapshot` + :class:`PortIndex`."""

    def __init__(self) -> None:
        self._by_source: dict[str, list[RouteEntry]] = defaultdict(list)
        self._by_target: dict[str, list[RouteEntry]] = defaultdict(list)
        self._by_connection_id: dict[str, RouteEntry] = {}

    @classmethod
    def build(cls, graph: GraphSnapshot, index: PortIndex) -> RouteTable:
        table = cls()
        for edge in graph.edges:
            source = index.lookup(edge.source) or PortRef(
                component_id=edge.source.rsplit(".", 1)[0],
                port=edge.source.rsplit(".", 1)[1] if "." in edge.source else "",
                payload_type=edge.payload,
                direction="output",
            )
            target = index.lookup(edge.target) or PortRef(
                component_id=edge.target.rsplit(".", 1)[0],
                port=edge.target.rsplit(".", 1)[1] if "." in edge.target else "",
                payload_type=edge.payload,
                direction="input",
            )
            entry = RouteEntry(
                connection_id=edge.connection_id,
                source=source,
                target=target,
                mode=edge.mode,
                policy=edge.policy,
            )
            table._by_source[source.fqid].append(entry)
            table._by_target[target.fqid].append(entry)
            table._by_connection_id[edge.connection_id] = entry
        return table

    def routes_from(self, source_fqid: str) -> list[RouteEntry]:
        return list(self._by_source.get(source_fqid, []))

    def routes_to(self, target_fqid: str) -> list[RouteEntry]:
        return list(self._by_target.get(target_fqid, []))

    def find(self, connection_id: str) -> RouteEntry | None:
        return self._by_connection_id.get(connection_id)

    def all_routes(self) -> list[RouteEntry]:
        return list(self._by_connection_id.values())
