"""Pure-Python structural validator mirroring the Harness XSD.

This validator enforces the structural rules that the bundled
``config/schema/harness.xsd`` declares. We intentionally avoid a hard
dependency on ``lxml`` so the MVP runtime stays pure Python while still
catching shape errors before semantic validation.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

_VALID_MODES = frozenset({"sync", "async", "event", "shadow"})
_VALID_POLICIES = frozenset({"required", "optional", "shadow"})


class XmlStructuralError(ValueError):
    """Raised when an XML graph document does not satisfy the structural schema."""

    def __init__(self, issues: list[str]) -> None:
        message = "; ".join(issues) if issues else "invalid harness document"
        super().__init__(message)
        self.issues = list(issues)


def _check_required_attrs(elem: ET.Element, names: list[str], issues: list[str]) -> None:
    for name in names:
        if name not in elem.attrib or not elem.attrib[name]:
            issues.append(f"<{elem.tag}> missing required attribute '{name}'")


def _validate_component(elem: ET.Element, issues: list[str]) -> None:
    _check_required_attrs(elem, ["id", "type", "impl", "version"], issues)
    protected = elem.attrib.get("protected")
    if protected is not None and protected not in {"true", "false", "1", "0"}:
        issues.append(
            f"Component '{elem.attrib.get('id', '?')}' has invalid protected='{protected}'"
        )


def _validate_connection(elem: ET.Element, issues: list[str]) -> None:
    _check_required_attrs(elem, ["id", "from", "to", "payload", "mode"], issues)
    mode = elem.attrib.get("mode")
    if mode is not None and mode not in _VALID_MODES:
        issues.append(f"Connection '{elem.attrib.get('id', '?')}' has invalid mode '{mode}'")
    policy = elem.attrib.get("policy")
    if policy is not None and policy not in _VALID_POLICIES:
        issues.append(f"Connection '{elem.attrib.get('id', '?')}' has invalid policy '{policy}'")


def validate_harness_document(root: ET.Element) -> None:
    """Validate a parsed ``<Harness>`` root against the structural schema.

    Raises :class:`XmlStructuralError` with the full list of issues found.
    """

    issues: list[str] = []

    if root.tag != "Harness":
        raise XmlStructuralError([f"root element must be <Harness>, got <{root.tag}>"])

    _check_required_attrs(root, ["version", "graphVersion", "schemaVersion"], issues)
    graph_version = root.attrib.get("graphVersion", "")
    if graph_version:
        try:
            if int(graph_version) <= 0:
                issues.append(f"graphVersion must be a positive integer, got '{graph_version}'")
        except ValueError:
            issues.append(f"graphVersion must be an integer, got '{graph_version}'")

    components_elem = root.find("./Components")
    connections_elem = root.find("./Connections")
    if components_elem is None:
        issues.append("<Harness> missing required child <Components>")
    if connections_elem is None:
        issues.append("<Harness> missing required child <Connections>")

    component_ids: set[str] = set()
    if components_elem is not None:
        for component in components_elem.findall("./Component"):
            _validate_component(component, issues)
            cid = component.attrib.get("id")
            if cid:
                if cid in component_ids:
                    issues.append(f"duplicate Component id '{cid}'")
                component_ids.add(cid)

    connection_ids: set[str] = set()
    if connections_elem is not None:
        for connection in connections_elem.findall("./Connection"):
            _validate_connection(connection, issues)
            cid = connection.attrib.get("id")
            if cid:
                if cid in connection_ids:
                    issues.append(f"duplicate Connection id '{cid}'")
                connection_ids.add(cid)

    if issues:
        raise XmlStructuralError(issues)


def validate_harness_xml(xml_text: str) -> None:
    """Parse ``xml_text`` and validate the resulting document."""

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:  # pragma: no cover - defensive
        raise XmlStructuralError([f"malformed XML: {exc}"]) from exc
    validate_harness_document(root)
