from __future__ import annotations

from pathlib import Path

from metaharness.benchmark_drivers.claude_cli import ClaudeCLIResult
from metaharness.benchmark_drivers.models import (
    BenchmarkCaseSpec,
    BenchmarkLane,
    ClaudeInvocationRecord,
)
from metaharness_ext.pycfd.benchmark_runner import PyCFDBenchmarkRunner


def _make_vortex_case() -> BenchmarkCaseSpec:
    return BenchmarkCaseSpec(
        case_id="vortex-2d",
        suite="pycfd-pde",
        task_family="pycfd-euler",
        description="Isentropic vortex convection",
        source_reference="PyCFD/vortex",
        expected_metrics=["residual_l1", "residual_l2"],
        tolerance={"residual_l1": 1e-3, "residual_l2": 1e-3},
        problem_definition={
            "case_type": "vortex",
            "task_id": "bench-vortex",
            "nx": 42,
            "ny": 21,
            "t_final": 1.0,
            "dt": 0.01,
        },
    )


class SequencedFakeBrainProvider:
    def __init__(self, proposals: list[dict]):
        self._proposals = proposals
        self.prompts: list[str] = []

    def propose(self, *, prompt: str, output_dir: Path) -> ClaudeCLIResult:
        proposal = self._proposals.pop(0)
        self.prompts.append(prompt)
        output_dir.mkdir(parents=True, exist_ok=True)
        prompt_path = output_dir / "claude_prompt.txt"
        prompt_path.write_text(prompt)
        invocation = ClaudeInvocationRecord(
            binary="fake-claude",
            command=["fake-claude", "-p", prompt],
            prompt_path=str(prompt_path),
            stdout_path=str(output_dir / "claude_stdout.json"),
            stderr_path=str(output_dir / "claude_stderr.txt"),
            result_path=str(output_dir / "claude_result.json"),
            proposal_path=str(output_dir / "proposal.json"),
            return_code=0,
        )
        return ClaudeCLIResult(invocation=invocation, result={"proposal": proposal}, proposal=proposal)


class TestPyCFDBenchmarkRunner:
    def test_dry_run_extension_lane(self, tmp_path: Path):
        runner = PyCFDBenchmarkRunner(runs_root=tmp_path, allow_real_tools=False)
        case = _make_vortex_case()
        summaries = runner.run_case(case, ["extension"])
        assert len(summaries) == 1
        s = summaries[0]
        assert s.lane == "extension"
        assert s.case_id == "vortex-2d"
        assert s.status == "passed"

    def test_dry_run_direct_lane(self, tmp_path: Path):
        runner = PyCFDBenchmarkRunner(runs_root=tmp_path, allow_real_tools=False)
        case = _make_vortex_case()
        summaries = runner.run_case(case, ["direct"])
        assert len(summaries) == 1
        s = summaries[0]
        assert s.lane == "direct"
        assert s.status == "passed"

    def test_dry_run_agent_lane(self, tmp_path: Path):
        runner = PyCFDBenchmarkRunner(runs_root=tmp_path, allow_real_tools=False)
        case = _make_vortex_case()
        summaries = runner.run_case(case, ["agent"])
        assert len(summaries) == 1
        s = summaries[0]
        assert s.lane == "agent"
        assert s.status == "passed"

    def test_agent_lane_accepts_pycfd_spec(self, tmp_path: Path):
        provider = SequencedFakeBrainProvider(
            [
                {
                    "pycfd_spec": {
                        "task_id": "bench-vortex",
                        "case_type": "vortex",
                        "mesh": {"nx": 48, "ny": 24},
                        "flow": {"M_inf": 0.4, "gamma": 1.4},
                        "solver": {"CFL": 0.8, "second_order": True, "use_limiter": False},
                        "t_final": 1.0,
                        "dt": 0.01,
                        "timeout_seconds": 300,
                    }
                }
            ]
        )
        runner = PyCFDBenchmarkRunner(
            runs_root=tmp_path,
            allow_real_tools=False,
            brain_provider=provider,
        )
        summary = runner.run_case(_make_vortex_case(), ["agent"])[0]
        assert summary.passed is True
        assert summary.preflight_status == "passed"
        assert summary.proposal_contract_status == "valid"
        assert summary.attempt_count == 1
        assert summary.llm_calls == 1
        assert summary.repair_count == 0

    def test_agent_lane_repairs_preflight_with_spec_patch(self, tmp_path: Path):
        provider = SequencedFakeBrainProvider(
            [
                {"spec_patch": {"mesh": {"nx": None}}},
                {
                    "spec_patch": {
                        "mesh": {"nx": 64, "ny": 32},
                        "flow": {"M_inf": 0.5, "gamma": 1.4},
                        "solver": {"CFL": 0.9, "second_order": True, "use_limiter": False},
                    }
                },
            ]
        )
        runner = PyCFDBenchmarkRunner(
            runs_root=tmp_path,
            allow_real_tools=False,
            brain_provider=provider,
            max_repair_attempts=1,
        )
        summary = runner.run_case(_make_vortex_case(), ["agent"])[0]
        assert summary.passed is True
        assert summary.preflight_status == "passed"
        assert summary.repair_outcome == "preflight_repaired"
        assert summary.attempt_count == 2
        assert summary.repair_count == 1
        assert summary.llm_calls == 2
        assert len(summary.evidence_files) >= 8
        assert len(summary.evidence_files) == len(set(summary.evidence_files))
        assert any("proposal_attempt_1" in path for path in summary.evidence_files)
        assert any("proposal_attempt_2" in path for path in summary.evidence_files)
        assert any("proposal_preflight_attempt_1.json" in path for path in summary.evidence_files)
        assert any("proposal_preflight_attempt_2.json" in path for path in summary.evidence_files)

    def test_agent_lane_rejects_null_repair_payload(self, tmp_path: Path):
        provider = SequencedFakeBrainProvider(
            [
                {"spec_patch": {"mesh": {"nx": None}}},
                {"spec_patch": {"mesh": {"nx": None}}},
            ]
        )
        runner = PyCFDBenchmarkRunner(
            runs_root=tmp_path,
            allow_real_tools=False,
            brain_provider=provider,
            max_repair_attempts=1,
        )
        summary = runner.run_case(_make_vortex_case(), ["agent"])[0]
        assert summary.passed is False
        assert summary.preflight_status == "failed"
        assert summary.repair_outcome == "preflight_unrepaired_failure"
        assert summary.attempt_count == 2
        assert summary.repair_count == 1
        assert summary.llm_calls == 2

    def test_unknown_lane_ignored(self, tmp_path: Path):
        runner = PyCFDBenchmarkRunner(runs_root=tmp_path)
        case = _make_vortex_case()
        summaries = runner.run_case(case, ["bogus"])  # type: ignore[list-item]
        assert len(summaries) == 0

    def test_run_all_three_lanes(self, tmp_path: Path):
        runner = PyCFDBenchmarkRunner(runs_root=tmp_path, allow_real_tools=False)
        case = _make_vortex_case()
        lanes: list[BenchmarkLane] = ["extension", "direct", "agent"]
        summaries = runner.run_case(case, lanes)
        assert len(summaries) == 3
        lane_names = {s.lane for s in summaries}
        assert lane_names == {"extension", "direct", "agent"}
        for s in summaries:
            assert s.status == "passed"
