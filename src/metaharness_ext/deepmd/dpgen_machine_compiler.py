from __future__ import annotations

from typing import Any

from metaharness_ext.deepmd.contracts import DPGenRunSpec, DPGenSimplifySpec


def build_dpgen_machine_json(spec: DPGenRunSpec | DPGenSimplifySpec) -> dict[str, Any]:
    machine = spec.machine
    payload: dict[str, Any] = {
        "batch_type": machine.batch_type,
        "context_type": machine.context_type,
        "local_root": machine.local_root,
    }
    if machine.remote_root is not None:
        payload["remote_root"] = machine.remote_root
    if machine.python_path is not None:
        payload["python_path"] = machine.python_path
    if machine.command is not None:
        payload["command"] = machine.command
    payload.update(machine.extra)
    return payload
