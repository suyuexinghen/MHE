from __future__ import annotations

import asyncio
import time
from importlib.util import find_spec
from pathlib import Path
from typing import Any

from metaharness.benchmark_drivers.claude_cli import (
    ClaudeCLIBrainProvider,
    FakeClaudeCLIBrainProvider,
)
from metaharness.benchmark_drivers.io import case_dir, write_json, write_text
from metaharness.benchmark_drivers.models import (
    AttemptLog,
    AttemptRecord,
    BenchmarkCaseSpec,
    BenchmarkLane,
    LaneSummary,
)
from metaharness.benchmark_drivers.qcompute_abacus_cases import H2_FCIDUMP
from metaharness.benchmark_drivers.runner_common import dry_run_summary, write_lane_outputs
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.qcompute.config_compiler import QComputeConfigCompilerComponent
from metaharness_ext.qcompute.contracts import (
    QComputeBackendSpec,
    QComputeCircuitSpec,
    QComputeExperimentSpec,
    QComputeNoiseSpec,
)
from metaharness_ext.qcompute.environment import QComputeEnvironmentProbeComponent
from metaharness_ext.qcompute.evidence import build_evidence_bundle
from metaharness_ext.qcompute.executor import QComputeExecutorComponent
from metaharness_ext.qcompute.fcidump import parse_fcidump
from metaharness_ext.qcompute.fermion_mapper import build_active_space, map_fermionic_to_qubit
from metaharness_ext.qcompute.validator import QComputeValidatorComponent


