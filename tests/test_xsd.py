"""Structural XSD validator tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from metaharness.config.xml_parser import parse_graph_xml
from metaharness.config.xsd_validator import XmlStructuralError, validate_harness_xml


def test_minimal_happy_path_passes(graphs_dir: Path) -> None:
    validate_harness_xml((graphs_dir / "minimal-happy-path.xml").read_text())


def test_minimal_expanded_passes(graphs_dir: Path) -> None:
    validate_harness_xml((graphs_dir / "minimal-expanded.xml").read_text())


def test_non_harness_root_is_rejected() -> None:
    doc = "<Nope version='0.1.0' graphVersion='1' schemaVersion='1.1'><Components/><Connections/></Nope>"
    with pytest.raises(XmlStructuralError) as excinfo:
        validate_harness_xml(doc)
    assert "root element must be <Harness>" in str(excinfo.value)


def test_missing_required_attribute_is_rejected() -> None:
    doc = """<Harness version='0.1.0' schemaVersion='1.1'>
        <Components/><Connections/>
    </Harness>"""
    with pytest.raises(XmlStructuralError) as excinfo:
        validate_harness_xml(doc)
    assert any("graphVersion" in issue for issue in excinfo.value.issues)


def test_invalid_mode_is_rejected() -> None:
    doc = """<Harness version='0.1.0' graphVersion='1' schemaVersion='1.1'>
        <Components>
          <Component id='a' type='x' impl='m' version='1'/>
          <Component id='b' type='x' impl='m' version='1'/>
        </Components>
        <Connections>
          <Connection id='c1' from='a.x' to='b.y' payload='T' mode='telepathy'/>
        </Connections>
    </Harness>"""
    with pytest.raises(XmlStructuralError) as excinfo:
        validate_harness_xml(doc)
    assert any("mode 'telepathy'" in issue for issue in excinfo.value.issues)


def test_duplicate_component_id_is_rejected() -> None:
    doc = """<Harness version='0.1.0' graphVersion='1' schemaVersion='1.1'>
        <Components>
          <Component id='a' type='x' impl='m' version='1'/>
          <Component id='a' type='x' impl='m' version='1'/>
        </Components>
        <Connections/>
    </Harness>"""
    with pytest.raises(XmlStructuralError) as excinfo:
        validate_harness_xml(doc)
    assert any("duplicate Component id 'a'" in issue for issue in excinfo.value.issues)


def test_parser_invokes_xsd_when_enabled() -> None:
    doc = "<Harness version='0.1.0' schemaVersion='1.1'><Components/><Connections/></Harness>"

    from io import StringIO  # noqa: F401  (silence unused import)

    tmp = Path("/tmp/_mhe_bad.xml")
    tmp.write_text(doc)
    try:
        with pytest.raises(XmlStructuralError):
            parse_graph_xml(tmp)
    finally:
        tmp.unlink(missing_ok=True)
