from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from metaharness.benchmark_drivers.io import write_json
from metaharness_ext.boutpp.compiler import BoutPPCompilerComponent
from metaharness_ext.boutpp.contracts import (
    BoutPPMpiSpec,
    BoutPPOptionValue,
    BoutPPOutputSpec,
    BoutPPProblemSpec,
    BoutPPValidationSpec,
)
from metaharness_ext.boutpp.executor import BoutPPExecutorComponent
from metaharness_ext.boutpp.postprocess import BoutPPPostprocessComponent
from metaharness_ext.boutpp.validator import BoutPPValidatorComponent


class BoutPPRealSmokeCase(BaseModel):
    case_id: str
    description: str
    executable_relpath: str
    source_case_relpath: str
    top_level_options: dict[str, BoutPPOptionValue] = Field(default_factory=dict)
    options: dict[str, dict[str, BoutPPOptionValue]] = Field(default_factory=dict)
    mpi_processes: int = 1
    output: BoutPPOutputSpec = Field(default_factory=BoutPPOutputSpec)
    validation: BoutPPValidationSpec = Field(default_factory=BoutPPValidationSpec)
    default_enabled: bool = True
    skip_reason: str | None = None


def boutpp_real_smoke_case_catalog() -> dict[str, BoutPPRealSmokeCase]:
    cases = [
        BoutPPRealSmokeCase(
            case_id="conduction-real",
            description="Compiled BOUT++ conduction example with retained logs/settings/dumps/restarts",
            executable_relpath="examples/conduction/conduction",
            source_case_relpath="examples/conduction",
            top_level_options={"MXG": 0},
            options={
                "mesh": {
                    "nx": 1,
                    "ny": 100,
                    "nz": 1,
                    "dy": 0.2,
                    "symmetricGlobalY": True,
                    "ixseps1": -1,
                    "ixseps2": -1,
                },
                "conduction": {"chi": 1.0},
                "T": {
                    "scale": 1.0,
                    "function": "gauss(y-pi, 0.2)",
                    "bndry_all": "dirichlet_o4(0.0)",
                },
                "solver": {"output_step": 0.1, "nout": 100},
            },
            mpi_processes=2,
            output=BoutPPOutputSpec(
                data_dir="data",
                require_settings=True,
                require_logs=True,
                require_dumps=True,
                require_restarts=True,
            ),
            validation=BoutPPValidationSpec(
                required_variables=[],
                metric_thresholds={},
                require_successful_return_code=True,
            ),
        ),
        BoutPPRealSmokeCase(
            case_id="boutpp-python-runexample",
            description="Python boutpp module example retained as a capability-gated candidate",
            executable_relpath="examples/boutpp/runexample",
            source_case_relpath="examples/boutpp",
            default_enabled=False,
            skip_reason="Python boutpp module support is optional and disabled in the documented local build.",
        ),
        BoutPPRealSmokeCase(
            case_id="staggered-grid-wrapper",
            description="Staggered-grid wrapper example retained as a capability-gated candidate",
            executable_relpath="examples/staggered_grid/run",
            source_case_relpath="examples/staggered_grid",
            default_enabled=False,
            skip_reason="Wrapper example does not expose a stable compiled BOUT++ binary in the local build.",
        ),
    ]
    return {case.case_id: case for case in cases}


def get_boutpp_real_smoke_cases(case_ids: list[str] | None = None) -> list[BoutPPRealSmokeCase]:
    catalog = boutpp_real_smoke_case_catalog()
    if case_ids is None:
        return list(catalog.values())
    return [catalog[case_id] for case_id in case_ids]


def preferred_mpi_launcher() -> str | None:
    for launcher in ("mpirun", "mpiexec"):
        if shutil.which(launcher):
            return launcher
    return None


def preflight_boutpp_real_smoke_case(
    case: BoutPPRealSmokeCase,
    build_root: Path,
    launcher: str | None = None,
) -> dict[str, Any]:
    executable = build_root / case.executable_relpath
    source_case_dir = build_root / case.source_case_relpath
    source_input = source_case_dir / case.output.data_dir / "BOUT.inp"
    launcher_available = launcher is not None and shutil.which(launcher) is not None
    missing = []
    if not build_root.exists():
        missing.append("build_root")
    if not executable.exists():
        missing.append("executable")
    if executable.exists() and not executable.stat().st_mode & 0o111:
        missing.append("executable_not_executable")
    if not source_case_dir.exists():
        missing.append("source_case_dir")
    if not source_input.exists():
        missing.append("source_BOUT_inp")
    if case.default_enabled and not launcher_available:
        missing.append("mpi_launcher")
    promotion_ready = case.default_enabled and not missing
    skip_reason = None
    if case.skip_reason:
        skip_reason = case.skip_reason
    elif missing:
        skip_reason = f"Missing prerequisites: {', '.join(missing)}"
    return {
        "case_id": case.case_id,
        "description": case.description,
        "build_root": str(build_root),
        "executable": str(executable),
        "source_case_dir": str(source_case_dir),
        "source_input": str(source_input),
        "default_enabled": case.default_enabled,
        "missing_prerequisites": missing,
        "promotion_ready": promotion_ready,
        "skip_reason": skip_reason,
    }