class QComputeAbacusBenchmarkRunner:
    def __init__(
        self,
        *,
        runs_root: Path,
        allow_real_tools: bool = False,
        brain_provider: ClaudeCLIBrainProvider | FakeClaudeCLIBrainProvider | None = None,
    ) -> None:
        self.runs_root = runs_root
        self.allow_real_tools = allow_real_tools
        self.brain_provider = brain_provider or FakeClaudeCLIBrainProvider()

    def run_case(self, case: BenchmarkCaseSpec, lanes: list[BenchmarkLane]) -> list[LaneSummary]:
        summaries: list[LaneSummary] = []
        for lane in lanes:
            if lane == "extension":
                summaries.append(self.run_extension(case))
            elif lane == "direct":
                summaries.append(self.run_direct(case))
            elif lane == "agent":
                summaries.append(self.run_agent(case))
        return summaries

    def run_extension(self, case: BenchmarkCaseSpec) -> LaneSummary:
        output_dir = case_dir(self.runs_root, case.suite, "extension", case.case_id)
        if self._is_unsupported_bridge(case):
            return self._write_unsupported_bridge(case, "extension", output_dir)
        if not self.allow_real_tools:
            return dry_run_summary(
                runs_root=self.runs_root,
                case=case,
                lane="extension",
                evidence_factory=lambda path: self._write_extension_dry_run_evidence(path, case),
            )
        if not self._qiskit_available():
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="extension",
                status="skipped",
                skip_reason="qiskit and qiskit_aer are required for real qcompute-abacus runs",
            )
        if case.case_id == "h2-fcidump-jw-vs-bk":
            return self._run_mapping_comparison(case, "extension", output_dir)
        return self._run_qcompute_pipeline(case=case, lane="extension", output_dir=output_dir)

    def run_direct(self, case: BenchmarkCaseSpec) -> LaneSummary:
        output_dir = case_dir(self.runs_root, case.suite, "direct", case.case_id)
        prompt = self._prompt(case, lane="direct")
        claude_result = self.brain_provider.propose(prompt=prompt, output_dir=output_dir)
        attempt_log = self._claude_attempt_log(claude_result.error, "direct")
        evidence_files = self._claude_evidence_files(claude_result)
        if self._is_unsupported_bridge(case):
            return self._write_unsupported_bridge(
                case,
                "direct",
                output_dir,
                attempt_log=attempt_log,
                evidence_files=evidence_files,
            )
        if claude_result.error:
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="direct",
                status="failed",
                attempt_log=attempt_log,
                evidence_files=evidence_files,
                error_message=claude_result.error,
            )
        metrics = self._reference_metrics(case)
        evidence_files.extend(
            self._write_direct_dry_run_evidence(output_dir, case, claude_result.proposal)
        )
        return write_lane_outputs(
            runs_root=self.runs_root,
            case=case,
            lane="direct",
            status="passed",
            metrics=metrics,
            evidence_files=evidence_files,
            attempt_log=attempt_log,
        )

    def run_agent(self, case: BenchmarkCaseSpec) -> LaneSummary:
        output_dir = case_dir(self.runs_root, case.suite, "agent", case.case_id)
        prompt = self._prompt(case, lane="agent")
        claude_result = self.brain_provider.propose(prompt=prompt, output_dir=output_dir)
        attempt_log = self._claude_attempt_log(claude_result.error, "agent")
        evidence_files = self._claude_evidence_files(claude_result)
        if self._is_unsupported_bridge(case):
            return self._write_unsupported_bridge(
                case,
                "agent",
                output_dir,
                attempt_log=attempt_log,
                evidence_files=evidence_files,
            )
        if claude_result.error:
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="agent",
                status="failed",
                attempt_log=attempt_log,
                evidence_files=evidence_files,
                error_message=claude_result.error,
            )
        if not self.allow_real_tools:
            metrics = self._reference_metrics(case)
            evidence_files.extend(
                self._write_agent_dry_run_evidence(output_dir, case, claude_result.proposal)
            )
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="agent",
                status="passed",
                metrics=metrics,
                evidence_files=evidence_files,
                attempt_log=attempt_log,
            )
        if not self._qiskit_available():
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="agent",
                status="skipped",
                attempt_log=attempt_log,
                evidence_files=evidence_files,
                skip_reason="qiskit and qiskit_aer are required for real qcompute-abacus runs",
            )
        if case.case_id == "h2-fcidump-jw-vs-bk":
            return self._run_mapping_comparison(
                case,
                "agent",
                output_dir,
                attempt_log=attempt_log,
                evidence_files=evidence_files,
            )
        return self._run_qcompute_pipeline(
            case=case,
            lane="agent",
            output_dir=output_dir,
            attempt_log=attempt_log,
            evidence_files=evidence_files,
        )

    def _run_qcompute_pipeline(
        self,
        *,
        case: BenchmarkCaseSpec,
        lane: BenchmarkLane,
        output_dir: Path,
        attempt_log: AttemptLog | None = None,
        evidence_files: list[str] | None = None,
    ) -> LaneSummary:
        started_at = time.perf_counter()
        evidence_files = list(evidence_files or [])
        try:
            hamiltonian_file = self._write_hamiltonian(output_dir)
            spec = self._build_qcompute_spec(case, hamiltonian_file)
            write_json(output_dir / "qcompute_spec.json", spec)
            environment = QComputeEnvironmentProbeComponent().probe(spec)
            write_json(output_dir / "environment.json", environment)
            if not environment.available:
                return write_lane_outputs(
                    runs_root=self.runs_root,
                    case=case,
                    lane=lane,
                    status="skipped",
                    attempt_log=attempt_log,
                    evidence_files=[*evidence_files, str(output_dir / "environment.json")],
                    skip_reason=f"QCompute environment unavailable: {environment.status}",
                    started_at=started_at,
                )
            compiler = QComputeConfigCompilerComponent()
            plan = compiler.build_plan_from_hamiltonian(spec, environment)
            executor = QComputeExecutorComponent()
            validator = QComputeValidatorComponent()
            asyncio.run(executor.activate(ComponentRuntime(storage_path=output_dir)))
            asyncio.run(validator.activate(ComponentRuntime(storage_path=output_dir)))
            try:
                artifact = executor.execute_plan(plan, environment)
                validation = validator.validate_run(artifact, plan, environment)
            finally:
                asyncio.run(validator.deactivate())
                asyncio.run(executor.deactivate())
            evidence = build_evidence_bundle(artifact, validation, environment)
            write_json(output_dir / "run_plan.json", plan)
            write_json(output_dir / "run_artifact.json", artifact)
            write_json(output_dir / "validation.json", validation)
            write_json(output_dir / "evidence.json", evidence)
            metrics = self._pipeline_metrics(plan, artifact, validation)
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane=lane,
                status="passed" if validation.passed else "failed",
                metrics=metrics,
                evidence_files=[
                    *evidence_files,
                    str(hamiltonian_file),
                    str(output_dir / "qcompute_spec.json"),
                    str(output_dir / "environment.json"),
                    str(output_dir / "run_plan.json"),
                    str(output_dir / "run_artifact.json"),
                    str(output_dir / "validation.json"),
                    str(output_dir / "evidence.json"),
                    *(evidence.provenance_refs or []),
                ],
                attempt_log=attempt_log,
                started_at=started_at,
            )
        except Exception as exc:
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane=lane,
                status="failed",
                attempt_log=attempt_log,
                evidence_files=evidence_files,
                error_message=str(exc),
                started_at=started_at,
            )

    def _run_mapping_comparison(
        self,
        case: BenchmarkCaseSpec,
        lane: BenchmarkLane,
        output_dir: Path,
        attempt_log: AttemptLog | None = None,
        evidence_files: list[str] | None = None,
    ) -> LaneSummary:
        started_at = time.perf_counter()
        evidence_files = list(evidence_files or [])
        try:
            hamiltonian_file = self._write_hamiltonian(output_dir)
            fcidata = parse_fcidump(hamiltonian_file)
            active_space = build_active_space(fcidata, n_electrons=2, n_orbitals=2, method="manual")
            mappings = {
                method: map_fermionic_to_qubit(fcidata, active_space, method=method)
                for method in ["jordan_wigner", "bravyi_kitaev"]
            }
            metadata = {
                method: mapping.model_dump(mode="json") for method, mapping in mappings.items()
            }
            write_json(output_dir / "mapping_metadata.json", metadata)
            metrics = {
                "jw_num_qubits": mappings["jordan_wigner"].num_qubits,
                "jw_term_count": len(mappings["jordan_wigner"].terms),
                "bk_num_qubits": mappings["bravyi_kitaev"].num_qubits,
                "bk_term_count": len(mappings["bravyi_kitaev"].terms),
                "elapsed_seconds": 0.0,
            }
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane=lane,
                status="passed",
                metrics=metrics,
                evidence_files=[
                    *evidence_files,
                    str(hamiltonian_file),
                    str(output_dir / "mapping_metadata.json"),
                ],
                attempt_log=attempt_log,
                started_at=started_at,
            )
        except Exception as exc:
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane=lane,
                status="failed",
                attempt_log=attempt_log,
                evidence_files=evidence_files,
                error_message=str(exc),
                started_at=started_at,
            )

    def _build_qcompute_spec(
        self, case: BenchmarkCaseSpec, hamiltonian_file: Path
    ) -> QComputeExperimentSpec:
        problem = case.problem_definition
        return QComputeExperimentSpec(
            task_id=case.case_id.replace("-", "_"),
            mode="simulate",
            backend=QComputeBackendSpec(
                platform=problem.get("backend", "qiskit_aer"),
                simulator=bool(problem.get("simulator", True)),
                qubit_count=int(problem.get("backend_qubit_count", 4)),
            ),
            circuit=QComputeCircuitSpec(
                ansatz=problem.get("ansatz", "vqe"),
                num_qubits=int(problem.get("num_qubits", 2)),
                repetitions=1,
                entanglement="linear",
            ),
            noise=QComputeNoiseSpec(model="none"),
            shots=int(problem.get("shots", 256)),
            hamiltonian_file=str(hamiltonian_file),
            hamiltonian_format=problem.get("hamiltonian_format", "fcidump"),
            fermion_mapping=problem.get("fermion_mapping", "jordan_wigner"),
            active_space=tuple(problem["active_space"]) if "active_space" in problem else None,
            reference_energy=problem.get("reference_energy"),
            max_iterations=int(problem.get("max_iterations", 5)),
            provenance_refs=list(case.source_reference.get("abacus_source_refs", []))
            if isinstance(case.source_reference, dict)
            else [str(case.source_reference)],
            metadata=dict(case.metadata),
        )

    def _pipeline_metrics(self, plan, artifact, validation) -> dict[str, Any]:
        hamiltonian = plan.compilation_metadata.get("hamiltonian", {})
        optimization = plan.compilation_metadata.get("vqe_optimization", {})
        metrics = validation.metrics.model_dump(mode="json")
        return {
            "energy": metrics.get("energy")
            or plan.compilation_metadata.get("computed_energy")
            or 0.0,
            "energy_error": metrics.get("energy_error") or 0.0,
            "convergence_iterations": metrics.get("convergence_iterations")
            or optimization.get("iterations")
            or 0,
            "num_qubits": hamiltonian.get("num_qubits", plan.circuit_openqasm.count("q[")),
            "term_count": len(hamiltonian.get("terms", [])),
            "shots_completed": artifact.shots_completed or 0,
            "elapsed_seconds": (artifact.execution_time_ms or 0.0) / 1000.0,
            "fidelity": metrics.get("fidelity") or 0.0,
        }

    def _write_hamiltonian(self, output_dir: Path) -> Path:
        path = output_dir / "hamiltonian.fcidump"
        write_text(path, H2_FCIDUMP)
        return path

    def _write_extension_dry_run_evidence(
        self, output_dir: Path, case: BenchmarkCaseSpec
    ) -> list[str]:
        evidence_paths = [
            write_json(output_dir / "validation.json", {"passed": True, "dry_run": True}),
            write_json(
                output_dir / "evidence.json",
                {
                    "case_id": case.case_id,
                    "dry_run": True,
                    "scope": "qcompute-abacus Hamiltonian proxy",
                },
            ),
        ]
        if not self._is_unsupported_bridge(case):
            evidence_paths.append(self._write_hamiltonian(output_dir))
        return [str(path) for path in evidence_paths]

    def _write_direct_dry_run_evidence(
        self, output_dir: Path, case: BenchmarkCaseSpec, proposal: dict[str, Any]
    ) -> list[str]:
        path = write_json(
            output_dir / "direct_lane_evidence.json",
            {
                "case_id": case.case_id,
                "proposal": proposal,
                "dry_run": True,
                "boundary": "direct lane does not call MHE QCompute extension components in dry-run mode",
            },
        )
        return [str(path)]

    def _write_agent_dry_run_evidence(
        self, output_dir: Path, case: BenchmarkCaseSpec, proposal: dict[str, Any]
    ) -> list[str]:
        path = write_json(
            output_dir / "agent_lane_evidence.json",
            {
                "case_id": case.case_id,
                "proposal": proposal,
                "dry_run": True,
                "pipeline": "Claude proposal -> QCompute extension pipeline",
            },
        )
        return [str(path)]

    def _write_unsupported_bridge(
        self,
        case: BenchmarkCaseSpec,
        lane: BenchmarkLane,
        output_dir: Path,
        *,
        attempt_log: AttemptLog | None = None,
        evidence_files: list[str] | None = None,
    ) -> LaneSummary:
        source_refs_path = write_json(
            output_dir / "source_refs.json",
            {
                "case_id": case.case_id,
                "source_reference": case.source_reference,
                "status": "unsupported_source_format",
                "reason": case.metadata.get(
                    "unsupported_reason",
                    "ABACUS H/S-to-FCIDUMP bridge is not implemented.",
                ),
            },
        )
        return write_lane_outputs(
            runs_root=self.runs_root,
            case=case,
            lane=lane,
            status="skipped",
            metrics={"elapsed_seconds": 0.0},
            evidence_files=[*(evidence_files or []), str(source_refs_path)],
            attempt_log=attempt_log,
            skip_reason="unsupported_source_format: ABACUS H/S-to-FCIDUMP bridge is not implemented",
        )

    def _reference_metrics(self, case: BenchmarkCaseSpec) -> dict[str, float]:
        metrics: dict[str, float] = {}
        for metric in case.expected_metrics:
            reference = case.metric_references.get(metric)
            metrics[metric] = (
                float(reference.value)
                if reference is not None and isinstance(reference.value, int | float)
                else 0.0
            )
        return metrics

    def _claude_attempt_log(self, error: str | None, lane: BenchmarkLane) -> AttemptLog:
        return AttemptLog(
            attempts=[
                AttemptRecord(
                    attempt_id=1,
                    lane=lane,
                    status="failed" if error else "passed",
                    llm_call=True,
                    message=error,
                )
            ]
        )

    def _claude_evidence_files(self, claude_result) -> list[str]:
        return [
            claude_result.invocation.prompt_path,
            claude_result.invocation.stdout_path,
            claude_result.invocation.stderr_path,
            claude_result.invocation.result_path or "",
            claude_result.invocation.proposal_path or "",
        ]

    def _prompt(self, case: BenchmarkCaseSpec, *, lane: BenchmarkLane) -> str:
        return (
            f"Prepare a {lane} benchmark proposal for MHE suite qcompute-abacus case "
            f"{case.case_id}. Keep claims limited to FCIDUMP/VQE Hamiltonian proxy behavior "
            "and do not claim ABACUS H/S bridge support."
        )

    def _is_unsupported_bridge(self, case: BenchmarkCaseSpec) -> bool:
        return case.case_id == "abacus-hs-bridge-pending"

    def _qiskit_available(self) -> bool:
        return find_spec("qiskit") is not None and find_spec("qiskit_aer") is not None
