from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from metaharness.benchmark_drivers.claude_cli import ClaudeCLIResult
from metaharness.benchmark_drivers.io import write_json, write_text
from metaharness.benchmark_drivers.models import ClaudeInvocationRecord


class ACPBrainConfig(BaseModel):
    command: list[str] = Field(
        default_factory=lambda: ["npx", "@agentclientprotocol/claude-agent-acp"]
    )
    cwd: str = "."
    env: dict[str, str] = Field(default_factory=lambda: {"ACP_PERMISSION_MODE": "acceptEdits"})
    session_key: str = "mhe-benchmark"
    timeout_seconds: float = 300.0
    sdk_root: Path | None = None


class ACPBrainProvider:
    def __init__(self, config: ACPBrainConfig | None = None) -> None:
        self.config = config or ACPBrainConfig()

    def propose(self, *, prompt: str, output_dir: Path) -> ClaudeCLIResult:
        return asyncio.run(self._propose(prompt=prompt, output_dir=output_dir))

    def build_json_diagnostic_prompt(self, task: str) -> str:
        return (
            "You are connected through ACP for an MHE benchmark diagnostic. "
            "Do not use tools. Return only a JSON object with keys: "
            "proposal, diagnostic_status, tool_use_allowed, and notes. "
            "Set diagnostic_status to ok if you can answer with JSON-only content. "
            f"Task: {task}"
        )

    def diagnose_json_response(self, result: dict[str, Any]) -> dict[str, Any]:
        proposal = self._extract_proposal(result)
        return {
            "transport": "acp",
            "diagnostic_status": "ok" if proposal else "blocked",
            "json_proposal_available": bool(proposal),
            "content_empty": not bool(str(result.get("content", "")).strip()),
            "proposal": proposal,
            "stop_reason": result.get("execution_meta", {}).get("stop_reason")
            if isinstance(result.get("execution_meta"), dict)
            else None,
        }

    async def _propose(self, *, prompt: str, output_dir: Path) -> ClaudeCLIResult:
        output_dir.mkdir(parents=True, exist_ok=True)
        prompt_path = write_text(output_dir / "acp_prompt.txt", prompt)
        command_path = write_json(
            output_dir / "acp_command.json",
            {
                "command": self.config.command,
                "cwd": self.config.cwd,
                "env": self.config.env,
                "session_key": self.config.session_key,
                "timeout_seconds": self.config.timeout_seconds,
                "sdk_root": str(self.config.sdk_root) if self.config.sdk_root else None,
            },
        )
        stdout_path = output_dir / "acp_stdout.json"
        stderr_path = output_dir / "acp_stderr.txt"
        result_path = output_dir / "acp_result.json"
        proposal_path = output_dir / "proposal.json"
        invocation = ClaudeInvocationRecord(
            binary=self.config.command[0] if self.config.command else "acp",
            command=self.config.command,
            prompt_path=str(prompt_path),
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
            result_path=str(result_path),
            proposal_path=str(proposal_path),
            return_code=None,
        )
        try:
            result = await asyncio.wait_for(
                self._run_acp_prompt(prompt), timeout=self.config.timeout_seconds
            )
        except Exception as exc:
            error = self._format_error(exc)
            write_text(stdout_path, "")
            write_text(stderr_path, error)
            write_json(result_path, {"is_error": True, "error": error, "transport": "acp"})
            return ClaudeCLIResult(invocation=invocation, error=error)

        write_json(stdout_path, result)
        write_text(stderr_path, "")
        write_json(result_path, result)
        proposal = self._extract_proposal(result)
        if not proposal:
            write_json(proposal_path, {})
            return ClaudeCLIResult(
                invocation=invocation,
                result=result,
                proposal={},
                error="ACP response did not contain a JSON proposal",
            )
        write_json(proposal_path, proposal)
        write_json(command_path, {"command": self.config.command, "result_path": str(result_path)})
        return ClaudeCLIResult(invocation=invocation, result=result, proposal=proposal)

    async def _run_acp_prompt(self, prompt: str) -> dict[str, Any]:
        self._ensure_sdk_path()
        try:
            from aeloon.plugins._sdk.acp.client import ACPClient
            from aeloon.plugins._sdk.acp.types import BackendProfile
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "ACP provider requires Aeloon ACP SDK and agent-client-protocol dependencies"
            ) from exc

        client = ACPClient()
        profile = BackendProfile(
            name="mhe_benchmark",
            command=self.config.command,
            cwd=self.config.cwd,
            timeout_seconds=self.config.timeout_seconds,
            env=self.config.env,
        )
        await client.connect(profile)
        try:
            response = await client.prompt(self.config.session_key, prompt)
        finally:
            await client.disconnect()
        return {
            "transport": "acp",
            "content": response.content,
            "usage": response.usage,
            "execution_meta": response.execution_meta,
        }

    def _ensure_sdk_path(self) -> None:
        sdk_root = self.config.sdk_root or _default_aeloon_root()
        if sdk_root is None:
            return
        root = str(sdk_root)
        if root not in sys.path:
            sys.path.insert(0, root)

    def _format_error(self, exc: Exception) -> str:
        message = str(exc)
        return message if message else exc.__class__.__name__

    def _extract_proposal(self, result: dict[str, Any]) -> dict[str, Any]:
        content = result.get("content")
        if not isinstance(content, str) or not content.strip():
            return {}
        parsed = self._parse_json_content(content)
        if not isinstance(parsed, dict):
            return {}
        proposal = parsed.get("proposal", parsed)
        return proposal if isinstance(proposal, dict) else {}

    def _parse_json_content(self, content: str) -> Any:
        stripped = content.strip()
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass
        if "```" not in stripped:
            return None
        parts = stripped.split("```")
        for part in parts:
            candidate = part.strip()
            if candidate.startswith("json"):
                candidate = candidate[4:].strip()
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue
        return None


def _default_aeloon_root() -> Path | None:
    for parent in Path(__file__).resolve().parents:
        candidate = parent.parent / "aeloon" / "plugins" / "_sdk" / "acp"
        if candidate.exists():
            return parent.parent
    return None
