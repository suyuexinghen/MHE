from __future__ import annotations

import re
from dataclasses import dataclass
from re import Pattern

from metaharness.core.models import ValidationIssue, ValidationIssueCategory
from metaharness_ext.octave.contracts import OctaveExperimentSpec


@dataclass(frozen=True, slots=True)
class OctaveSecurityPattern:
    code: str
    description: str
    pattern: Pattern[str]


OCTAVE_SECURITY_PATTERNS = (
    OctaveSecurityPattern(
        code="octave_security_system_call",
        description="system() command execution is not allowed in controlled Octave scripts.",
        pattern=re.compile(r"\bsystem\s*\(", re.IGNORECASE),
    ),
    OctaveSecurityPattern(
        code="octave_security_unix_call",
        description="unix() command execution is not allowed in controlled Octave scripts.",
        pattern=re.compile(r"\bunix\s*\(", re.IGNORECASE),
    ),
    OctaveSecurityPattern(
        code="octave_security_shell_escape",
        description="Shell escape commands are not allowed in controlled Octave scripts.",
        pattern=re.compile(r"^\s*![^\n]+", re.MULTILINE),
    ),
    OctaveSecurityPattern(
        code="octave_security_urlread",
        description="urlread network access is not allowed in controlled Octave scripts.",
        pattern=re.compile(r"\burlread\s*\(", re.IGNORECASE),
    ),
    OctaveSecurityPattern(
        code="octave_security_urlwrite",
        description="urlwrite network access is not allowed in controlled Octave scripts.",
        pattern=re.compile(r"\burlwrite\s*\(", re.IGNORECASE),
    ),
    OctaveSecurityPattern(
        code="octave_security_web_call",
        description="web() network/browser access is not allowed in controlled Octave scripts.",
        pattern=re.compile(r"\bweb\s*\(", re.IGNORECASE),
    ),
    OctaveSecurityPattern(
        code="octave_security_pkg_install",
        description="pkg install is not allowed in controlled Octave scripts.",
        pattern=re.compile(r"\bpkg\s+install\b", re.IGNORECASE),
    ),
)


class OctaveSecurityScanError(ValueError):
    def __init__(self, issues: list[ValidationIssue]) -> None:
        self.issues = issues
        codes = ", ".join(issue.code for issue in issues)
        super().__init__(f"Octave script failed security scan: {codes}")


class OctaveSecurityScanner:
    def scan(self, spec: OctaveExperimentSpec) -> list[ValidationIssue]:
        source = _script_source(spec)
        issues: list[ValidationIssue] = []
        for security_pattern in OCTAVE_SECURITY_PATTERNS:
            if security_pattern.pattern.search(source):
                issues.append(
                    ValidationIssue(
                        code=security_pattern.code,
                        message=security_pattern.description,
                        subject=spec.task_id,
                        category=ValidationIssueCategory.PROMOTION_BLOCKER,
                        blocks_promotion=True,
                    )
                )
        return issues

    def require_safe(self, spec: OctaveExperimentSpec) -> None:
        issues = self.scan(spec)
        if issues:
            raise OctaveSecurityScanError(issues)


def _script_source(spec: OctaveExperimentSpec) -> str:
    if spec.script.mode == "inline":
        return spec.script.inline_source or ""
    if spec.script.mode == "file":
        return spec.script.script_path or ""
    return "\n".join([spec.script.function_name or "", *spec.script.function_args])
