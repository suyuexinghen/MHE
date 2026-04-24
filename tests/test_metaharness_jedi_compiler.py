from metaharness_ext.jedi.config_compiler import JediConfigCompilerComponent
from metaharness_ext.jedi.contracts import (
    JediExecutableSpec,
    JediForecastSpec,
    JediHofXSpec,
    JediLocalEnsembleDASpec,
    JediVariationalSpec,
)


def test_jedi_compiler_builds_all_families() -> None:
    compiler = JediConfigCompilerComponent()
    specs = [
        JediVariationalSpec(
            task_id="var-1",
            executable=JediExecutableSpec(binary_name="qg4DVar.x", execution_mode="validate_only"),
        ),
        JediLocalEnsembleDASpec(
            task_id="ens-1",
            executable=JediExecutableSpec(binary_name="qgLETKF.x", execution_mode="validate_only"),
            ensemble_paths=["/tmp/ens.000"],
        ),
        JediHofXSpec(
            task_id="hofx-1",
            executable=JediExecutableSpec(binary_name="qgHofX3D.x", execution_mode="validate_only"),
        ),
        JediForecastSpec(
            task_id="forecast-1",
            executable=JediExecutableSpec(binary_name="qgForecast.x", execution_mode="schema"),
        ),
    ]

    plans = [compiler.build_plan(spec) for spec in specs]

    assert [plan.application_family for plan in plans] == [
        "variational",
        "local_ensemble_da",
        "hofx",
        "forecast",
    ]
    assert plans[0].config_text
    assert plans[3].schema_path is not None


def test_jedi_compiler_variational_yaml_is_stable() -> None:
    compiler = JediConfigCompilerComponent()
    spec = JediVariationalSpec(
        task_id="var-stable",
        executable=JediExecutableSpec(binary_name="qg4DVar.x", execution_mode="validate_only"),
        background_path="/tmp/background.nc",
        observation_paths=["/tmp/obs.ioda"],
    )

    plan_one = compiler.build_plan(spec)
    plan_two = compiler.build_plan(spec)

    assert plan_one.config_text == plan_two.config_text
    assert "cost function:" in plan_one.config_text
    assert '  cost type: "4D-Var"' in plan_one.config_text
    assert "variational:" in plan_one.config_text
    assert "  minimizer:" in plan_one.config_text
    assert "output:" in plan_one.config_text
    assert "final:" in plan_one.config_text
    assert "test:" in plan_one.config_text
    assert "3DFGAT" not in plan_one.config_text


def test_jedi_compiler_threads_orchestration_ids_into_plan() -> None:
    compiler = JediConfigCompilerComponent()
    spec = JediVariationalSpec(
        task_id="var-ids",
        executable=JediExecutableSpec(binary_name="qg4DVar.x", execution_mode="real_run"),
        candidate_id="candidate-42",
        graph_version_id=7,
        session_id="session-abc",
        audit_refs=["audit-record:123"],
    )

    plan = compiler.build_plan(spec)

    assert plan.candidate_id == "candidate-42"
    assert plan.graph_version_id == 7
    assert plan.session_id == "session-abc"
    assert plan.audit_refs == ["audit-record:123"]


def test_jedi_compiler_variational_real_run_declares_expected_evidence() -> None:
    compiler = JediConfigCompilerComponent()
    spec = JediVariationalSpec(
        task_id="var-real",
        executable=JediExecutableSpec(
            binary_name="qg4DVar.x",
            execution_mode="real_run",
            launcher="mpiexec",
            process_count=4,
        ),
        background_path="/tmp/background.nc",
        background_error_path="/tmp/background-error.nc",
        observation_paths=["/tmp/obs.ioda"],
        scientific_check="rms_improves",
        expected_diagnostics=["departures.json"],
    )

    plan = compiler.build_plan(spec)

    assert plan.expected_outputs == ["analysis.out"]
    assert plan.expected_diagnostics == ["departures.json"]
    assert plan.expected_references == ["reference.json"]
    assert plan.scientific_check == "rms_improves"
    assert "/tmp/background.nc" in plan.required_runtime_paths
    assert "/tmp/background-error.nc" in plan.required_runtime_paths
    assert "/tmp/obs.ioda" in plan.required_runtime_paths


def test_jedi_compiler_does_not_passthrough_arbitrary_yaml() -> None:
    compiler = JediConfigCompilerComponent()
    spec = JediVariationalSpec(
        task_id="var-no-pass",
        executable=JediExecutableSpec(binary_name="qg4DVar.x", execution_mode="validate_only"),
        variational={"solver": {"iterations": 10}},
    )

    plan = compiler.build_plan(spec)

    assert "!!python/object" not in plan.config_text
    assert "solver:" in plan.config_text
    assert "iterations: 10" in plan.config_text


def test_jedi_compiler_variational_real_run_defaults_departures_diagnostic() -> None:
    compiler = JediConfigCompilerComponent()
    spec = JediVariationalSpec(
        task_id="var-default-diagnostics",
        executable=JediExecutableSpec(binary_name="qg4DVar.x", execution_mode="real_run"),
    )

    plan = compiler.build_plan(spec)

    assert plan.expected_diagnostics == ["departures.json"]


def test_jedi_compiler_local_ensemble_real_run_declares_expected_evidence() -> None:
    compiler = JediConfigCompilerComponent()
    spec = JediLocalEnsembleDASpec(
        task_id="ens-real",
        executable=JediExecutableSpec(
            binary_name="qgLETKF.x",
            execution_mode="real_run",
            launcher="mpiexec",
            process_count=8,
        ),
        ensemble_paths=["/tmp/ens.000", "/tmp/ens.001"],
        background_path="/tmp/background.nc",
        observation_paths=["/tmp/obs.ioda"],
        scientific_check="ensemble_outputs_present",
        expected_diagnostics=["posterior.out", "observer.out"],
    )

    plan = compiler.build_plan(spec)

    assert plan.expected_outputs == ["letkf.out"]
    assert plan.expected_diagnostics == ["posterior.out", "observer.out"]
    assert plan.expected_references == ["ensemble_reference.json"]
    assert plan.scientific_check == "ensemble_outputs_present"
    assert "/tmp/ens.000" in plan.required_runtime_paths
    assert "/tmp/background.nc" in plan.required_runtime_paths
    assert "/tmp/obs.ioda" in plan.required_runtime_paths
    assert "driver:" in plan.config_text
    assert "local ensemble DA:" in plan.config_text


def test_jedi_compiler_local_ensemble_real_run_defaults_posterior_diagnostic() -> None:
    compiler = JediConfigCompilerComponent()
    spec = JediLocalEnsembleDASpec(
        task_id="ens-default-diagnostics",
        executable=JediExecutableSpec(binary_name="qgLETKF.x", execution_mode="real_run"),
        ensemble_paths=["/tmp/ens.000"],
    )

    plan = compiler.build_plan(spec)

    assert plan.expected_diagnostics == ["posterior.out"]
