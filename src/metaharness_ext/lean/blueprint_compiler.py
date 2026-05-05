from __future__ import annotations

from graphlib import CycleError, TopologicalSorter

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.lean.capabilities import CAP_LEAN_COMPILE_BLUEPRINT
from metaharness_ext.lean.contracts import LeanBlueprint, LeanBlueprintItem, LeanTaskSpec
from metaharness_ext.lean.slots import LEAN_BLUEPRINT_COMPILER_SLOT
from metaharness_ext.lean.types import LeanBlueprintItemStatus


class LeanBlueprintCompilerComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(LEAN_BLUEPRINT_COMPILER_SLOT)
        api.declare_input("task", "LeanTaskSpec")
        api.declare_output("blueprint", "LeanBlueprint", mode="sync")
        api.provide_capability(CAP_LEAN_COMPILE_BLUEPRINT)

    def compile(self, task: LeanTaskSpec) -> LeanBlueprint:
        raw_items = task.metadata.get("blueprint_items")
        if raw_items:
            items = [LeanBlueprintItem.model_validate(item) for item in raw_items]
        else:
            label = task.target_lemma or task.target_file
            items = [
                LeanBlueprintItem(
                    label=label,
                    lean_declaration=task.target_lemma or label,
                    file=task.target_file,
                    budget=task.budget,
                    informal_statement=task.metadata.get("informal_statement", ""),
                    informal_proof=task.metadata.get("informal_proof", ""),
                )
            ]
        return LeanBlueprint(items=order_blueprint_items(items), metadata=dict(task.metadata))

    def refine_at_checkpoint(self, item: LeanBlueprintItem) -> LeanBlueprintItem:
        if not should_refine(item.attempts):
            return item
        return item.model_copy(update={"status": LeanBlueprintItemStatus.PARTIAL})


def order_blueprint_items(items: list[LeanBlueprintItem]) -> list[LeanBlueprintItem]:
    by_label = {item.label: item for item in items}
    missing = sorted({dependency for item in items for dependency in item.uses} - set(by_label))
    if missing:
        raise ValueError(f"Unknown Lean blueprint dependencies: {', '.join(missing)}")
    sorter = TopologicalSorter({item.label: set(item.uses) for item in items})
    try:
        ordered_labels = tuple(sorter.static_order())
    except CycleError as exc:
        raise ValueError("Lean blueprint dependencies contain a cycle") from exc
    return [by_label[label] for label in ordered_labels]


def should_refine(attempts: int) -> bool:
    return attempts > 0 and attempts & (attempts - 1) == 0
