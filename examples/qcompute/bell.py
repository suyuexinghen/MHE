from __future__ import annotations

import asyncio
import os

from _shared import hardware_enabled, runtime_path

from metaharness.provenance import ArtifactSnapshotStore
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.qcompute import (
    QComputeBackendSpec,
    QComputeCircuitSpec,
    QComputeExperimentSpec,
    QComputeGatewayComponent,
)

BELL_STATE_OPENQASM = (
    'OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; creg c[2]; '
    "h q[0]; cx q[0],q[1]; measure q[0]->c[0]; measure q[1]->c[1];"
)


def build_backend() -> QComputeBackendSpec:
    if hardware_enabled() and os.getenv("Qcompute_Token"):
        return QComputeBackendSpec(
            platform="quafu",
            simulator=False,
            qubit_count=int(os.getenv("QCOMPUTE_QUAFU_QUBITS", "41")),
            chip_id=os.getenv("QCOMPUTE_QUAFU_CHIP", "Baihua"),
            api_token_env="Qcompute_Token",
            daily_quota=int(os.getenv("QCOMPUTE_QUAFU_DAILY_QUOTA", "10")),
        )
    return QComputeBackendSpec(platform="qiskit_aer", simulator=True, qubit_count=2)


async def run_demo() -> None:
    runtime_dir = runtime_path("bell")
    backend = build_backend()
    mode = "run" if backend.platform == "quafu" else "simulate"
    gateway = QComputeGatewayComponent()
    await gateway.activate(ComponentRuntime(storage_path=runtime_dir))
    try:
        spec = QComputeExperimentSpec(
            task_id="qcompute-bell-demo",
            mode=mode,
            backend=backend,
            circuit=QComputeCircuitSpec(
                ansatz="custom",
                num_qubits=2,
                openqasm=BELL_STATE_OPENQASM,
            ),
            shots=1024,
        )
        artifact_store = ArtifactSnapshotStore(path=runtime_dir / "artifact-snapshots.jsonl")
        result = gateway.run_baseline_full(spec, artifact_store=artifact_store)
        bundle = result.bundle
        if bundle is None:
            raise SystemExit("No evidence bundle returned.")
        print(f"Backend: {backend.platform}")
        print(f"Mode: {spec.mode}")
        print(f"Run status: {bundle.run_artifact.status}")
        print(f"Counts: {bundle.run_artifact.counts}")
        print(f"Validation: {bundle.validation_report.status.value}")
        print(f"Policy decision: {result.policy.decision if result.policy else 'unknown'}")
        print(f"Raw output: {bundle.run_artifact.raw_output_path}")
        print(f"Artifact snapshots: {artifact_store.path}")
    finally:
        await gateway.deactivate()


def main() -> None:
    asyncio.run(run_demo())


if __name__ == "__main__":
    main()
