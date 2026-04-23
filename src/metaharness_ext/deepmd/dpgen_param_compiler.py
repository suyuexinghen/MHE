from __future__ import annotations

from copy import deepcopy
from typing import Any

from metaharness_ext.deepmd.contracts import DPGenRunSpec


def build_dpgen_param_json(spec: DPGenRunSpec) -> dict[str, Any]:
    payload = deepcopy(spec.param)
    payload.setdefault("type_map", payload.get("type_map", []))
    payload.setdefault("fp_style", payload.get("fp_style", "vasp"))
    return payload
