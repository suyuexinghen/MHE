"""ToolHub registration and execution tests."""

from __future__ import annotations

import asyncio

import pytest

from metaharness.components.toolhub import ToolHubComponent
from metaharness.safety import SandboxExecutionResult, SandboxTier
from metaharness.sdk.runtime import ComponentRuntime


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

    with pytest.raises(ValueError):
        hub.register_tool("x", callable=lambda: None)


class _SandboxClient:
    def __init__(self, *, supported: set[SandboxTier]) -> None:
        self.supported = supported
        self.calls: list[tuple[SandboxTier, dict[str, object]]] = []

    def supports_tier(self, tier: SandboxTier) -> bool:
        return tier in self.supported

    def execute(self, callable, *, tier: SandboxTier, arguments: dict[str, object]):  # noqa: ANN001
        self.calls.append((tier, dict(arguments)))
        return SandboxExecutionResult(tier=tier, success=True, output=callable(**arguments))


def test_execute_uses_runtime_sandbox_client() -> None:
    hub = ToolHubComponent()
    client = _SandboxClient(supported={SandboxTier.GVISOR})
    asyncio.run(hub.activate(ComponentRuntime(sandbox_client=client)))
    hub.register_tool("add", sandbox_tier="gvisor", callable=lambda a, b: a + b)

    record = hub.execute("add", {"a": 2, "b": 3})

    assert record.result == 5
    assert client.calls == [(SandboxTier.GVISOR, {"a": 2, "b": 3})]


def test_execute_rejects_unavailable_sandbox_tier() -> None:
    hub = ToolHubComponent()
    client = _SandboxClient(supported={SandboxTier.V8_WASM})
    asyncio.run(hub.activate(ComponentRuntime(sandbox_client=client)))
    hub.register_tool("add", sandbox_tier="firecracker", callable=lambda a, b: a + b)

    record = hub.execute("add", {"a": 2, "b": 3})

    assert record.result is None
    assert record.error == "sandbox policy requires tier 'firecracker'"
