from __future__ import annotations

import json
import re
from pathlib import Path

from metaharness_ext.deepmd.contracts import DeepMDDiagnosticSummary


def build_diagnostic_summary(
    run_dir: Path,
    diagnostic_files: list[str],
    stdout_path: str,
) -> DeepMDDiagnosticSummary:
    summary = DeepMDDiagnosticSummary()
    lcurve_path = run_dir / "lcurve.out"
    if lcurve_path.exists():
        summary.learning_curve_path = str(lcurve_path)
        parse_lcurve(lcurve_path, summary)

    train_log_path = run_dir / "train.log"
    if train_log_path.exists():
        summary.train_log_path = str(train_log_path)
        parse_train_log_clues(train_log_path.read_text(), summary)

    compressed_model = run_dir / "compressed_model.pb"
    if compressed_model.exists():
        summary.compressed_model_path = str(compressed_model)

    stdout_file = Path(stdout_path)
    stdout_text = stdout_file.read_text() if stdout_file.exists() else ""
    if stdout_text:
        parse_test_metrics(stdout_text, summary)
        parse_compress_output(stdout_text, summary)
        parse_model_devi_output(stdout_text, summary)
        parse_neighbor_stat_output(stdout_text, summary)
        parse_train_log_clues(stdout_text, summary)

    for diagnostic in diagnostic_files:
        diagnostic_path = Path(diagnostic)
        message = f"Discovered diagnostic: {diagnostic_path.name}"
        if message not in summary.messages:
            summary.messages.append(message)
        text = diagnostic_path.read_text()
        if diagnostic_path.name.startswith("model_devi"):
            parse_model_devi_output(text, summary)
        elif diagnostic_path.name.startswith("neighbor_stat"):
            parse_neighbor_stat_output(text, summary)
        elif diagnostic_path.name.startswith("test") or diagnostic_path.name.startswith("results"):
            parse_test_metrics(text, summary)
        elif diagnostic_path.name == "train.log":
            parse_train_log_clues(text, summary)
        elif diagnostic_path.name in ("result.out", "result.json"):
            parse_autotest_results(diagnostic_path, summary)
    return summary


def parse_lcurve(path: Path, summary: DeepMDDiagnosticSummary) -> None:
    lines = path.read_text().splitlines()
    header: list[str] = []
    data_lines: list[str] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            candidate = line.lstrip("#").strip().split()
            if candidate:
                header = candidate
            continue
        data_lines.append(line)
    if not data_lines:
        return

    last = data_lines[-1].split()
    if last:
        try:
            summary.last_step = int(float(last[0]))
        except ValueError:
            pass

    named_values = _map_named_columns(header, last)
    summary.lcurve_metrics.update(named_values)
    summary.rmse_e_trn = _pick_first_float(named_values, ["rmse_e_trn", "rmse_e_train", "rmse_e"])
    summary.rmse_f_trn = _pick_first_float(named_values, ["rmse_f_trn", "rmse_f_train", "rmse_f"])
    summary.rmse_e_val = _pick_first_float(named_values, ["rmse_e_val", "rmse_e_test"])
    summary.rmse_f_val = _pick_first_float(named_values, ["rmse_f_val", "rmse_f_test"])

    if summary.rmse_e_trn is None and len(last) >= 2:
        summary.rmse_e_trn = _safe_float(last[1])
    if summary.rmse_f_trn is None and len(last) >= 3:
        summary.rmse_f_trn = _safe_float(last[2])