def build_boutpp_real_smoke_spec(
    case: BoutPPRealSmokeCase,
    build_root: Path,
    launcher: str,
) -> BoutPPProblemSpec:
    return BoutPPProblemSpec(
        task_id=case.case_id,
        case_name=case.case_id,
        executable=str((build_root / case.executable_relpath).resolve()),
        source_case_dir=str((build_root / case.source_case_relpath).resolve()),
        top_level_options=case.top_level_options,
        options=case.options,
        mpi=BoutPPMpiSpec(launcher_mode="mpi", launcher=launcher, processes=case.mpi_processes),
        output=case.output,
        validation=case.validation,
        timeout_seconds=300,
    )


def run_repeated_boutpp_real_smoke(
    *,
    build_root: Path,
    runs_root: Path,
    case_ids: list[str] | None = None,
    repeat_count: int = 2,
    launcher: str | None = None,
) -> dict[str, Any]:
    build_root = build_root.resolve()
    runs_root = runs_root.resolve()
    resolved_launcher = launcher or preferred_mpi_launcher()
    compiler = BoutPPCompilerComponent()
    postprocessor = BoutPPPostprocessComponent()
    validator = BoutPPValidatorComponent()
    case_summaries = []
    preflight_records = []
    for case in get_boutpp_real_smoke_cases(case_ids):
        preflight = preflight_boutpp_real_smoke_case(case, build_root, resolved_launcher)
        preflight_records.append(preflight)
        case_root = runs_root / case.case_id
        preflight_path = write_json(case_root / "preflight.json", preflight)
        if not preflight["promotion_ready"]:
            case_summaries.append(
                {
                    "case_id": case.case_id,
                    "status": "skipped",
                    "repeat_count": 0,
                    "passed_count": 0,
                    "skip_reason": preflight["skip_reason"],
                    "evidence_files": [str(preflight_path)],
                }
            )
            continue
        assert resolved_launcher is not None
        spec = build_boutpp_real_smoke_spec(case, build_root, resolved_launcher)
        repeat_summaries = []
        evidence_files = [str(preflight_path)]
        for repeat_index in range(1, max(1, repeat_count) + 1):
            run_id = f"{case.case_id}-repeat-{repeat_index:02d}"
            plan = compiler.compile(
                spec,
                run_id=run_id,
                workspace_dir=str(case_root / run_id),
            )
            artifact = BoutPPExecutorComponent(workspace_root=str(case_root)).execute(plan)
            postprocess = postprocessor.postprocess(artifact)
            validation = validator.validate(
                artifact,
                plan_ref=plan.plan_id,
                postprocess=postprocess,
                validation_spec=spec.validation,
            )
            output_dir = case_root / run_id
            files = [
                write_json(output_dir / "boutpp_problem_spec.json", spec),
                write_json(output_dir / "boutpp_run_plan.json", plan),
                write_json(output_dir / "boutpp_run_artifact.json", artifact),
                write_json(output_dir / "boutpp_postprocess_report.json", postprocess),
                write_json(output_dir / "boutpp_validation_report.json", validation),
            ]
            evidence_files.extend(str(path) for path in files)
            repeat_summaries.append(
                {
                    "repeat_index": repeat_index,
                    "run_id": run_id,
                    "artifact_status": artifact.status,
                    "return_code": artifact.return_code,
                    "validation_status": validation.status,
                    "validation_passed": validation.passed,
                    "evidence_ref_count": len(artifact.evidence_refs),
                    "missing_artifacts": artifact.missing_artifacts,
                    "summary_metrics": validation.summary_metrics,
                }
            )
        passed_count = sum(1 for item in repeat_summaries if item["validation_passed"])
        case_summaries.append(
            {
                "case_id": case.case_id,
                "status": "passed" if passed_count == len(repeat_summaries) else "failed",
                "repeat_count": len(repeat_summaries),
                "passed_count": passed_count,
                "repeats": repeat_summaries,
                "evidence_files": evidence_files,
            }
        )
    summary = {
        "suite": "boutpp-real-smoke",
        "real_tools": True,
        "real_claude": False,
        "repeat_count": max(1, repeat_count),
        "build_root": str(build_root),
        "mpi_launcher": resolved_launcher,
        "case_summaries": case_summaries,
        "preflight_records": preflight_records,
        "claim_boundary": "Local opt-in BOUT++ smoke only; no numerical superiority, convergence, runtime superiority, or broad solver-family support claim.",
    }
    write_json(runs_root / "boutpp_real_repeated_smoke_summary.json", summary)
    return summary


__all__ = [
    "BoutPPRealSmokeCase",
    "boutpp_real_smoke_case_catalog",
    "build_boutpp_real_smoke_spec",
    "get_boutpp_real_smoke_cases",
    "preferred_mpi_launcher",
    "preflight_boutpp_real_smoke_case",
    "run_repeated_boutpp_real_smoke",
]
