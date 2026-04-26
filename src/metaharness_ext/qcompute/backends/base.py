"""Structural protocol for quantum backend adapters."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from metaharness_ext.qcompute.contracts import QComputeNoiseSpec


@runtime_checkable
class BackendAdapter(Protocol):
    """Common interface shared by all QCompute backend adapters."""

    def run(
        self,
        *,
        circuit: Any,
        shots: int,
        noise: QComputeNoiseSpec | None = None,
    ) -> dict[str, Any]: ...
