"""ToolHub registration and execution tests."""

from __future__ import annotations

from metaharness.components.toolhub import ToolHubComponent


def test_tool_registration_and_lookup() -> None:
    hub = ToolHubComponent()
    hub.register_tool("echo", description="echo back", tags=("debug",), callable=lambda **kw: kw)
    assert {t.name for t in hub.list_tools()} == {"echo"}
    assert hub.get("echo") is not None
    assert hub.find_tools(tag="debug")[0].name == "echo"


def test_execute_records_success() -> None:
    hub = ToolHubComponent()
    hub.register_tool("add", callable=lambda a, b: a + b)
    record = hub.execute("add", {"a": 2, "b": 3}, trace_id="t")
    assert record.result == 5
    assert record.error is None
    assert record.trace_id == "t"


def test_execute_records_failure() -> None:
    hub = ToolHubComponent()

    def boom(**_: object) -> None:
        raise RuntimeError("bad tool")

    hub.register_tool("boom", callable=boom)
    record = hub.execute("boom")
    assert record.error == "bad tool"
    assert record.result is None


def test_execute_unknown_tool() -> None:
    hub = ToolHubComponent()
    record = hub.execute("missing")
    assert "not executable" in (record.error or "")


def test_duplicate_registration_fails() -> None:
    hub = ToolHubComponent()
    hub.register_tool("x", callable=lambda: None)
    import pytest

    with pytest.raises(ValueError):
        hub.register_tool("x", callable=lambda: None)
