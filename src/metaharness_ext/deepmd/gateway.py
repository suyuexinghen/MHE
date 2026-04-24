from __future__ import annotations

from metaharness.core.boot import HarnessRuntime
from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.deepmd.capabilities import CAP_DEEPMD_CASE_COMPILE
from metaharness_ext.deepmd.contracts import (
    DeepMDBaselineReport,
    DeepMDDatasetSpec,
    DeepMDDescriptorSpec,
    DeepMDExecutableSpec,
    DeepMDExperimentSpec,
    DeepMDFittingNetSpec,
    DeepMDTrainSpec,
    DPGenAutotestSpec,
    DPGenMachineSpec,
    DPGenRunSpec,
    DPGenSimplifySpec,
)
from metaharness_ext.deepmd.environment import DeepMDEnvironmentProbeComponent
from metaharness_ext.deepmd.evidence import build_evidence_bundle
from metaharness_ext.deepmd.executor import DeepMDExecutorComponent
from metaharness_ext.deepmd.governance import DeepMDGovernanceAdapter
from metaharness_ext.deepmd.policy import DeepMDEvidencePolicy
from metaharness_ext.deepmd.runtime_handoff import handoff_governed_candidate
from metaharness_ext.deepmd.slots import DEEPMD_GATEWAY_SLOT
from metaharness_ext.deepmd.train_config_compiler import DeepMDTrainConfigCompilerComponent
from metaharness_ext.deepmd.validator import DeepMDValidatorComponent


class DeepMDGatewayComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(DEEPMD_GATEWAY_SLOT)
        api.declare_output("task", "DeepMDExperimentSpec", mode="sync")
        api.provide_capability(CAP_DEEPMD_CASE_COMPILE)

    def issue_task(
        self,
        *,
        train_systems: list[str],
        type_map: list[str],
        task_id: str = "deepmd-task-1",
        working_directory: str | None = None,
    ) -> DeepMDTrainSpec:
        return DeepMDTrainSpec(
            task_id=task_id,
            executable=DeepMDExecutableSpec(execution_mode="train"),
            dataset=DeepMDDatasetSpec(
                dataset_id=task_id,
                train_systems=train_systems,
                validation_systems=[],
                type_map=type_map,
                labels_present=["energy", "force"],
            ),
            type_map=type_map,
            descriptor=DeepMDDescriptorSpec(
                descriptor_type="se_e2_a",
                rcut=6.0,
                rcut_smth=5.5,
                sel=[32],
                neuron=[25, 50, 100],
            ),
            fitting_net=DeepMDFittingNetSpec(neuron=[240, 240, 240]),
            training={"numb_steps": 1000, "save_freq": 100, "disp_freq": 100},
            learning_rate={"type": "exp", "start_lr": 0.001, "decay_steps": 1000},
            loss={"type": "ener", "start_pref_e": 0.02, "start_pref_f": 1000.0},
            working_directory=working_directory,
        )

    def issue_dpgen_run_task(
        self,
        *,
        param: dict,
        machine: DPGenMachineSpec | None = None,
        task_id: str = "dpgen-run-task-1",
        working_directory: str | None = None,
        workspace_files: list[str] | None = None,
        workspace_inline_files: dict[str, str] | None = None,
    ) -> DPGenRunSpec:
        return DPGenRunSpec(
            task_id=task_id,
            param=param,
            machine=machine or DPGenMachineSpec(),
            working_directory=working_directory,
            workspace_files=list(workspace_files or []),
            workspace_inline_files=dict(workspace_inline_files or {}),
        )

    def issue_dpgen_simplify_task(
        self,
        *,
        param: dict,
        machine: DPGenMachineSpec | None = None,
        training_init_model: list[str] | None = None,
        trainable_mask: list[bool] | None = None,
        relabeling: dict | None = None,
        task_id: str = "dpgen-simplify-task-1",
        working_directory: str | None = None,
        workspace_files: list[str] | None = None,
        workspace_inline_files: dict[str, str] | None = None,
    ) -> DPGenSimplifySpec:
        return DPGenSimplifySpec(
            task_id=task_id,
            param=param,
            machine=machine or DPGenMachineSpec(),
            training_init_model=list(training_init_model or []),
            trainable_mask=list(trainable_mask or []),
            relabeling=dict(relabeling or {}),
            working_directory=working_directory,
            workspace_files=list(workspace_files or []),
            workspace_inline_files=dict(workspace_inline_files or {}),
        )

    def issue_dpgen_autotest_task(
        self,
        *,
        param: dict,
        machine: DPGenMachineSpec | None = None,
        properties: list[str] | None = None,
        task_id: str = "dpgen-autotest-task-1",
        working_directory: str | None = None,
        workspace_files: list[str] | None = None,
        workspace_inline_files: dict[str, str] | None = None,
    ) -> DPGenAutotestSpec:
        return DPGenAutotestSpec(
            task_id=task_id,
            param=param,
            machine=machine or DPGenMachineSpec(),
            properties=list(properties or []),
            working_directory=working_directory,
            workspace_files=list(workspace_files or []),
            workspace_inline_files=dict(workspace_inline_files or {}),
        )

    def run_baseline(
        self,
        task: DeepMDExperimentSpec,
        *,
        environment: DeepMDEnvironmentProbeComponent,
        compiler: DeepMDTrainConfigCompilerComponent,
        executor: DeepMDExecutorComponent,
        validator: DeepMDValidatorComponent,
        runtime: HarnessRuntime | None = None,
    ) -> DeepMDBaselineReport:
        environment_report = environment.probe(task)
        plan = compiler.build_plan(task)
        run = executor.execute_plan(plan)
        validation = validator.validate_run(run)
        evidence_bundle = build_evidence_bundle(run, validation, environment_report)
        policy_report = DeepMDEvidencePolicy().evaluate(evidence_bundle)
        governance = DeepMDGovernanceAdapter()
        core_validation_report = governance.build_core_validation_report(validation, policy_report)
        candidate_record = governance.build_candidate_record(evidence_bundle, policy_report)
        candidate_record = handoff_governed_candidate(
            runtime,
            candidate_record,
            bundle=evidence_bundle,
            policy=policy_report,
        )
        return DeepMDBaselineReport(
            task=task,
            environment=environment_report,
            plan=plan,
            run=run,
            validation=validation,
            evidence_bundle=evidence_bundle,
            policy_report=policy_report,
            core_validation_report=core_validation_report,
            candidate_record=candidate_record,
        )

