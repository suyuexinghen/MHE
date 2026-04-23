from pathlib import Path

from metaharness_ext.deepmd.contracts import (
    DeepMDExecutableSpec,
    DPGenMachineSpec,
    DPGenRunSpec,
    DPGenSimplifySpec,
)
from metaharness_ext.deepmd.train_config_compiler import DeepMDTrainConfigCompilerComponent


def test_dpgen_compiler_builds_param_and_machine_json(tmp_path: Path) -> None:
    spec = DPGenRunSpec(
        task_id="dpgen-task",
        executable=DeepMDExecutableSpec(binary_name="dpgen", execution_mode="dpgen_run"),
        param={"type_map": ["H", "O"], "numb_models": 4},
        machine=DPGenMachineSpec(local_root=str(tmp_path), python_path="python3"),
        workspace_inline_files={"conf.lmp": "units metal\n"},
    )

    plan = DeepMDTrainConfigCompilerComponent().build_plan(spec)

    assert plan.execution_mode == "dpgen_run"
    assert plan.command == ["dpgen", "run"]
    assert plan.param_json["type_map"] == ["H", "O"]
    assert plan.param_json["numb_models"] == 4
    assert plan.machine_json["local_root"] == str(tmp_path)
    assert plan.machine_json["python_path"] == "python3"
    assert plan.param_json_path is not None and plan.param_json_path.endswith("param.json")
    assert plan.machine_json_path is not None and plan.machine_json_path.endswith("machine.json")


def test_dpgen_simplify_compiler_builds_param_and_machine_json(tmp_path: Path) -> None:
    spec = DPGenSimplifySpec(
        task_id="dpgen-simplify-task",
        executable=DeepMDExecutableSpec(binary_name="dpgen", execution_mode="dpgen_simplify"),
        param={"type_map": ["H", "O"], "numb_models": 4},
        machine=DPGenMachineSpec(local_root=str(tmp_path), python_path="python3"),
        training_init_model=["models/model.pb"],
        trainable_mask=[True, False],
        relabeling={"pick_number": 12, "freeze_level": 2},
    )

    plan = DeepMDTrainConfigCompilerComponent().build_plan(spec)

    assert plan.execution_mode == "dpgen_simplify"
    assert plan.command == ["dpgen", "simplify"]
    assert plan.param_json["training_init_model"] == ["models/model.pb"]
    assert plan.param_json["trainable_mask"] == [True, False]
    assert plan.param_json["simplify"]["pick_number"] == 12
    assert plan.param_json["simplify"]["freeze_level"] == 2
    assert plan.machine_json["local_root"] == str(tmp_path)
    assert plan.machine_json["python_path"] == "python3"
