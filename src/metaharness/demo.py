"""Runnable demo harness for the Meta-Harness minimal graph."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from metaharness.components.evaluation import EvaluationComponent
from metaharness.components.executor import ExecutorComponent
from metaharness.components.gateway import GatewayComponent
from metaharness.components.memory import MemoryComponent
from metaharness.components.observability import ObservabilityComponent
from metaharness.components.planner import PlannerComponent
from metaharness.components.policy import PolicyComponent
from metaharness.components.runtime import RuntimeComponent
from metaharness.config.xml_parser import parse_graph_xml
from metaharness.core.connection_engine import ConnectionEngine
from metaharness.core.graph_versions import GraphVersionStore
from metaharness.core.lifecycle_tracker import LifecycleTracker
from metaharness.core.models import PendingConnectionSet
from metaharness.sdk.lifecycle import ComponentPhase
from metaharness.sdk.loader import declare_component, load_manifest
from metaharness.sdk.registry import ComponentRegistry

Topology = Literal["minimal", "expanded"]

_MINIMAL_COMPONENTS = ["gateway", "runtime", "executor", "evaluation"]
_EXPANDED_COMPONENTS = [
    "gateway",
    "runtime",
    "planner",
    "executor",
    "evaluation",
    "memory",
]
_CONTROL_PLANE = ["policy", "observability"]


@dataclass(slots=True)
class DemoResult:
    """Structured result returned by the demo harness."""

    graph_version: int
    trace_id: str
    gateway_payload: dict[str, str]
    runtime_payload: dict[str, str]
    executor_payload: dict[str, str]
    evaluation_payload: dict[str, str]
    policy_record: dict[str, str]
    audit_event: dict[str, str]
    plan_payload: dict[str, str] | None = None
    memory_record: dict[str, str] | None = None
    lifecycle: dict[str, str] = field(default_factory=dict)


class DemoHarness:
    """Runs the minimal or expanded Meta-Harness graph end-to-end."""

    def __init__(self, root: Path | None = None, *, topology: Topology = "minimal") -> None:
        self.root = root or Path(__file__).resolve().parents[2]
        self.examples_dir = self.root / "examples"
        self.manifest_dir = self.examples_dir / "manifests" / "baseline"
        self.topology = topology
        graph_name = "minimal-expanded.xml" if topology == "expanded" else "minimal-happy-path.xml"
        self.graph_path = self.examples_dir / "graphs" / graph_name

        self.registry = ComponentRegistry()
        self.store = GraphVersionStore()
        self.engine = ConnectionEngine(self.registry, self.store)
        self.lifecycle = LifecycleTracker()

        self.gateway = GatewayComponent()
        self.runtime = RuntimeComponent()
        self.executor = ExecutorComponent()
        self.evaluation = EvaluationComponent()
        self.planner = PlannerComponent()
        self.memory = MemoryComponent()
        self.policy = PolicyComponent()
        self.observability = ObservabilityComponent()

        self._last_plan_payload: dict[str, str] | None = None
        self._last_runtime_payload: dict[str, str] | None = None
        self._last_executor_payload: dict[str, str] | None = None
        self._last_evaluation_payload: dict[str, str] | None = None
        self._last_memory_record: dict[str, str] | None = None

    # ------------------------------------------------------------------ wiring

    def _component_names(self) -> list[str]:
        if self.topology == "expanded":
            return _EXPANDED_COMPONENTS + _CONTROL_PLANE
        return _MINIMAL_COMPONENTS + _CONTROL_PLANE

    def _register_manifests(self) -> None:
        for name in self._component_names():
            manifest = load_manifest(self.manifest_dir / f"{name}.json")
            _, api = declare_component(f"{name}.primary", manifest)
            self.registry.register(f"{name}.primary", manifest, api.snapshot())
            self.lifecycle.record(f"{name}.primary", ComponentPhase.DISCOVERED)
            self.lifecycle.record(f"{name}.primary", ComponentPhase.VALIDATED_STATIC)

    def _register_handlers(self) -> None:
        if self.topology == "expanded":
            self.engine.register_handler("runtime.primary.task", self._handle_runtime)
            self.engine.register_handler("planner.primary.task", self._handle_planner)
            self.engine.register_handler("executor.primary.task", self._handle_executor)
            self.engine.register_handler("evaluation.primary.task_result", self._handle_evaluation)
            self.engine.register_handler("memory.primary.task_result", self._handle_memory)
        else:
            self.engine.register_handler("runtime.primary.task", self._handle_runtime)
            self.engine.register_handler("executor.primary.task", self._handle_executor)
            self.engine.register_handler("evaluation.primary.task_result", self._handle_evaluation)

    # --------------------------------------------------------------- handlers

    def _handle_runtime(self, payload: dict[str, str]) -> dict[str, str]:
        self._last_runtime_payload = self.runtime.handle_task(payload)
        self.engine.emit("runtime.primary.result", self._last_runtime_payload)
        return self._last_runtime_payload

    def _handle_planner(self, payload: dict[str, str]) -> dict[str, str]:
        self._last_plan_payload = self.planner.make_plan(payload)
        self.engine.emit("planner.primary.plan", self._last_plan_payload)
        return self._last_plan_payload

    def _handle_executor(self, payload: dict[str, str]) -> dict[str, str]:
        self._last_executor_payload = self.executor.handle_task(payload)
        self.engine.emit("executor.primary.result", self._last_executor_payload)
        return self._last_executor_payload

    def _handle_evaluation(self, payload: dict[str, str]) -> dict[str, str]:
        self._last_evaluation_payload = self.evaluation.handle_result(payload)
        return self._last_evaluation_payload

    def _handle_memory(self, payload: dict[str, str]) -> dict[str, str]:
        self._last_memory_record = self.memory.remember(payload)
        return self._last_memory_record

    # ----------------------------------------------------------------- commit

    def _commit_graph(self, *, label: str) -> int:
        snapshot = parse_graph_xml(self.graph_path)
        candidate, report = self.engine.stage(
            PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges)
        )
        decision = "allow" if report.valid else "reject"
        self.policy.record(decision, label)
        self.observability.record_event("graph_commit_attempt", label, "trace-demo-graph")
        version = self.engine.commit(f"demo-{label}", candidate, report)
        if not report.valid:
            raise ValueError(f"Demo graph '{label}' is invalid: {report.issues}")
        for node in candidate.nodes:
            self.lifecycle.record(node.component_id, ComponentPhase.ASSEMBLED)
            self.lifecycle.record(node.component_id, ComponentPhase.VALIDATED_DYNAMIC)
            self.lifecycle.record(node.component_id, ComponentPhase.ACTIVATED)
            self.lifecycle.record(node.component_id, ComponentPhase.COMMITTED)
        self._register_handlers()
        return version

    # ------------------------------------------------------------------- api

    def run(self, task: str = "demo task", trace_id: str = "trace-demo-1") -> DemoResult:
        """Run the configured topology end-to-end and return observed outputs."""

        self._register_manifests()
        graph_version = self._commit_graph(label=self.topology)

        gateway_payload = self.gateway.issue_task(task)
        self.engine.emit("gateway.primary.task", gateway_payload)
        policy_record = self.policy.record("allow", task)
        audit_event = self.observability.record_event("demo_run", task, trace_id)

        return DemoResult(
            graph_version=graph_version,
            trace_id=trace_id,
            gateway_payload=gateway_payload,
            runtime_payload=self._last_runtime_payload or {},
            executor_payload=self._last_executor_payload or {},
            evaluation_payload=self._last_evaluation_payload or {},
            policy_record=policy_record,
            audit_event=audit_event,
            plan_payload=self._last_plan_payload,
            memory_record=self._last_memory_record,
            lifecycle={cid: phase.value for cid, phase in self.lifecycle.snapshot().items()},
        )

    async def run_async(
        self, task: str = "demo task", trace_id: str = "trace-demo-1"
    ) -> DemoResult:
        """Async variant that uses the async emit path."""

        self._register_manifests()
        graph_version = self._commit_graph(label=self.topology)

        gateway_payload = self.gateway.issue_task(task)
        await self.engine.emit_async("gateway.primary.task", gateway_payload)
        policy_record = self.policy.record("allow", task)
        audit_event = self.observability.record_event("demo_run", task, trace_id)

        return DemoResult(
            graph_version=graph_version,
            trace_id=trace_id,
            gateway_payload=gateway_payload,
            runtime_payload=self._last_runtime_payload or {},
            executor_payload=self._last_executor_payload or {},
            evaluation_payload=self._last_evaluation_payload or {},
            policy_record=policy_record,
            audit_event=audit_event,
            plan_payload=self._last_plan_payload,
            memory_record=self._last_memory_record,
            lifecycle={cid: phase.value for cid, phase in self.lifecycle.snapshot().items()},
        )


def main() -> None:
    """Entry point for the ``metaharness-demo`` console script."""

    import argparse

    parser = argparse.ArgumentParser(description="Run the Meta-Harness demo graph")
    parser.add_argument(
        "--topology",
        choices=["minimal", "expanded"],
        default="minimal",
        help="demo topology to run",
    )
    parser.add_argument("--task", default="demo task", help="task payload to submit")
    parser.add_argument("--trace-id", default="trace-demo-1", help="trace id for audit events")
    parser.add_argument(
        "--async-mode", action="store_true", help="drive the demo via the async dispatch path"
    )
    args = parser.parse_args()

    harness = DemoHarness(topology=args.topology)
    if args.async_mode:
        result = asyncio.run(harness.run_async(task=args.task, trace_id=args.trace_id))
    else:
        result = harness.run(task=args.task, trace_id=args.trace_id)

    print(f"topology={args.topology}")
    print(f"graph_version={result.graph_version}")
    print(f"trace_id={result.trace_id}")
    print(f"task={result.gateway_payload['task']}")
    print(f"runtime_status={result.runtime_payload.get('status', '-')}")
    if result.plan_payload is not None:
        print(f"plan={result.plan_payload.get('plan', '-')}")
    print(f"executor_status={result.executor_payload.get('status', '-')}")
    print(f"score={result.evaluation_payload.get('score', '-')}")
    if result.memory_record is not None:
        print(f"memory_count={result.memory_record.get('count', '-')}")


if __name__ == "__main__":
    main()
