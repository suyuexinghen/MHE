from __future__ import annotations

import re
from pathlib import Path

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.jedi.capabilities import CAP_JEDI_DIAGNOSTICS
from metaharness_ext.jedi.contracts import JediDiagnosticSummary, JediRunArtifact
from metaharness_ext.jedi.slots import JEDI_DIAGNOSTICS_SLOT


class JediDiagnosticsCollectorComponent(HarnessComponent):
    """Extract structured evidence from JEDI diagnostic outputs."""

    COST_FUNCTION_RE = re.compile(r"(?:cost function|cost)\s*[:=]\s*([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)", re.IGNORECASE)
    GRADIENT_NORM_RE = re.compile(r"gradient\s+norm\s*[:=]\s*([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)", re.IGNORECASE)
    OUTER_ITERATION_RE = re.compile(r"outer\s+iteration\s*[:#=]?\s*(\d+)", re.IGNORECASE)
    INNER_ITERATION_RE = re.compile(r"inner\s+iteration\s*[:#=]?\s*(\d+)", re.IGNORECASE)
    MINIMIZER_ITERATION_RE = re.compile(r"minimizer\s+iteration\s*[:#=]?\s*(\d+)", re.IGNORECASE)

    IODA_GROUPS = {
        "MetaData",
        "ObsValue",
        "ObsError",
        "PreQC",
        "HofX",
        "EffectiveError",
        "DerivedObsValue",
        "DerivedMetaData",
        "ObsErrorData",
        "QCFlags",
    }

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(JEDI_DIAGNOSTICS_SLOT)
        api.declare_input("run", "JediRunArtifact")
        api.declare_output("diagnostics", "JediDiagnosticSummary", mode="sync")
        api.provide_capability(CAP_JEDI_DIAGNOSTICS)

    def collect(self, artifact: JediRunArtifact) -> "JediDiagnosticSummary":
        groups_found: set[str] = set()
        files_scanned: list[str] = []
        messages: list[str] = []
        cost_values: list[float] = []
        gradient_norms: list[float] = []
        outer_iterations: list[int] = []
        inner_iterations: list[int] = []
        minimizer_iterations: list[int] = []
        posterior_output_detected = False
        observer_output_detected = False

        candidate_paths = [
            *artifact.diagnostic_files,
            *( [artifact.stdout_path] if artifact.stdout_path else [] ),
        ]

        for path_str in candidate_paths:
            path = Path(path_str)
            if not path.exists():
                messages.append(f"Diagnostic file not found: {path}")
                continue
            files_scanned.append(str(path))
            groups_found.update(self._scan_file(path))
            text = self._read_text(path)
            if text:
                cost_values.extend(self._extract_float_matches(self.COST_FUNCTION_RE, text))
                gradient_norms.extend(self._extract_float_matches(self.GRADIENT_NORM_RE, text))
                outer_iterations.extend(self._extract_int_matches(self.OUTER_ITERATION_RE, text))
                inner_iterations.extend(self._extract_int_matches(self.INNER_ITERATION_RE, text))
                minimizer_iterations.extend(self._extract_int_matches(self.MINIMIZER_ITERATION_RE, text))
                posterior_output_detected = posterior_output_detected or self._detect_posterior_output(path, text)
                observer_output_detected = observer_output_detected or self._detect_observer_output(path, text)

        return JediDiagnosticSummary(
            ioda_groups_found=sorted(groups_found),
            ioda_groups_missing=sorted(self.IODA_GROUPS - groups_found),
            files_scanned=list(dict.fromkeys(files_scanned)),
            messages=messages,
            minimizer_iterations=max(minimizer_iterations) if minimizer_iterations else None,
            outer_iterations=max(outer_iterations) if outer_iterations else None,
            inner_iterations=max(inner_iterations) if inner_iterations else None,
            initial_cost_function=cost_values[0] if cost_values else None,
            final_cost_function=cost_values[-1] if cost_values else None,
            initial_gradient_norm=gradient_norms[0] if gradient_norms else None,
            final_gradient_norm=gradient_norms[-1] if gradient_norms else None,
            gradient_norm_reduction=self._gradient_norm_reduction(gradient_norms),
            posterior_output_detected=posterior_output_detected,
            observer_output_detected=observer_output_detected,
        )

    def _scan_file(self, path: Path) -> set[str]:
        found: set[str] = set()

        try:
            import h5py

            with h5py.File(path, "r") as f:
                for name in f.keys():
                    if name in self.IODA_GROUPS:
                        found.add(name)
            return found
        except Exception:
            pass

        data = self._read_json(path)
        if isinstance(data, dict):
            for key in data.keys():
                if key in self.IODA_GROUPS:
                    found.add(key)
            return found

        text = self._read_text(path)
        if text:
            for group in self.IODA_GROUPS:
                if group in text:
                    found.add(group)

        return found

    def _read_json(self, path: Path) -> object | None:
        try:
            import json

            return json.loads(path.read_text())
        except Exception:
            return None

    def _read_text(self, path: Path) -> str:
        try:
            return path.read_text()
        except Exception:
            return ""

    def _extract_float_matches(self, pattern: re.Pattern[str], text: str) -> list[float]:
        values: list[float] = []
        for match in pattern.findall(text):
            try:
                values.append(float(match))
            except ValueError:
                continue
        return values

    def _extract_int_matches(self, pattern: re.Pattern[str], text: str) -> list[int]:
        values: list[int] = []
        for match in pattern.findall(text):
            try:
                values.append(int(match))
            except ValueError:
                continue
        return values

    def _gradient_norm_reduction(self, gradient_norms: list[float]) -> float | None:
        if len(gradient_norms) < 2 or gradient_norms[0] == 0:
            return None
        return gradient_norms[-1] / gradient_norms[0]

    def _detect_posterior_output(self, path: Path, text: str) -> bool:
        return path.name == "posterior.out" or "posterior" in text.lower()

    def _detect_observer_output(self, path: Path, text: str) -> bool:
        return path.name.startswith("observer") or "observer" in text.lower()
