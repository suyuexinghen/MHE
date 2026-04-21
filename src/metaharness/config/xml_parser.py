"""XML import helpers for Meta-Harness graph configs."""

from __future__ import annotations

import asyncio
import xml.etree.ElementTree as ET
from pathlib import Path

from metaharness.config.xsd_validator import validate_harness_document
from metaharness.core.models import ComponentNode, ConnectionEdge, GraphSnapshot
from metaharness.sdk.contracts import ConnectionPolicy, RouteMode
from metaharness.sdk.lifecycle import ComponentPhase


def _build_snapshot(root: ET.Element) -> GraphSnapshot:
    graph_version = int(root.attrib.get("graphVersion", "0"))

    nodes: list[ComponentNode] = []
    for component in root.findall("./Components/Component"):
        config: dict[str, str] = {}
        config_node = component.find("Config")
        if config_node is not None:
            for child in config_node:
                config[child.tag] = child.text or ""
        nodes.append(
            ComponentNode(
                component_id=component.attrib["id"],
                component_type=component.attrib["type"],
                implementation=component.attrib["impl"],
                version=component.attrib["version"],
                phase=ComponentPhase.ASSEMBLED,
                protected=component.attrib.get("protected", "false") in {"true", "1"},
                config=config,
            )
        )

    edges: list[ConnectionEdge] = []
    for connection in root.findall("./Connections/Connection"):
        edges.append(
            ConnectionEdge(
                connection_id=connection.attrib["id"],
                source=connection.attrib["from"],
                target=connection.attrib["to"],
                payload=connection.attrib["payload"],
                mode=RouteMode(connection.attrib["mode"]),
                policy=ConnectionPolicy(
                    connection.attrib.get("policy", ConnectionPolicy.REQUIRED.value)
                ),
            )
        )

    return GraphSnapshot(graph_version=graph_version, nodes=nodes, edges=edges)


def parse_graph_xml(path: Path, *, validate_schema: bool = True) -> GraphSnapshot:
    """Parse a graph XML file into the internal graph snapshot model.

    If ``validate_schema`` is true, enforce the bundled structural XSD rules
    before building the snapshot.
    """

    root = ET.fromstring(path.read_text())
    if validate_schema:
        validate_harness_document(root)
    return _build_snapshot(root)


def parse_graph_xml_text(xml_text: str, *, validate_schema: bool = True) -> GraphSnapshot:
    """Parse a graph XML string into the internal graph snapshot model."""

    root = ET.fromstring(xml_text)
    if validate_schema:
        validate_harness_document(root)
    return _build_snapshot(root)


async def parse_graph_xml_async(path: Path, *, validate_schema: bool = True) -> GraphSnapshot:
    """Async variant of :func:`parse_graph_xml` using a thread pool."""

    return await asyncio.to_thread(parse_graph_xml, path, validate_schema=validate_schema)
