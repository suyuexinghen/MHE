# Real-Run Repeated Protocol

Use this reference before executing or reporting real benchmark runs.

## Root Layout

Separate exploratory runs from reportable final runs:

```text
.runs/<suite>-benchmark-pilot/<timestamp-or-label>/
.runs/<suite>-benchmark-final/<suite-or-report-label>/
```

If the repo uses a user-provided `--runs-root`, encode the same distinction in the path name.

## Artifact Truth Hierarchy

Use this hierarchy for conclusions:

1. **Clean final roots** — only source for manager-facing conclusions and numerical claims.
2. **Repeated final run aggregates** — source for timing, stability, success-rate, and flaky flags.
3. **Single final real runs** — source for smoke/capability conclusions only.
4. **Pilot roots** — source for bug reports, driver portability issues, and backlog rows only.
5. **Dry-run roots** — source for workflow/schema/evidence claims only.

Never cite pilot runs as final evidence for solver superiority. If a pilot exposes a bug, fix it and rerun into a clean final root.

## Standard Phase Ladder

Use the smallest phase that supports the claim being made:

1. **Dry-run schema smoke** — validate case catalog, lane artifact shape, comparator parsing, approval gates, and non-claims without external solver or real Claude evidence.
2. **Real solver baseline** — run extension lane or a minimal lane set with `--allow-real-tools` and fake Claude to prove dependency gating, solver execution, stdout/stderr capture, and domain metric parsing.
3. **Real Claude workflow comparison** — add `--allow-real-claude` for direct and agent lanes only after solver baseline evidence is clean; pin Claude binary, model, max turns, permission mode, and prompt policy for parity.
4. **Full-catalog repeated final run** — expand to all supported cases and `--repeat N` only after short-case runs are clean; use this phase for timing, stability, repair-rate, or success-rate claims.

Do not skip from dry-run directly to full-catalog real Claude comparison unless the user explicitly accepts the cost and the report still separates solver, Claude, and workflow gates.

## Real Run Checklist

Before a final real run:

- choose one suite and a small case set;
- confirm solver/dependency binaries with preflight;
- decide whether `--allow-real-claude` is enabled separately from `--allow-real-tools`;
- pin Claude binary/model/max turns/permission/extra args for direct and agent parity;
- use a fresh final runs root with no stale artifacts;
- record exact commands for `benchmark-run` and `benchmark-compare`.

## Repeat Rules

Use `--repeat N` for claims about timing, stability, repair rate, or LLM success rate.

Recommended minimums:

- `N=1` for real-mode smoke only;
- `N=3` for first stability/timing signal;
- `N>=5` before comparing timing or repair-rate trends in a report.

Repeated outputs should preserve per-run roots and write an aggregate such as `comparison/repeat_summary.json` with run count, pass/fail/skip counts, median timing, solver elapsed median, LLM calls, repairs, and flaky flags.

## Failure Rerun Rules

Classify failures before rerunning:

- **capability skip** — expected unsupported case; keep skipped and add backlog only if promotion is planned;
- **dependency skip** — missing binary/package/hardware; do not rerun until dependency is installed or path is fixed;
- **runner portability bug** — driver assumes local behavior that real tools violate; fix the runner, then rerun in a clean final root;
- **solver failure** — real solver ran and failed scientifically/numerically; preserve evidence and include in final results;
- **LLM proposal failure** — Claude output invalid or insufficient; preserve prompt/result and count as LLM behavior unless the prompt/runner was wrong.

Do not cherry-pick successful repeats. If a final repeated run is invalid because of a runner bug, mark the whole root non-final and rerun cleanly after the fix.

## Reporting Rule

Final reports must name the artifact root class:

- `dry-run`: workflow-only claims;
- `pilot real-run`: bugs/backlog only;
- `single final real-run`: smoke/capability claims;
- `repeated final real-run`: timing/stability/success-rate claims.
