from __future__ import annotations

from dataclasses import dataclass, field

from metaharness_ext.lean.contracts import LeanDiagnostic


@dataclass
class MockLeanResult:
    exit_code: int
    stdout: str
    stderr: str
    diagnostics: list[LeanDiagnostic]


@dataclass
class MockLeanBackend:
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    diagnostics: list[LeanDiagnostic] = field(default_factory=list)

    def run(self, file: str) -> MockLeanResult:
        return MockLeanResult(
            exit_code=self.exit_code,
            stdout=self.stdout,
            stderr=self.stderr,
            diagnostics=[
                diagnostic.model_copy(update={"file": diagnostic.file or file})
                for diagnostic in self.diagnostics
            ],
        )
