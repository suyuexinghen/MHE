from __future__ import annotations

from metaharness_ext.lean.backends import MockLeanBackend
from metaharness_ext.lean.contracts import LeanDiagnostic, LeanTaskSpec
from metaharness_ext.lean.gateway import LeanGatewayComponent
from metaharness_ext.lean.types import LeanDiagnosticSeverity, LeanValidationStatus


def test_gateway_formal_proof_dry_run_success() -> None:
    gateway = LeanGatewayComponent(MockLeanBackend())
    task = LeanTaskSpec(target_file="Proofs/Main.lean", target_lemma="main")

    bundle = gateway.prove_sorry(task)

    assert bundle.task_ref == "main"
    assert bundle.validation_report.status is LeanValidationStatus.FULLY_PROVEN
    assert bundle.artifacts[0].backend == "mock"


def test_gateway_formal_proof_dry_run_sorry() -> None:
    gateway = LeanGatewayComponent(
        MockLeanBackend(
            diagnostics=[
                LeanDiagnostic(
                    severity=LeanDiagnosticSeverity.WARNING,
                    message="declaration uses sorry",
                    code="sorry",
                )
            ]
        )
    )
    task = LeanTaskSpec(target_file="Proofs/Main.lean", target_lemma="main", budget=2)

    bundle = gateway.prove_sorry(task)

    assert bundle.validation_report.status is LeanValidationStatus.PARTIALLY_PROVEN
    assert bundle.validation_report.sorry_count == 1


def test_gateway_audit_dry_run_clean() -> None:
    gateway = LeanGatewayComponent(MockLeanBackend())
    task = LeanTaskSpec(target_file="Proofs/Main.lean")

    bundle = gateway.audit(task)

    assert bundle.task_ref == "audit:Proofs/Main.lean"
    assert bundle.validation_report.status is LeanValidationStatus.FULLY_PROVEN
    assert bundle.validation_report.audit_files == ["Proofs/Main.lean"]


def test_gateway_audit_dry_run_sorry() -> None:
    gateway = LeanGatewayComponent(
        MockLeanBackend(
            diagnostics=[
                LeanDiagnostic(
                    severity=LeanDiagnosticSeverity.WARNING,
                    message="declaration uses sorry",
                    code="sorry",
                )
            ]
        )
    )
    task = LeanTaskSpec(target_file="Proofs/Main.lean")

    bundle = gateway.audit(task)

    assert bundle.validation_report.status is LeanValidationStatus.BUDGET_EXHAUSTED
    assert bundle.validation_report.warning_count == 1


def test_gateway_audit_dry_run_error() -> None:
    gateway = LeanGatewayComponent(
        MockLeanBackend(
            exit_code=1,
            diagnostics=[
                LeanDiagnostic(
                    severity=LeanDiagnosticSeverity.ERROR,
                    message="unknown identifier",
                )
            ],
        )
    )
    task = LeanTaskSpec(target_file="Proofs/Main.lean")

    bundle = gateway.audit(task)

    assert bundle.validation_report.status is LeanValidationStatus.COMPILATION_FAILED
    assert bundle.validation_report.error_count == 1


def test_gateway_project_dry_run_orders_blueprint_items() -> None:
    gateway = LeanGatewayComponent(MockLeanBackend())
    task = LeanTaskSpec(
        target_file="Proofs/Main.lean",
        metadata={
            "blueprint_items": [
                {
                    "label": "main",
                    "lean_declaration": "main : True",
                    "file": "Proofs/Main.lean",
                    "uses": ["helper"],
                },
                {
                    "label": "helper",
                    "lean_declaration": "helper : True",
                    "file": "Proofs/Main.lean",
                },
            ]
        },
    )

    bundle = gateway.run_project(task)

    assert bundle.task_ref == "project:Proofs/Main.lean"
    assert bundle.validation_report.status is LeanValidationStatus.FULLY_PROVEN
    assert [artifact.plan_ref for artifact in bundle.artifacts] == [
        "plan:helper",
        "plan:main",
    ]
    assert bundle.blueprint is not None
    assert [item.label for item in bundle.blueprint.items] == ["helper", "main"]


def test_gateway_project_stops_on_partial_proof() -> None:
    gateway = LeanGatewayComponent(
        MockLeanBackend(
            diagnostics=[
                LeanDiagnostic(
                    severity=LeanDiagnosticSeverity.WARNING,
                    message="declaration uses sorry",
                    code="sorry",
                )
            ]
        )
    )
    task = LeanTaskSpec(
        target_file="Proofs/Main.lean",
        metadata={
            "blueprint_items": [
                {
                    "label": "helper",
                    "lean_declaration": "helper : True",
                    "file": "Proofs/Main.lean",
                },
                {
                    "label": "main",
                    "lean_declaration": "main : True",
                    "file": "Proofs/Main.lean",
                    "uses": ["helper"],
                },
            ]
        },
    )

    bundle = gateway.run_project(task)

    assert bundle.validation_report.status is LeanValidationStatus.PARTIALLY_PROVEN
    assert bundle.validation_report.sorry_count == 1
    assert [artifact.plan_ref for artifact in bundle.artifacts] == ["plan:helper"]
