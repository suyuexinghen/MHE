from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from metaharness.config.xml_parser import parse_graph_xml
from metaharness.core.boot import HarnessRuntime, bundled_discovery
from metaharness.core.models import PendingConnectionSet
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
        self.runtime = HarnessRuntime(bundled_discovery(self.manifest_dir))
        self._booted = False

    def _ensure_booted(self) -> None:
        if not self._booted:
            self.runtime.boot()
            self._booted = True

    def _get_component(self, component_id: str, component_type: type[object]) -> object:
        self._ensure_booted()
        component = self.runtime.components[component_id]
        if not isinstance(component, component_type):
            raise TypeError(f"Component {component_id} is not a {component_type.__name__}")
        return component

    def _commit_graph(self, graph_path: Path) -> int:
        self._ensure_booted()
        snapshot = parse_graph_xml(graph_path)
        return self.runtime.commit_graph(
            PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges),
            candidate_id=graph_path.stem,
        )

    def run_case(self, case_path: str | Path) -> AI4PDECaseDemoResult:
        resolved_case_path = Path(case_path).resolve()
        gateway = self._get_component("pde_gateway.primary", PDEGatewayComponent)
        formulator = self._get_component("problem_formulator.primary", ProblemFormulatorComponent)
        router = self._get_component("method_router.primary", MethodRouterComponent)
        executor = self._get_component("solver_executor.primary", SolverExecutorComponent)
        reference_solver = self._get_component("reference_solver.primary", ReferenceSolverComponent)
        validator = self._get_component("physics_validator.primary", PhysicsValidatorComponent)
        evidence = self._get_component("evidence_manager.primary", EvidenceManagerComponent)
        memory = self._get_component("experiment_memory.primary", ExperimentMemoryComponent)

        task, compiled_plan = gateway.issue_task_from_case(resolved_case_path)
        graph_template = compiled_plan.parameter_overrides.get("runtime", {}).get("graph_template")
        graph_path = (
            Path(graph_template) if graph_template else self.graphs_dir / "ai4pde-minimal.xml"
        )
        graph_version = self._commit_graph(graph_path)

        formulated = formulator.formulate(task)
        plan = router.build_plan(formulated)
        run_artifact = executor.execute_plan(plan)
        reference_result = reference_solver.run_reference(plan)
        validation_bundle = validator.validate_run(
            run_artifact,
            graph_version_id=graph_version,
            reference_result=reference_result,
        )
        evidence_bundle = evidence.assemble_evidence(
            run_artifact,
            validation_bundle,
            reference_result=reference_result,
            graph_family=plan.graph_family,
        )
        memory_record = memory.remember(validation_bundle, evidence_bundle)
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
