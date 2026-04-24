from __future__ import annotations

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.jedi.capabilities import CAP_JEDI_SMOKE_POLICY
from metaharness_ext.jedi.contracts import (
    JediEnvironmentReport,
    JediSmokePolicyReport,
)
from metaharness_ext.jedi.slots import JEDI_SMOKE_POLICY_SLOT

_SMOKE_READINESS_FIELDS = (
    "binary_available",
    "launcher_available",
    "shared_libraries_resolved",
    "required_paths_present",
    "workspace_testinput_present",
)

_SMOKE_PRIORITY = ("hofx", "variational", "local_ensemble_da", "forecast")


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
        ready, reason = self.evaluate_environment(report)
        if not ready:
            return JediSmokePolicyReport(
                ready=False,
                recommended_family=report.smoke_candidate,
                recommended_binary=None,
                reason=reason,
            )
        if report.smoke_candidate is None:
            return JediSmokePolicyReport(
                ready=True,
                recommended_family=None,
                recommended_binary=None,
                reason="Environment gated: no smoke family candidate declared.",
            )

        for family in self._family_priority(report):
            if self._family_ready(report, family):
                return JediSmokePolicyReport(
                    ready=True,
                    recommended_family=family,
                    recommended_binary=self._binary_for_family(family),
                    reason=f"Environment gated: {family} baseline selected.",
                )

        return JediSmokePolicyReport(
            ready=False,
            recommended_family=report.smoke_candidate,
            recommended_binary=None,
            reason="Environment not smoke-ready for any supported baseline.",
        )

    def evaluate_environment(self, report: JediEnvironmentReport) -> tuple[bool, str]:
        missing = [field for field in _SMOKE_READINESS_FIELDS if not getattr(report, field)]
        if not missing:
            return True, "Environment is smoke-ready."
        if report.messages:
            return False, "Environment not smoke-ready: " + "; ".join(report.messages)
        return False, "Environment not smoke-ready: missing " + ", ".join(missing)

    def _family_priority(self, report: JediEnvironmentReport) -> tuple[str, ...]:
        if report.smoke_candidate in _SMOKE_PRIORITY:
            candidate_index = _SMOKE_PRIORITY.index(report.smoke_candidate)
            return _SMOKE_PRIORITY[candidate_index:]
        return _SMOKE_PRIORITY

    def _family_ready(self, report: JediEnvironmentReport, family: str) -> bool:
        if family == "hofx":
            return report.data_paths_present
        if family == "variational":
            return report.data_prerequisites_ready
        if family == "local_ensemble_da":
            return report.data_prerequisites_ready and report.data_paths_present
        if family == "forecast":
            return report.data_paths_present
        return False

    def _binary_for_family(self, family: str | None) -> str | None:
        mapping = {
            "hofx": "qgHofX4D.x",
            "variational": "qg4DVar.x",
            "local_ensemble_da": "qgLETKF.x",
            "forecast": "qgForecast.x",
        }
        return mapping.get(family) if family else None
