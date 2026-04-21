from __future__ import annotations

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.ai4pde.contracts import PDEPlan, PDETaskRequest, ValidationBundle
from metaharness_ext.ai4pde.policies import (
    check_budget,
    check_reproducibility,
    classify_budget,
    classify_risk,
)
from metaharness_ext.ai4pde.slots import POLICY_GUARD_SLOT


class RiskPolicyComponent(HarnessComponent):
    protected = True

    def __init__(self) -> None:
        self.decisions: list[dict[str, object]] = []

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(POLICY_GUARD_SLOT)
        api.declare_event("risk_decision", "RiskDecision")

    def classify(
        self,
        request: PDETaskRequest,
        *,
        plan: PDEPlan | None = None,
        validation_bundle: ValidationBundle | None = None,
    ) -> dict[str, object]:
        budget_state = check_budget(request.budget)
        decision = {
            "risk_level": classify_risk(request, plan).value,
            "budget_level": classify_budget(request.budget),
            "budget_state": budget_state,
            "reproducibility": (
                check_reproducibility(validation_bundle) if validation_bundle is not None else None
            ),
        }
        self.decisions.append(decision)
        return decision
