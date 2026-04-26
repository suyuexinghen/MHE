from __future__ import annotations

import asyncio
import json

from _shared import runtime_path

from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.qcompute import (
    QComputeBackendSpec,
    QComputeCircuitSpec,
    QComputeExperimentSpec,
    QComputeGatewayComponent,
    QComputeNoiseSpec,
)

BELL_STATE_OPENQASM = (
    'OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; '
    "h q[0]; cx q[0],q[1];"
)


async def run_demo() -> None:
    runtime_dir = runtime_path("noise-mitigation")
    gateway = QComputeGatewayComponent()
    await gateway.activate(ComponentRuntime(storage_path=runtime_dir))
    try:
        spec = QComputeExperimentSpec(
            task_id="qcompute-noise-mitigation-demo",
            mode="simulate",
            backend=QComputeBackendSpec(platform="qiskit_aer", simulator=True, qubit_count=2),
            circuit=QComputeCircuitSpec(
                ansatz="custom",
                num_qubits=2,
                openqasm=BELL_STATE_OPENQASM,
            ),
            noise=QComputeNoiseSpec(
                model="depolarizing",
                depolarizing_prob=0.01,
                readout_error=0.02,
            ),
            shots=1024,
            error_mitigation=["zne", "rem"],
        )
        bundle = gateway.run_baseline(spec)
        if bundle.run_artifact.status != "completed":
            raise SystemExit(f"Run failed with status {bundle.run_artifact.status}")
        mitigation = bundle.run_artifact.execution_policy.details.get("error_mitigation", {})
        print(f"Backend: {spec.backend.platform}")
        print(f"Run status: {bundle.run_artifact.status}")
        print(f"Counts: {bundle.run_artifact.counts}")
        print(f"Validation: {bundle.validation_report.status.value}")
        print("Mitigation details:")
        print(json.dumps(mitigation, indent=2, sort_keys=True))
        print(f"Raw output: {bundle.run_artifact.raw_output_path}")
    finally:
        await gateway.deactivate()


def main() -> None:
    asyncio.run(run_demo())


if __name__ == "__main__":
    main()
