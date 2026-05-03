from __future__ import annotations

from typing import Any

from metaharness_ext.boutpp.contracts import BoutPPProblemSpec


class BoutPPGatewayComponent:
    def issue_task(self, spec: BoutPPProblemSpec | dict[str, Any]) -> BoutPPProblemSpec:
        if isinstance(spec, BoutPPProblemSpec):
            return spec
        return BoutPPProblemSpec.model_validate(spec)
