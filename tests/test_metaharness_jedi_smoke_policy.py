from __future__ import annotations

from metaharness_ext.jedi.contracts import JediEnvironmentReport
from metaharness_ext.jedi.smoke_policy import JediSmokePolicyComponent


class TestJediSmokePolicyComponent:
    def test_selects_hofx_when_environment_ready(self) -> None:
        env = JediEnvironmentReport(
            binary_available=True,
            launcher_available=True,
            shared_libraries_resolved=True,
            required_paths_present=True,
            workspace_testinput_present=True,
            data_paths_present=True,
            data_prerequisites_ready=True,
            smoke_candidate="hofx",
            smoke_ready=True,
        )
        policy = JediSmokePolicyComponent().select_baseline(env)

        assert policy.ready is True
        assert policy.recommended_family == "hofx"
        assert policy.recommended_binary == "qgHofX4D.x"
        assert "hofx baseline selected" in policy.reason

    def test_selects_variational_when_hofx_not_ready(self) -> None:
        env = JediEnvironmentReport(
            binary_available=True,
            launcher_available=True,
            shared_libraries_resolved=True,
            required_paths_present=True,
            workspace_testinput_present=True,
            data_paths_present=True,
            data_prerequisites_ready=True,
            smoke_candidate="variational",
            smoke_ready=True,
        )
        policy = JediSmokePolicyComponent().select_baseline(env)

        assert policy.ready is True
        assert policy.recommended_family == "variational"
        assert policy.recommended_binary == "qg4DVar.x"

    def test_falls_back_from_hofx_to_variational_without_observation_data_readiness(self) -> None:
        env = JediEnvironmentReport(
            binary_available=True,
            launcher_available=True,
            shared_libraries_resolved=True,
            required_paths_present=True,
            workspace_testinput_present=True,
            data_paths_present=False,
            data_prerequisites_ready=True,
            smoke_candidate="hofx",
            smoke_ready=True,
        )

        policy = JediSmokePolicyComponent().select_baseline(env)

        assert policy.ready is True
        assert policy.recommended_family == "variational"
        assert policy.recommended_binary == "qg4DVar.x"

    def test_falls_back_from_variational_to_forecast_when_qg_data_prerequisites_missing(self) -> None:
        env = JediEnvironmentReport(
            binary_available=True,
            launcher_available=True,
            shared_libraries_resolved=True,
            required_paths_present=True,
            workspace_testinput_present=True,
            data_paths_present=True,
            data_prerequisites_ready=False,
            smoke_candidate="variational",
            smoke_ready=True,
        )

        policy = JediSmokePolicyComponent().select_baseline(env)

        assert policy.ready is True
        assert policy.recommended_family == "forecast"
        assert policy.recommended_binary == "qgForecast.x"

    def test_falls_back_from_local_ensemble_da_to_forecast_when_data_prerequisites_missing(self) -> None:
        env = JediEnvironmentReport(
            binary_available=True,
            launcher_available=True,
            shared_libraries_resolved=True,
            required_paths_present=True,
            workspace_testinput_present=True,
            data_paths_present=True,
            data_prerequisites_ready=False,
            smoke_candidate="local_ensemble_da",
            smoke_ready=True,
        )

        policy = JediSmokePolicyComponent().select_baseline(env)

        assert policy.ready is True
        assert policy.recommended_family == "forecast"
        assert policy.recommended_binary == "qgForecast.x"

    def test_blocks_when_environment_not_ready(self) -> None:
        env = JediEnvironmentReport(
            binary_available=False,
            launcher_available=True,
            shared_libraries_resolved=True,
            required_paths_present=True,
            workspace_testinput_present=True,
            data_paths_present=True,
            data_prerequisites_ready=True,
            smoke_candidate="variational",
            smoke_ready=False,
            messages=["JEDI binary not found: qg4DVar.x"],
        )
        policy = JediSmokePolicyComponent().select_baseline(env)

        assert policy.ready is False
        assert policy.recommended_family == "variational"
        assert policy.recommended_binary is None
        assert "Environment not smoke-ready" in policy.reason

    def test_evaluate_environment_reports_missing_common_readiness_fields_without_messages(
        self,
    ) -> None:
        env = JediEnvironmentReport(
            binary_available=True,
            launcher_available=True,
            shared_libraries_resolved=False,
            required_paths_present=True,
            workspace_testinput_present=True,
            data_paths_present=True,
            data_prerequisites_ready=False,
            smoke_candidate="variational",
            smoke_ready=False,
        )

        ready, reason = JediSmokePolicyComponent().evaluate_environment(env)

        assert ready is False
        assert "shared_libraries_resolved" in reason
        assert "data_prerequisites_ready" not in reason

    def test_maps_local_ensemble_da_to_letkf_binary(self) -> None:
        env = JediEnvironmentReport(
            binary_available=True,
            launcher_available=True,
            shared_libraries_resolved=True,
            required_paths_present=True,
            workspace_testinput_present=True,
            data_paths_present=True,
            data_prerequisites_ready=True,
            smoke_candidate="local_ensemble_da",
            smoke_ready=True,
        )
        policy = JediSmokePolicyComponent().select_baseline(env)

        assert policy.ready is True
        assert policy.recommended_binary == "qgLETKF.x"

    def test_maps_forecast_to_forecast_binary(self) -> None:
        env = JediEnvironmentReport(
            binary_available=True,
            launcher_available=True,
            shared_libraries_resolved=True,
            required_paths_present=True,
            workspace_testinput_present=True,
            data_paths_present=True,
            data_prerequisites_ready=True,
            smoke_candidate="forecast",
            smoke_ready=True,
        )
        policy = JediSmokePolicyComponent().select_baseline(env)

        assert policy.ready is True
        assert policy.recommended_binary == "qgForecast.x"

    def test_handles_none_smoke_candidate(self) -> None:
        env = JediEnvironmentReport(
            binary_available=True,
            launcher_available=True,
            shared_libraries_resolved=True,
            required_paths_present=True,
            workspace_testinput_present=True,
            data_paths_present=True,
            data_prerequisites_ready=True,
            smoke_candidate=None,
            smoke_ready=True,
        )
        policy = JediSmokePolicyComponent().select_baseline(env)

        assert policy.ready is True
        assert policy.recommended_family is None
        assert policy.recommended_binary is None
