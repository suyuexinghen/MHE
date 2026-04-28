from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from metaharness.benchmark_drivers.io import write_json, write_text
from metaharness.benchmark_drivers.models import ClaudeInvocationRecord


class ClaudeCLIConfig(BaseModel):
    binary: str = "claude"
    model: str | None = None
    max_turns: int = 5
    permission_mode: str = "auto"
    extra_args: list[str] = Field(default_factory=list)


class ClaudeCLIResult(BaseModel):
    invocation: ClaudeInvocationRecord
    result: dict[str, Any] = Field(default_factory=dict)
    proposal: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


CommandRunner = Callable[..., subprocess.CompletedProcess[str]]


class ClaudeCLIBrainProvider:
    def __init__(
        self,
        config: ClaudeCLIConfig | None = None,
        command_runner: CommandRunner | None = None,
    ) -> None:
        self.config = config or ClaudeCLIConfig()
        self._command_runner = command_runner or subprocess.run

    def build_command(self, prompt: str) -> list[str]:
        command = [
            self.config.binary,
            "-p",
            prompt,
            "--output-format",
            "json",
            "--no-session-persistence",
            "--max-turns",
            str(self.config.max_turns),
            "--permission-mode",
            self.config.permission_mode,
        ]
        if self.config.model:
            command.extend(["--model", self.config.model])
        command.extend(self.config.extra_args)
        return command

    def propose(self, *, prompt: str, output_dir: Path) -> ClaudeCLIResult:
        output_dir.mkdir(parents=True, exist_ok=True)
        prompt_path = write_text(output_dir / "claude_prompt.txt", prompt)
        command = self.build_command(prompt)
        command_path = write_json(
            output_dir / "claude_command.json",
            {
                "binary": self.config.binary,
                "command": command,
                "output_format": "json",
                "max_turns": self.config.max_turns,
                "permission_mode": self.config.permission_mode,
                "no_session_persistence": True,
                "model": self.config.model,
            },
        )
        result_path = output_dir / "claude_result.json"
        proposal_path = output_dir / "proposal.json"
        stdout_path = output_dir / "claude_stdout.json"
        stderr_path = output_dir / "claude_stderr.txt"

        try:
            completed = self._command_runner(
                command,
                text=True,
                capture_output=True,
                check=False,
                timeout=300,
            )
        except OSError as exc:
            write_text(stdout_path, "")
            write_text(stderr_path, str(exc))
            invocation = ClaudeInvocationRecord(
                binary=self.config.binary,
                command=command,
                prompt_path=str(prompt_path),
                stdout_path=str(stdout_path),
                stderr_path=str(stderr_path),
                result_path=str(result_path),
                proposal_path=str(proposal_path),
                return_code=None,
            )
            return ClaudeCLIResult(invocation=invocation, error=str(exc))

        write_text(stdout_path, completed.stdout)
        write_text(stderr_path, completed.stderr)
        invocation = ClaudeInvocationRecord(
            binary=self.config.binary,
            command=command,
            prompt_path=str(prompt_path),
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
            result_path=str(result_path),
            proposal_path=str(proposal_path),
            return_code=completed.returncode,
        )
        if completed.returncode != 0:
            return ClaudeCLIResult(invocation=invocation, error=completed.stderr.strip())

        try:
            result = json.loads(completed.stdout or "{}")
        except json.JSONDecodeError as exc:
            return ClaudeCLIResult(invocation=invocation, error=f"invalid Claude JSON: {exc}")

        proposal = result.get("proposal", result if isinstance(result, dict) else {})
        write_json(result_path, result)
        write_json(proposal_path, proposal)
        write_json(command_path, {"command": command, "result_path": str(result_path)})
        return ClaudeCLIResult(invocation=invocation, result=result, proposal=proposal)


class FakeClaudeCLIBrainProvider:
    def __init__(self, proposal: dict[str, Any] | None = None) -> None:
        self.proposal = proposal or {}

    def propose(self, *, prompt: str, output_dir: Path) -> ClaudeCLIResult:
        output_dir.mkdir(parents=True, exist_ok=True)
        prompt_path = write_text(output_dir / "claude_prompt.txt", prompt)
        command = ["fake-claude", "-p", prompt]
        stdout_path = write_json(output_dir / "claude_stdout.json", {"proposal": self.proposal})
        stderr_path = write_text(output_dir / "claude_stderr.txt", "")
        result_path = write_json(output_dir / "claude_result.json", {"proposal": self.proposal})
        proposal_path = write_json(output_dir / "proposal.json", self.proposal)
        command_path = write_json(output_dir / "claude_command.json", {"command": command})
        invocation = ClaudeInvocationRecord(
            binary="fake-claude",
            command=command,
            prompt_path=str(prompt_path),
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
            result_path=str(result_path),
            proposal_path=str(proposal_path),
            return_code=0,
        )
        write_json(command_path, {"command": command, "result_path": str(result_path)})
        return ClaudeCLIResult(
            invocation=invocation, result={"proposal": self.proposal}, proposal=self.proposal
        )
