from __future__ import annotations

import asyncio
from pathlib import Path

from _shared import runtime_path

from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.qcompute import (
    QComputeBackendSpec,
    QComputeCircuitSpec,
    QComputeConfigCompilerComponent,
    QComputeEnvironmentProbeComponent,
    QComputeExecutorComponent,
    QComputeExperimentSpec,
    QComputeNoiseSpec,
    QComputeValidatorComponent,
)

H2_FCIDUMP = """ &FCI NORB=2,NELEC=2,MS2=0,
   ORBSYM=1,1,
   ISYM=1,
 &END
  1.834752942932  1  1  0  0
  0.715403888080  2  1  0  0
  0.663476275792  2  2  0  0
  0.181293137885  1  1  1  1
  0.663476275792  2  2  2  2
  0.715403888080  1  2  0  0
  0.181293137885  2  2  1  1
  0.120365812741  2  1  2  1
  0.120365812741  1  2  1  2
  0.675710775216  2  2  2  1
  0.675710775216  2  1  2  2
  0.000000000000  0  0  0  0
"""


def write_h2_fcidump(path: Path) -> Path:
    path.write_text(H2_FCIDUMP, encoding="utf-8")
    return path


async def run_demo() -> None:
    runtime_dir = runtime_path("vqe")
    hamiltonian_file = write_h2_fcidump(runtime_dir / "h2_sto3g.fcidump")
    spec = QComputeExperimentSpec(
        task_id="qcompute-vqe-demo",
        mode="simulate",
        backend=QComputeBackendSpec(platform="qiskit_aer", simulator=True, qubit_count=4),
        circuit=QComputeCircuitSpec(
            ansatz="vqe",
            num_qubits=2,
            repetitions=1,
            entanglement="linear",
        ),
        noise=QComputeNoiseSpec(model="none"),
        shots=256,
        hamiltonian_file=str(hamiltonian_file),
        hamiltonian_format="fcidump",
        fermion_mapping="jordan_wigner",
        active_space=(2, 2),
        reference_energy=-1.137,
        max_iterations=5,
    )
    probe = QComputeEnvironmentProbeComponent()
    environment = probe.probe(spec)
    if not environment.available:
        raise SystemExit(f"Backend unavailable: {environment.status}")
    compiler = QComputeConfigCompilerComponent()
    plan = compiler.build_plan_from_hamiltonian(spec, environment)
    executor = QComputeExecutorComponent()
    validator = QComputeValidatorComponent()
    await executor.activate(ComponentRuntime(storage_path=runtime_dir))
    await validator.activate(ComponentRuntime(storage_path=runtime_dir))
    try:
        artifact = executor.execute_plan(plan, environment)
        validation = validator.validate_run(artifact, plan, environment)
        optimization = plan.compilation_metadata.get("vqe_optimization", {})
        print(f"Run status: {artifact.status}")
        print(f"Validation: {validation.status.value}")
        print(f"Best parameters: {optimization.get('best_parameters')}")
        print(f"Computed energy: {plan.compilation_metadata.get('computed_energy')}")
        print(f"Reference energy: {spec.reference_energy}")
        print(f"Energy error: {validation.metrics.energy_error}")
        print(f"Raw output: {artifact.raw_output_path}")
        print(f"Hamiltonian file: {hamiltonian_file}")
    finally:
        await validator.deactivate()
        await executor.deactivate()


def main() -> None:
    asyncio.run(run_demo())


if __name__ == "__main__":
    main()