def parse_test_metrics(text: str, summary: DeepMDDiagnosticSummary) -> None:
    patterns = {
        "rmse_e": r"rmse[_ ]e(?:nergy)?\s*[=:]\s*([0-9.eE+-]+)",
        "rmse_f": r"rmse[_ ]f(?:orce)?\s*[=:]\s*([0-9.eE+-]+)",
        "rmse_v": r"rmse[_ ]v(?:irial)?\s*[=:]\s*([0-9.eE+-]+)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            summary.test_metrics[key] = float(match.group(1))


def parse_compress_output(text: str, summary: DeepMDDiagnosticSummary) -> None:
    compressed_match = re.search(
        r"(?:saved|written|output)\s+(?:to\s+)?([^\s]+(?:graph-compress|compressed_model|compressed)[^\s]*\.pb)",
        text,
        re.IGNORECASE,
    )
    if compressed_match:
        summary.compressed_model_path = compressed_match.group(1)
    elif "compress" in text.lower() and "pb" in text.lower() and not summary.compressed_model_path:
        summary.messages.append("Compress stdout mentions PB output.")


def parse_model_devi_output(text: str, summary: DeepMDDiagnosticSummary) -> None:
    patterns = {
        "max_devi_f": r"max[_ ]devi[_ ]f\s*[=:]\s*([0-9.eE+-]+)",
        "avg_devi_f": r"avg[_ ]devi[_ ]f\s*[=:]\s*([0-9.eE+-]+)",
        "min_devi_f": r"min[_ ]devi[_ ]f\s*[=:]\s*([0-9.eE+-]+)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            summary.model_devi_metrics[key] = float(match.group(1))
    lowered = text.lower()
    for marker in ("candidate", "accurate", "failed"):
        if marker in lowered:
            message = f"Model deviation output mentions {marker}."
            if message not in summary.messages:
                summary.messages.append(message)


def parse_neighbor_stat_output(text: str, summary: DeepMDDiagnosticSummary) -> None:
    patterns = {
        "min_nbor_dist": r"min[_ ]n(?:eig)?h?b?or[_ ]dist\s*[=:]\s*([0-9.eE+-]+)",
        "max_nbor_size": r"max[_ ]n(?:eig)?h?b?or[_ ]size\s*[=:]\s*([0-9.eE+-]+)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            summary.neighbor_stat_metrics[key] = float(match.group(1))
    sel_match = re.search(r"sel\s*[=:]\s*\[([^\]]+)\]", text, re.IGNORECASE)
    if sel_match:
        message = f"Neighbor stat suggested sel [{sel_match.group(1).strip()}]."
        if message not in summary.messages:
            summary.messages.append(message)


def parse_train_log_clues(text: str, summary: DeepMDDiagnosticSummary) -> None:
    for key, pattern in {
        "deepmd_version": r"(?:deepmd|deepmd-kit)[^\n]*?version[^\n:=]*[:=]\s*([^\s\n]+)",
        "backend": r"backend\s*[:=]\s*([^\n]+)",
        "device": r"device\s*[:=]\s*([^\n]+)",
        "wall_time": r"(?:wall[_ ]?time|elapsed[_ ]?time|training time)\s*[:=]\s*([^\n]+)",
    }.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            summary.log_clues[key] = match.group(1).strip()


def parse_autotest_results(path: Path, summary: DeepMDDiagnosticSummary) -> None:
    if path.name == "result.json":
        try:
            data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            return
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    metrics = {
                        k: float(v)
                        for k, v in value.items()
                        if isinstance(v, int | float)
                    }
                    if metrics:
                        summary.autotest_properties[key] = metrics
                elif isinstance(value, int | float):
                    summary.autotest_properties.setdefault("summary", {})[key] = float(value)
        return

    if path.name == "result.out":
        text = path.read_text()
        current_property: str | None = None
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("#"):
                current_property = line.lstrip("#").strip().split()[0]
                continue
            parts = line.split()
            if len(parts) >= 2 and current_property is not None:
                key = parts[0]
                try:
                    summary.autotest_properties.setdefault(current_property, {})[key] = float(parts[1])
                except ValueError:
                    pass


def _map_named_columns(header: list[str], values: list[str]) -> dict[str, float]:
    if not header or len(header) != len(values):
        return {}
    metrics: dict[str, float] = {}
    for name, value in zip(header, values, strict=False):
        if name.lower() == "step":
            continue
        parsed = _safe_float(value)
        if parsed is not None:
            metrics[name.lower()] = parsed
    return metrics


def _pick_first_float(metrics: dict[str, float], keys: list[str]) -> float | None:
    for key in keys:
        value = metrics.get(key)
        if value is not None:
            return value
    return None


def _safe_float(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None
