from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from metaharness.config.xml_parser import parse_graph_xml
from metaharness.core.connection_engine import ConnectionEngine
from metaharness.core.graph_versions import GraphVersionStore
from metaharness.core.models import PendingConnectionSet
from metaharness.sdk.loader import declare_component, load_manifest
from metaharness.sdk.registry import ComponentRegistry
from metaharness_ext.ai4pde.components.evidence_manager import EvidenceManagerComponent
from metaharness_ext.ai4pde.components.experiment_memory import ExperimentMemoryComponent
from metaharness_ext.ai4pde.components.method_router import MethodRouterComponent
from metaharness_ext.ai4pde.components.pde_gateway import PDEGatewayComponent
from metaharness_ext.ai4pde.components.physics_validator import PhysicsValidatorComponent
from metaharness_ext.ai4pde.components.problem_formulator import ProblemFormulatorComponent
from metaharness_ext.ai4pde.components.reference_solver import ReferenceSolverComponent
from metaharness_ext.ai4pde.components.solver_executor import SolverExecutorComponent
from metaharness_ext.ai4pde.contracts import (
    PDEPlan,
    PDERunArtifact,
    PDETaskRequest,
    ScientificEvidenceBundle,
    ValidationBundle,
)

AI4PDE_COMPONENTS = [
    "pde_gateway",
    "problem_formulator",
    "method_router",
    "solver_executor",
    "reference_solver",
    "physics_validator",
    "evidence_manager",
    "experiment_memory",
    "risk_policy",
    "observability_hub",
    "knowledge_adapter",
]


@dataclass(slots=True)
class AI4PDECaseDemoResult:
    case_path: str
    graph_version: int
    task: PDETaskRequest
    plan: PDEPlan
    run_artifact: PDERunArtifact
    validation_bundle: ValidationBundle
    evidence_bundle: ScientificEvidenceBundle
    reference_result: dict[str, object]
    memory_record: dict[str, str]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "case_path": self.case_path,
            "graph_version": self.graph_version,
            "task": self.task.model_dump(mode="json"),
            "plan": self.plan.model_dump(mode="json"),
            "run_artifact": self.run_artifact.model_dump(mode="json"),
            "validation_bundle": self.validation_bundle.model_dump(mode="json"),
            "evidence_bundle": self.evidence_bundle.model_dump(mode="json"),
            "reference_result": self.reference_result,
            "memory_record": self.memory_record,
        }


class AI4PDECaseDemoHarness:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path(__file__).resolve().parents[3]
        self.examples_dir = self.root / "examples"
        self.manifest_dir = self.examples_dir / "manifests" / "ai4pde"
        self.graphs_dir = self.examples_dir / "graphs"

        self.registry = ComponentRegistry()
        self.store = GraphVersionStore()
        self.engine = ConnectionEngine(self.registry, self.store)

        self.gateway = PDEGatewayComponent()
        self.formulator = ProblemFormulatorComponent()
        self.router = MethodRouterComponent()
        self.executor = SolverExecutorComponent()
        self.reference_solver = ReferenceSolverComponent()
        self.validator = PhysicsValidatorComponent()
        self.evidence = EvidenceManagerComponent()
        self.memory = ExperimentMemoryComponent()

    def _register_manifests(self) -> None:
        for name in AI4PDE_COMPONENTS:
            manifest = load_manifest(self.manifest_dir / f"{name}.json")
            _, api = declare_component(f"{name}.primary", manifest)
            self.registry.register(f"{name}.primary", manifest, api.snapshot())

    def _commit_graph(self, graph_path: Path) -> int:
        snapshot = parse_graph_xml(graph_path)
        candidate, report = self.engine.stage(
            PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges)
        )
        if not report.valid:
            raise ValueError(f"AI4PDE graph is invalid: {report.issues}")
        return self.engine.commit(graph_path.stem, candidate, report)

    def run_case(self, case_path: str | Path) -> AI4PDECaseDemoResult:
        resolved_case_path = Path(case_path).resolve()
        self._register_manifests()
        task, compiled_plan = self.gateway.issue_task_from_case(resolved_case_path)
        graph_template = compiled_plan.parameter_overrides.get("runtime", {}).get("graph_template")
        graph_path = Path(graph_template) if graph_template else self.graphs_dir / "ai4pde-minimal.xml"
        graph_version = self._commit_graph(graph_path)

        formulated = self.formulator.formulate(task)
        plan = self.router.build_plan(formulated)
        run_artifact = self.executor.execute_plan(plan)
        reference_result = self.reference_solver.run_reference(plan)
        validation_bundle = self.validator.validate_run(
            run_artifact,
            graph_version_id=graph_version,
            reference_result=reference_result,
        )
        evidence_bundle = self.evidence.assemble_evidence(
            run_artifact,
            validation_bundle,
            reference_result=reference_result,
            graph_family=plan.graph_family,
        )
        memory_record = self.memory.remember(validation_bundle, evidence_bundle)
        return AI4PDECaseDemoResult(
            case_path=str(resolved_case_path),
            graph_version=graph_version,
            task=task,
            plan=plan,
            run_artifact=run_artifact,
            validation_bundle=validation_bundle,
            evidence_bundle=evidence_bundle,
            reference_result=reference_result.model_dump(mode="json"),
            memory_record=memory_record,
        )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run an AI4PDE case through the demo harness")
    parser.add_argument("case", help="path to AI4PDECase XML")
    args = parser.parse_args()

    result = AI4PDECaseDemoHarness().run_case(args.case)
    print(json.dumps(result.to_json_dict(), indent=2, sort_keys=True))
