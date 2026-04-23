from __future__ import annotations

from typing import Any, Literal

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.abacus.capabilities import CAP_ABACUS_CASE_COMPILE
from metaharness_ext.abacus.contracts import (
    AbacusExecutableSpec,
    AbacusExperimentSpec,
    AbacusKPointSpec,
    AbacusNscfSpec,
    AbacusRelaxSpec,
    AbacusScfSpec,
    AbacusStructureSpec,
)
from metaharness_ext.abacus.slots import ABACUS_GATEWAY_SLOT


class AbacusGatewayComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self, runtime: ComponentRuntime) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(ABACUS_GATEWAY_SLOT)
        api.declare_output("task", "AbacusExperimentSpec", mode="sync")
        api.provide_capability(CAP_ABACUS_CASE_COMPILE)

    def issue_task(
        self,
        *,
        task_id: str = "abacus-task-1",
        family: Literal["scf", "nscf", "relax"] = "scf",
        working_directory: str | None = None,
        structure_content: str = "",
        kpoints_content: str | None = None,
        basis_type: str = "pw",
        esolver_type: str = "ksdft",
        suffix: str = "ABACUS",
        charge_density_path: str | None = None,
        restart_file_path: str | None = None,
        relax_controls: dict[str, Any] | None = None,
    ) -> AbacusExperimentSpec:
        common_kwargs = {
            "task_id": task_id,
            "executable": AbacusExecutableSpec(),
            "structure": AbacusStructureSpec(content=structure_content),
            "kpoints": AbacusKPointSpec(content=kpoints_content) if kpoints_content else None,
            "basis_type": basis_type,
            "esolver_type": esolver_type,
            "suffix": suffix,
            "working_directory": working_directory,
        }
        if family == "nscf":
            return AbacusNscfSpec(
                **common_kwargs,
                charge_density_path=charge_density_path,
                restart_file_path=restart_file_path,
            )
        if family == "relax":
            return AbacusRelaxSpec(
                **common_kwargs,
                relax_controls=relax_controls or {},
            )
        return AbacusScfSpec(**common_kwargs)
