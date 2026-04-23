from __future__ import annotations

import re
from pathlib import Path

from metaharness_ext.deepmd.contracts import DPGenIterationCollection, DPGenIterationSummary


class DPGenIterationCollector:
    _COUNT_PATTERNS = {
        "candidate_count": re.compile(r"candidate\w*\s*[:=]\s*(\d+)", re.IGNORECASE),
        "accurate_count": re.compile(r"accurate\w*\s*[:=]\s*(\d+)", re.IGNORECASE),
        "failed_count": re.compile(r"failed\w*\s*[:=]\s*(\d+)", re.IGNORECASE),
    }
    _CONVERGED_PATTERN = re.compile(r"\b(converged|no\s+new\s+candidate)\b", re.IGNORECASE)
    _RELABEL_PATTERN = re.compile(r"\b(relabel|pick(?:ed|_number)?)\b", re.IGNORECASE)

    def collect(self, run_dir: Path) -> DPGenIterationCollection:
        collection = DPGenIterationCollection()
        record_path = run_dir / "record.dpgen"
        record_counts = DPGenIterationSummary(iteration_id="record", path=str(run_dir))
        if record_path.exists():
            collection.record_path = str(record_path)
            self._apply_counts(record_path.read_text(), record_counts)

        for iteration_dir in sorted(path for path in run_dir.glob("iter.*") if path.is_dir()):
            summary = DPGenIterationSummary(
                iteration_id=iteration_dir.name, path=str(iteration_dir)
            )
            train_dir = iteration_dir / "00.train"
            devi_dir = iteration_dir / "01.model_devi"
            fp_dir = iteration_dir / "02.fp"
            if train_dir.exists():
                summary.train_path = str(train_dir)
            if devi_dir.exists():
                summary.model_devi_path = str(devi_dir)
            if fp_dir.exists():
                summary.fp_path = str(fp_dir)

            text_paths = [path for path in iteration_dir.rglob("*") if path.is_file()]
            if record_path.exists():
                text_paths.insert(0, record_path)
            for text_path in text_paths:
                self._apply_counts(text_path.read_text(), summary)

            collection.iterations.append(summary)
            collection.candidate_count += summary.candidate_count
            collection.accurate_count += summary.accurate_count
            collection.failed_count += summary.failed_count

        if collection.iterations:
            collection.candidate_count = max(
                collection.candidate_count, record_counts.candidate_count
            )
            collection.accurate_count = max(collection.accurate_count, record_counts.accurate_count)
            collection.failed_count = max(collection.failed_count, record_counts.failed_count)
            collection.messages.append(f"Collected {len(collection.iterations)} DP-GEN iterations.")
        all_text = "\n".join(
            path.read_text(errors="ignore") for path in sorted(run_dir.rglob("*")) if path.is_file()
        )
        if self._RELABEL_PATTERN.search(all_text):
            collection.messages.append("Detected relabeling clues in DP-GEN workspace.")
        if self._CONVERGED_PATTERN.search(all_text):
            collection.messages.append("DP-GEN workflow appears converged.")
        return collection

    def _apply_counts(
        self,
        text: str,
        target: DPGenIterationCollection | DPGenIterationSummary,
    ) -> None:
        for field_name, pattern in self._COUNT_PATTERNS.items():
            match = pattern.search(text)
            if match:
                setattr(target, field_name, max(int(match.group(1)), getattr(target, field_name)))
