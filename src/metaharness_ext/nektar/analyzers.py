from __future__ import annotations

import re
from pathlib import Path

from metaharness_ext.nektar.contracts import ErrorSummary, FilterOutputAnalysis, SolverLogAnalysis

_FLOAT_PATTERN = r"[0-9]*\.?[0-9]+(?:[eE][+-]?[0-9]+)?"
_COORDINATE_VARIABLES = frozenset({"x", "y", "z"})
_ERROR_NORM_LINE_PATTERN = re.compile(
    rf"L\s*(2|inf)\s+error\s+\(variable\s+(\w+)\)\s*:\s*({_FLOAT_PATTERN})"
)
_STEP_PATTERN = re.compile(
    rf"Steps:\s+(\d+)\s+Time:\s+({_FLOAT_PATTERN})\s+CPU Time:\s+({_FLOAT_PATTERN})s"
)
_WALL_TIME_PATTERN = re.compile(rf"Total Computation Time\s*=\s*({_FLOAT_PATTERN})s")
_PRESSURE_PATTERN = re.compile(
    rf"Pressure system \(mapping\) converged in (\d+) iterations with error = ({_FLOAT_PATTERN})"
)
_VELOCITY_PATTERN = re.compile(
    rf"Velocity system \(mapping\) converged in (\d+) iterations with error = ({_FLOAT_PATTERN})"
)
_NEWTON_PATTERN = re.compile(r"We have done (\d+) iteration\(s\)")
_L2NORM_PATTERN = re.compile(rf"L2Norm\[(\d+)\]\s*=\s*({_FLOAT_PATTERN})")
_INFNORM_PATTERN = re.compile(rf"InfNorm\[(\d+)\]\s*=\s*({_FLOAT_PATTERN})")


def parse_solver_log(log_path: str | Path) -> SolverLogAnalysis:
    path = Path(log_path)
    if not path.exists():
        return SolverLogAnalysis(path=str(path), exists=False)

    text = path.read_text()
    warnings, errors, has_timeout_marker = _extract_log_messages(text)
    l2_keys, linf_keys = _extract_error_keys(text)
    total_steps, final_time, cpu_time = _extract_step_metrics(text)
    wall_time = _extract_wall_time(text)
    incns_metrics = _extract_incns_metrics(text)
    return SolverLogAnalysis(
        path=str(path),
        exists=True,
        warning_count=len(warnings),
        error_count=len(errors),
        warnings=warnings,
        errors=errors,
        total_steps=total_steps,
        final_time=final_time,
        cpu_time=cpu_time,
        wall_time=wall_time,
        l2_error_keys=l2_keys,
        linf_error_keys=linf_keys,
        has_timeout_marker=has_timeout_marker,
        incns_metrics=incns_metrics,
    )


def parse_filter_outputs(paths: list[str] | None = None) -> FilterOutputAnalysis:
    files = [str(path) for path in paths or []]
    existing_files: list[str] = []
    missing_files: list[str] = []
    formats: dict[str, str] = {}
    file_sizes: dict[str, int] = {}
    nonempty_count = 0

    for raw_path in files:
        path = Path(raw_path)
        formats[raw_path] = _detect_output_format(path)
        if not path.exists():
            missing_files.append(raw_path)
            continue
        existing_files.append(raw_path)
        size = path.stat().st_size
        file_sizes[raw_path] = size
        if size > 0:
            nonempty_count += 1

    return FilterOutputAnalysis(
        files=files,
        existing_files=existing_files,
        missing_files=missing_files,
        formats=formats,
        file_sizes=file_sizes,
        has_vtu=any(fmt in {"vtu", "pvtu"} for fmt in formats.values()),
        has_dat=any(fmt == "dat" for fmt in formats.values()),
        has_fld=any(fmt == "fld" for fmt in formats.values()),
        nonempty_count=nonempty_count,
    )


