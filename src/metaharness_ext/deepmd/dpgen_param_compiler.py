from __future__ import annotations

from copy import deepcopy
from typing import Any

from metaharness_ext.deepmd.contracts import DPGenRunSpec, DPGenSimplifySpec


def build_dpgen_param_json(spec: DPGenRunSpec | DPGenSimplifySpec) -> dict[str, Any]:
    payload = deepcopy(spec.param)
    payload.setdefault("type_map", payload.get("type_map", []))
    payload.setdefault("fp_style", payload.get("fp_style", "vasp"))
    if isinstance(spec, DPGenSimplifySpec):
        if spec.training_init_model:
            payload["training_init_model"] = list(spec.training_init_model)
        if spec.trainable_mask:
            payload["trainable_mask"] = list(spec.trainable_mask)
        if spec.relabeling:
            payload.setdefault("simplify", {})
            payload["simplify"].update(spec.relabeling)
    return payload
