import pytest

from metaharness_ext.jedi import (
    CANONICAL_CAPABILITIES,
    CAP_JEDI_CASE_COMPILE,
    CAP_JEDI_ENV_PROBE,
    CAP_JEDI_REAL_RUN,
    CAP_JEDI_SCHEMA,
    CAP_JEDI_STUDY,
    CAP_JEDI_VALIDATE,
    CAP_JEDI_VALIDATE_ONLY,
    JEDI_EXPERIMENT_SPEC_ADAPTER,
    JediEvidenceBundle,
    JediEvidencePolicy,
    JediEvidenceWarning,
    JediExecutableSpec,
    JediForecastSpec,
    JediGovernanceAdapter,
    JediHofXSpec,
    JediLocalEnsembleDASpec,
    JediMutationAxis,
    JediPolicyReport,
    JediRunArtifact,
    JediRunPlan,
    JediRunPreprocessor,
    JediStudyReport,
    JediStudySpec,
    JediValidationReport,
    JediVariationalSpec,
    build_jedi_config,
    render_jedi_yaml,
)


def test_metaharness_jedi_contracts_round_trip() -> None:
    variational = JediVariationalSpec(
        task_id="task-1",
        executable=JediExecutableSpec(binary_name="qg4DVar.x", execution_mode="validate_only"),
    )
    forecast = JediForecastSpec(
        task_id="task-2",
        executable=JediExecutableSpec(binary_name="qgForecast.x", execution_mode="schema"),
    )
    local_ensemble_da = JediLocalEnsembleDASpec(
        task_id="task-3",
        executable=JediExecutableSpec(binary_name="qgLETKF.x", execution_mode="validate_only"),
        ensemble_paths=["/tmp/ens.000"],
    )
    hofx = JediHofXSpec(
        task_id="task-4",
        executable=JediExecutableSpec(binary_name="qgHofX3D.x", execution_mode="validate_only"),
    )
    plan = JediRunPlan(
        task_id="task-1",
        run_id="run-1",
        application_family="variational",
        execution_mode="validate_only",
        working_directory="run-1",
        config_path="run-1/config.yaml",
        config_text="cost function: {}\n",
        executable=variational.executable,
    )
    artifact = JediRunArtifact(
        task_id="task-1",
        run_id="run-1",
        application_family="variational",
        execution_mode="validate_only",
        working_directory="run-1",
    )
    validation = JediValidationReport(
        task_id="task-1", run_id="run-1", passed=True, status="validated"
    )
    evidence_warning = JediEvidenceWarning(code="warning-1", message="warning")
    evidence_bundle = JediEvidenceBundle(
        task_id="task-1",
        run_id="run-1",
        application_family="variational",
        execution_mode="validate_only",
        run=artifact,
        validation=validation,
    )
    policy_report = JediPolicyReport(passed=True, decision="allow", reason="ok")
    study = JediStudySpec(
        study_id="study-1",
        task_id="task-1",
        base_task=variational,
        axis=JediMutationAxis(kind="variational_iterations", values=[10, 20]),
        metric_key="final_cost_function",
    )
    study_report = JediStudyReport(
        study_id="study-1",
        task_id="task-1",
        axis_kind="variational_iterations",
        metric_key="final_cost_function",
    )

    assert JEDI_EXPERIMENT_SPEC_ADAPTER.validate_python(variational.model_dump()) == variational
    assert JEDI_EXPERIMENT_SPEC_ADAPTER.validate_python(forecast.model_dump()) == forecast
    assert (
        JEDI_EXPERIMENT_SPEC_ADAPTER.validate_python(local_ensemble_da.model_dump())
        == local_ensemble_da
    )
    assert JEDI_EXPERIMENT_SPEC_ADAPTER.validate_python(hofx.model_dump()) == hofx
    assert JediRunPlan.model_validate(plan.model_dump()) == plan
    assert JediRunArtifact.model_validate(artifact.model_dump()) == artifact
    assert JediValidationReport.model_validate(validation.model_dump()) == validation
    assert JediEvidenceWarning.model_validate(evidence_warning.model_dump()) == evidence_warning
    assert JediEvidenceBundle.model_validate(evidence_bundle.model_dump()) == evidence_bundle
    assert JediPolicyReport.model_validate(policy_report.model_dump()) == policy_report
    assert JediEvidencePolicy is not None
    assert JediStudySpec.model_validate(study.model_dump()) == study
    assert JediStudyReport.model_validate(study_report.model_dump()) == study_report


def test_metaharness_jedi_exports_exist() -> None:
    assert CAP_JEDI_CASE_COMPILE in CANONICAL_CAPABILITIES
    assert CAP_JEDI_ENV_PROBE in CANONICAL_CAPABILITIES
    assert CAP_JEDI_SCHEMA in CANONICAL_CAPABILITIES
    assert CAP_JEDI_VALIDATE_ONLY in CANONICAL_CAPABILITIES
    assert CAP_JEDI_REAL_RUN in CANONICAL_CAPABILITIES
    assert CAP_JEDI_STUDY in CANONICAL_CAPABILITIES
    assert CAP_JEDI_VALIDATE in CANONICAL_CAPABILITIES
    assert callable(build_jedi_config)
    assert callable(render_jedi_yaml)
    assert JediGovernanceAdapter is not None
    assert JediRunPreprocessor is not None


def test_metaharness_jedi_rejects_invalid_cost_type() -> None:
    with pytest.raises(ValueError, match="cost_type"):
        JediVariationalSpec(
            task_id="task-bad",
            executable=JediExecutableSpec(binary_name="qg4DVar.x", execution_mode="validate_only"),
            cost_type="3DFGAT",
        )


def test_metaharness_jedi_rejects_ctest_style_binary_name() -> None:
    with pytest.raises(ValueError, match="CTest"):
        JediExecutableSpec(binary_name="qg_4dvar_rpcg.x", execution_mode="validate_only")


def test_metaharness_jedi_rejects_empty_ensemble_path_and_launcher_arg() -> None:
    with pytest.raises(ValueError, match="ensemble_paths"):
        JediLocalEnsembleDASpec(
            task_id="task-bad-ensemble",
            executable=JediExecutableSpec(binary_name="qgLETKF.x", execution_mode="validate_only"),
            ensemble_paths=[""],
        )

    with pytest.raises(ValueError, match="launcher_args"):
        JediExecutableSpec(
            binary_name="qg4DVar.x",
            execution_mode="validate_only",
            launcher_args=["", "--bind-to", "core"],
        )
