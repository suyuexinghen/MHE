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
    assert "  cost type: \"4D-Var\"" in plan_one.config_text
    assert "3DFGAT" not in plan_one.config_text


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
