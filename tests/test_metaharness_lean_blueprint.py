from __future__ import annotations

import pytest

from metaharness_ext.lean.blueprint_compiler import (
    LeanBlueprintCompilerComponent,
    order_blueprint_items,
    should_refine,
)
from metaharness_ext.lean.contracts import LeanBlueprintItem, LeanTaskSpec
from metaharness_ext.lean.types import LeanBlueprintItemStatus


def test_compile_single_item_from_task() -> None:
    task = LeanTaskSpec(target_file="Proofs/Main.lean", target_lemma="main", budget=4)

    blueprint = LeanBlueprintCompilerComponent().compile(task)

    assert blueprint.items[0].label == "main"
    assert blueprint.items[0].budget == 4


def test_order_blueprint_items_dependencies_first() -> None:
    main = LeanBlueprintItem(label="main", lean_declaration="main", file="Main.lean", uses=["base"])
    base = LeanBlueprintItem(label="base", lean_declaration="base", file="Main.lean")

    ordered = order_blueprint_items([main, base])

    assert [item.label for item in ordered] == ["base", "main"]


def test_order_blueprint_items_rejects_missing_dependency() -> None:
    item = LeanBlueprintItem(
        label="main", lean_declaration="main", file="Main.lean", uses=["missing"]
    )

    with pytest.raises(ValueError, match="Unknown Lean blueprint dependencies"):
        order_blueprint_items([item])


def test_order_blueprint_items_rejects_cycle() -> None:
    first = LeanBlueprintItem(label="a", lean_declaration="a", file="Main.lean", uses=["b"])
    second = LeanBlueprintItem(label="b", lean_declaration="b", file="Main.lean", uses=["a"])

    with pytest.raises(ValueError, match="cycle"):
        order_blueprint_items([first, second])


def test_refine_at_power_of_two_checkpoint() -> None:
    item = LeanBlueprintItem(label="main", lean_declaration="main", file="Main.lean", attempts=4)

    refined = LeanBlueprintCompilerComponent().refine_at_checkpoint(item)

    assert should_refine(4) is True
    assert should_refine(3) is False
    assert refined.status is LeanBlueprintItemStatus.PARTIAL
