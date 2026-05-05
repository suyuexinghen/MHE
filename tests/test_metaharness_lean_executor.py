from __future__ import annotations

from metaharness_ext.lean.backends import MockLeanBackend
from metaharness_ext.lean.contracts import LeanDiagnostic, LeanRunPlan
from metaharness_ext.lean.executor import LeanExecutorComponent, parse_lean_diagnostics
from metaharness_ext.lean.types import LeanDiagnosticSeverity


def test_parse_lean_diagnostics_warning_sorry() -> None:
    diagnostics = parse_lean_diagnostics(
        "Proofs/Main.lean:12:4: warning: declaration uses 'sorry'",
        "Proofs/Main.lean",
    )

    assert diagnostics[0].severity is LeanDiagnosticSeverity.WARNING
    assert diagnostics[0].code == "sorry"
    assert diagnostics[0].line == 12


def test_parse_lean_diagnostics_information() -> None:
    diagnostics = parse_lean_diagnostics(
        "Proofs/Main.lean:1:1: information: all good",
        "Proofs/Main.lean",
    )

    assert diagnostics[0].severity is LeanDiagnosticSeverity.INFO


def test_executor_mock_collects_sorry_locations() -> None:
    backend = MockLeanBackend(
        diagnostics=[LeanDiagnostic(message="declaration uses sorry", code="sorry")]
    )
    plan = LeanRunPlan(plan_id="plan-1", task_ref="task-1", target_file="Proofs/Main.lean")

    artifact = LeanExecutorComponent(backend).execute_plan(plan)

    assert artifact.backend == "mock"
    assert artifact.execution_mode == "dry_run"
    assert len(artifact.sorry_locations) == 1
