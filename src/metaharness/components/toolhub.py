"""ToolHub component: tool registration, discovery, and sandboxed execution."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from metaharness.safety import parse_sandbox_tier
from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime

ToolCallable = Callable[..., Any] | Callable[..., Awaitable[Any]]


@dataclass(slots=True)
class ToolSpec:
    """Metadata describing a registered tool."""

    name: str
    description: str
    sandbox_tier: str = "v8"
    tags: tuple[str, ...] = ()
    callable: ToolCallable | None = None


@dataclass(slots=True)
class ToolExecutionRecord:
    """Audit trail entry for a tool invocation."""

    name: str
    arguments: dict[str, Any]
    result: Any | None
    error: str | None = None
    trace_id: str | None = None


class ToolHubComponent(HarnessComponent):
    """In-memory tool registry with optional sandbox-aware execution.

    The ToolHub is intentionally decoupled from the Executor. Tools register
    themselves with :meth:`register_tool`; the Executor calls
    :meth:`execute` when it needs to dispatch work to a named tool. The
    sandbox integration is declarative (``sandbox_tier``): when the
    :attr:`runtime.sandbox_client` is present it is consulted before running
    the callable, but the default implementation still runs the tool
    in-process to keep the MVP test suite portable.
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}
        self.execution_log: list[ToolExecutionRecord] = field(default_factory=list)  # type: ignore[assignment]
        self.execution_log = []
        self._runtime: ComponentRuntime | None = None

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot("toolhub.primary")
        api.provide_capability("tool.invoke")
        api.register_service("tool_registry", "metaharness.components.toolhub:ToolHubComponent")

    # ------------------------------------------------------------------ API

    def register_tool(
        self,
        name: str,
        *,
        description: str = "",
        sandbox_tier: str = "v8",
        tags: tuple[str, ...] = (),
        callable: ToolCallable | None = None,
    ) -> None:
        """Register a tool under ``name``."""

        if name in self._tools:
            raise ValueError(f"Tool '{name}' is already registered")
        self._tools[name] = ToolSpec(
            name=name,
            description=description,
            sandbox_tier=sandbox_tier,
            tags=tags,
            callable=callable,
        )

    def unregister_tool(self, name: str) -> None:
        self._tools.pop(name, None)

    def list_tools(self) -> list[ToolSpec]:
        return list(self._tools.values())

    def find_tools(self, *, tag: str | None = None) -> list[ToolSpec]:
        results: list[ToolSpec] = []
        for spec in self._tools.values():
            if tag is not None and tag not in spec.tags:
                continue
            results.append(spec)
        return results

    def get(self, name: str) -> ToolSpec | None:
        return self._tools.get(name)

    def execute(
        self, name: str, arguments: dict[str, Any] | None = None, *, trace_id: str | None = None
    ) -> ToolExecutionRecord:
        """Synchronously execute a registered tool and record the outcome."""

        arguments = dict(arguments or {})
        spec = self._tools.get(name)
        if spec is None or spec.callable is None:
            record = ToolExecutionRecord(
                name=name,
                arguments=arguments,
                result=None,
                error=f"tool '{name}' is not executable",
                trace_id=trace_id,
            )
            self.execution_log.append(record)
            return record
        try:
            runtime = self._runtime
            if runtime is not None:
                declared_tier = parse_sandbox_tier(spec.sandbox_tier)
                runtime.require_sandbox_tier(declared_tier)
                client = runtime.sandbox_client
                if client is not None and hasattr(client, "execute"):
                    sandbox_result = client.execute(
                        spec.callable, tier=declared_tier, arguments=arguments
                    )
                    if getattr(sandbox_result, "success", True) is False:
                        raise RuntimeError(
                            getattr(sandbox_result, "error", "sandbox execution failed")
                        )
                    result = getattr(sandbox_result, "output", sandbox_result)
                else:
                    result = spec.callable(**arguments)
            else:
                result = spec.callable(**arguments)
        except Exception as exc:  # noqa: BLE001
            record = ToolExecutionRecord(
                name=name, arguments=arguments, result=None, error=str(exc), trace_id=trace_id
            )
            self.execution_log.append(record)
            return record
        record = ToolExecutionRecord(
            name=name, arguments=arguments, result=result, trace_id=trace_id
        )
        self.execution_log.append(record)
        return record
