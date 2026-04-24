from metaharness.core.models import ScoredEvidence
from metaharness.demo import DemoHarness
from metaharness.sdk.lifecycle import ComponentPhase


def test_demo_harness_runs_minimal_graph() -> None:
    harness = DemoHarness()
    result = harness.run(task="hello world", trace_id="trace-test")

    assert result.graph_version == 1
    assert result.gateway_payload == {"task": "hello world"}
    assert result.runtime_payload["status"] == "runtime-ok"
    assert result.executor_payload["status"] == "executed"
    assert result.evaluation_payload["score"] == "1.0"
    assert result.policy_record == {"decision": "allow", "subject": "hello world"}
    assert result.audit_event == {
        "event_type": "demo_run",
        "subject": "hello world",
        "trace_id": "trace-test",
    }
    assert harness.engine.emit("gateway.primary.task", {"task": "second run"}) == [
        {"task": "second run", "status": "runtime-ok"}
    ]
    assert harness._last_executor_payload == {"task": "second run", "status": "executed"}
    assert harness._last_evaluation_payload == {"score": "1.0", "source_status": "executed"}
    assert result.lifecycle["runtime.primary"] == ComponentPhase.COMMITTED.value


def test_demo_harness_runs_expanded_topology() -> None:
    harness = DemoHarness(topology="expanded")
    result = harness.run(task="plan me", trace_id="trace-expanded")

    assert result.graph_version == 1
    assert result.plan_payload == {"task": "plan me", "plan": "basic"}
    assert result.executor_payload == {"task": "plan me", "status": "executed"}
    assert result.evaluation_payload == {"score": "1.0", "source_status": "executed"}
    assert result.memory_record == {"count": "1"}
    assert result.lifecycle["planner.primary"] == ComponentPhase.COMMITTED.value
    assert result.lifecycle["memory.primary"] == ComponentPhase.COMMITTED.value


def test_demo_async_run_produces_same_outputs() -> None:
    import asyncio

    harness = DemoHarness(topology="expanded")
    result = asyncio.run(harness.run_async(task="async", trace_id="trace-async"))

    assert result.graph_version == 1
    assert result.evaluation_payload["source_status"] == "executed"
    assert result.memory_record == {"count": "1"}


def test_scored_evidence_legacy_payload_round_trip() -> None:
    evidence = ScoredEvidence(score=1.0, attributes={"source_status": "executed"})
    payload = evidence.as_legacy_payload()
    restored = ScoredEvidence.from_legacy_payload(payload)
    assert payload == {"score": "1.0", "source_status": "executed"}
    assert restored.score == 1.0
    assert restored.attributes == {"source_status": "executed"}
