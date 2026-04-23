from __future__ import annotations

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.jedi.capabilities import CAP_JEDI_SMOKE_POLICY
from metaharness_ext.jedi.contracts import JediEnvironmentReport, JediSmokePolicyReport
from metaharness_ext.jedi.slots import JEDI_SMOKE_POLICY_SLOT


class JediSmokePolicyComponent(HarnessComponent):
    """Environment-gated smoke baseline selection policy.

    Given an environment readiness report, recommends the lightest available
    toy baseline that can realistically run in the current workspace.
    """

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(JEDI_SMOKE_POLICY_SLOT)
        api.declare_input("environment", "JediEnvironmentReport")
        api.declare_output("policy", "JediSmokePolicyReport", mode="sync")
        api.provide_capability(CAP_JEDI_SMOKE_POLICY)

    def select_baseline(self, report: JediEnvironmentReport) -> "JediSmokePolicyReport":
        if not report.smoke_ready:
            return JediSmokePolicyReport(
                ready=False,
                recommended_family=report.smoke_candidate,
                recommended_binary=None,
                reason="Environment not smoke-ready: " + "; ".join(report.messages),
            )

        candidate = report.smoke_candidate
        binary = self._binary_for_family(candidate)

        return JediSmokePolicyReport(
            ready=True,
            recommended_family=candidate,
            recommended_binary=binary,
            reason=f"Environment gated: {candidate} baseline selected.",
        )

    def _binary_for_family(self, family: str | None) -> str | None:
        mapping = {
            "hofx": "qgHofX4D.x",
            "variational": "qg4DVar.x",
            "local_ensemble_da": "qgLETKF.x",
            "forecast": "qgForecast.x",
        }
        return mapping.get(family) if family else None