def summarize_reference_error(metrics: dict[str, float | str] | None = None) -> ErrorSummary:
    raw_metrics = dict(metrics or {})
    l2_pairs = _collect_error_pairs(raw_metrics, prefix="l2_error_")
    linf_pairs = _collect_error_pairs(raw_metrics, prefix="linf_error_")
    if not l2_pairs and not linf_pairs:
        return ErrorSummary(messages=["No reference error metrics were found."])

    l2_keys = [key for key, _ in l2_pairs]
    linf_keys = [key for key, _ in linf_pairs]
    max_l2 = max((value for _, value in l2_pairs), default=None)
    max_linf = max((value for _, value in linf_pairs), default=None)
    primary_variable = None
    primary_l2 = None
    if l2_pairs:
        primary_key, primary_l2 = max(l2_pairs, key=lambda item: item[1])
        primary_variable = primary_key.removeprefix("l2_error_")

    tolerance = _coerce_float(raw_metrics.get("error_tolerance"))
    status = "reference_error_present"
    messages: list[str] = []
    if primary_variable is not None and primary_l2 is not None:
        messages.append(
            f"Primary reference error variable is {primary_variable} with L2 error {primary_l2:.6g}."
        )
    if max_linf is not None:
        messages.append(f"Maximum Linf reference error is {max_linf:.6g}.")
    if tolerance is None:
        messages.append("No error tolerance was provided, so no pass/fail judgement was made.")
    elif max_l2 is not None and max_l2 <= tolerance:
        status = "reference_error_within_tolerance"
        messages.append(f"Maximum L2 reference error {max_l2:.6g} is within tolerance {tolerance:.6g}.")
    elif max_l2 is not None:
        status = "reference_error_exceeds_tolerance"
        messages.append(f"Maximum L2 reference error {max_l2:.6g} exceeds tolerance {tolerance:.6g}.")

    return ErrorSummary(
        l2_keys=l2_keys,
        linf_keys=linf_keys,
        max_l2=max_l2,
        max_linf=max_linf,
        primary_variable=primary_variable,
        primary_l2=primary_l2,
        status=status,
        messages=messages,
    )


def _extract_log_messages(text: str) -> tuple[list[str], list[str], bool]:
    warnings: list[str] = []
    errors: list[str] = []
    has_timeout_marker = False
    for line in text.splitlines():
        lowered = line.lower()
        if "timed out" in lowered:
            has_timeout_marker = True
        if "warning" in lowered:
            warnings.append(line.strip())
        if "error" not in lowered:
            continue
        if _ERROR_NORM_LINE_PATTERN.search(line):
            continue
        errors.append(line.strip())
    return warnings, errors, has_timeout_marker


def _extract_error_keys(text: str) -> tuple[list[str], list[str]]:
    l2_keys: list[str] = []
    linf_keys: list[str] = []
    for match in _ERROR_NORM_LINE_PATTERN.finditer(text):
        norm_type = "l2" if match.group(1) == "2" else "linf"
        variable = match.group(2).lower()
        if variable in _COORDINATE_VARIABLES:
            continue
        key = f"{norm_type}_error_{variable}"
        target = l2_keys if norm_type == "l2" else linf_keys
        if key not in target:
            target.append(key)
    return l2_keys, linf_keys


def _extract_step_metrics(text: str) -> tuple[int | None, float | None, float | None]:
    matches = list(_STEP_PATTERN.finditer(text))
    if not matches:
        return None, None, None
    last = matches[-1]
    return int(last.group(1)), float(last.group(2)), float(last.group(3))


def _extract_wall_time(text: str) -> float | None:
    match = _WALL_TIME_PATTERN.search(text)
    if match is None:
        return None
    return float(match.group(1))


def _extract_incns_metrics(text: str) -> dict[str, float]:
    metrics: dict[str, float] = {}

    pressure_match = None
    for match in _PRESSURE_PATTERN.finditer(text):
        pressure_match = match
    if pressure_match is not None:
        metrics["incns_pressure_iterations"] = float(pressure_match.group(1))
        metrics["incns_pressure_error"] = float(pressure_match.group(2))

    velocity_match = None
    for match in _VELOCITY_PATTERN.finditer(text):
        velocity_match = match
    if velocity_match is not None:
        metrics["incns_velocity_iterations"] = float(velocity_match.group(1))
        metrics["incns_velocity_error"] = float(velocity_match.group(2))

    newton_match = None
    for match in _NEWTON_PATTERN.finditer(text):
        newton_match = match
    if newton_match is not None:
        metrics["incns_newton_iterations"] = float(newton_match.group(1))

    for match in _L2NORM_PATTERN.finditer(text):
        metrics[f"incns_l2norm_{match.group(1)}"] = float(match.group(2))
    for match in _INFNORM_PATTERN.finditer(text):
        metrics[f"incns_infnorm_{match.group(1)}"] = float(match.group(2))
    return metrics


def _detect_output_format(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".vtu":
        return "vtu"
    if suffix == ".pvtu":
        return "pvtu"
    if suffix == ".dat":
        return "dat"
    if suffix == ".fld":
        return "fld"
    if suffix == ".chk":
        return "chk"
    return "unknown"


def _collect_error_pairs(metrics: dict[str, float | str], *, prefix: str) -> list[tuple[str, float]]:
    pairs: list[tuple[str, float]] = []
    for key, value in metrics.items():
        if not key.startswith(prefix):
            continue
        numeric = _coerce_float(value)
        if numeric is None:
            continue
        pairs.append((key, numeric))
    return pairs


def _coerce_float(value: float | str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
