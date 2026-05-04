---
name: project-leader
description: |
  Use when a task needs ongoing project leadership, task-state management, reviewer/verifier coordination, long-term project schematization, and high-value reporting for project administrators. Trigger when the user asks to call an agent teammate as a project leader, maintain benchmark/report task status, guide next steps, coordinate reviewers, document whole-project blueprint/plan/roadmap files, maintain README/reference indexes, write implementation roadmaps after approval, or shape technical findings into product/business analysis. Especially useful for scientific-computing agent projects and MHE benchmark/report iteration.
author: Claude Code
version: 1.7.2
date: 2026-05-03
---

# Project Leader

Use this skill as a compact router for leader-guided, reviewer-gated project work.

## Core Rule

Keep leadership, implementation, and acceptance separate:

- **Leader**: maintains task state, recommends next actions, preserves the macro project schema, and coordinates reviewers.
- **Implementer / executor**: performs approved code or documentation changes.
- **Reviewer / verifier**: independently returns `complete` or `needs changes`; this is the acceptance gate.

Do not let the same active context both produce the work and accept it as complete when the result affects reports, product claims, roadmap direction, or manager-facing conclusions.

## When To Use

Use this skill when the task involves:

- a project leader, benchmark lead, roadmap lead, report lead, or coordinator;
- multi-step benchmark/report/extension work that needs state management;
- blueprint, plan, roadmap, README, or handoff schematization;
- multiple future directions that need user approval before implementation;
- reviewer/verifier acceptance before stopping or closing the work;
- product/business implications from technical evidence.

## Minimal Startup

Before launching a leader teammate, gather a concise evidence-based frame:

- goal, scope, non-goals, and current approval state;
- completed artifacts, evidence roots, tests, and known blockers;
- non-claims or claim boundaries that must not be crossed;
- existing blueprint, plan, roadmap, handoff, README, or index files;
- whether the user wants direction options, an implementation roadmap, or active coordination.

## Read References On Demand

Load only the reference needed for the current mode:

- `references/document-structure.md`
  - blueprint vs plan vs roadmap vs README responsibilities, timescales, and schematization rules.
- `references/leader-workflow.md`
  - leader launch prompt, shared task frame, direction ratings, approval-gated execution, and handoff behavior.
- `references/reviewer-verifier.md`
  - independent review loops, verifier gates, follow-up classification, and shutdown criteria.

## Default Behavior

- Load `omc-reference` before creating or using any agent team or teammate.
- Prefer an existing real leader teammate surfaced by `<teammate-message teammate_id="...">`; reply with `SendMessage` to that teammate instead of spawning a new `Agent(...)` or external tmux lane.
- For execution work, use a real agent team so concrete implementation, review, and verification happen through team-assigned agents.
- When the user asks for a leader teammate and no suitable teammate exists, create a persistent named leader via `TeamCreate` plus `Agent(..., team_name=...)`; use a project-specific real name such as `<project>-leader`, not reserved metadata names like `team-lead`.
- Use the Agent tool directly only for read-only explore/plan-style tasks, final read-only advisory checks, one-off advisory guidance, or creating a missing persistent teammate through the supported team runtime.
- Do not run concrete task execution in standalone/background agents. If execution needs an agent, assign it through the team workflow instead.
- Run project-leader teammates on Sonnet unless the user explicitly overrides the model.
- Ask the user to approve one direction before implementation when multiple valid directions exist.
- After approval, let the leader coordinate execution directly within the approved scope through team-assigned implementation agents.
- At stop/handoff, present multiple future directions instead of auto-continuing.
- Pause for destructive actions, external side effects, budget, product strategy, or scientific-design choices that broaden scope.

## Teammate Message Routing

Prefer the `<teammate-message teammate_id="...">` pattern when a real teammate already exists or the runtime provides one. Treat the tag as an inbound/runtime teammate message envelope, not as a standalone way to spawn an agent.

Operationally:

- If a leader teammate is already visible through `<teammate-message teammate_id="team-lead">...`, continue by replying with `SendMessage({"to": "team-lead", ...})`.
- If the user provides a teammate-message template for the leader, convert its content into a `SendMessage` payload to the existing named teammate.
- Do not invoke a new `Agent(...)`, external tmux lane, or one-off background agent when an appropriate leader teammate already exists.
- If no real teammate exists, first create or recover a persistent team/teammate through the supported team runtime, then communicate with it via `SendMessage`; do not pretend that writing raw XML creates an agent.
- Keep all concrete implementation routed through team-assigned executors or the main context after approval; the leader message route is for leadership, scheduling, review coordination, and verdicts.

## Pane Capacity Failures

Handle `Error: Failed to create teammate pane: no space for new pane` as a runtime capacity issue, not as a project-work failure.

Operationally:

- Do not retry the same `Agent(..., team_name=...)` call; repeated attempts usually fail until panes are freed.
- Inspect `~/.claude/teams/<team-name>/config.json` before assuming a teammate exists; a member with empty `tmuxPaneId` is only a metadata identity and may accept mailbox delivery without a live process responding.
- Treat `team-lead` with empty `tmuxPaneId` as the main-context leadership identity, not as an acceptance reviewer or live responder.
- If a real teammate is visible through `<teammate-message teammate_id="...">` or team config with a non-empty pane/runtime, route through `SendMessage({"to": "...", ...})` and do not spawn a duplicate pane.
- If `TeamCreate` succeeded but teammate spawning failed, record the fallback explicitly and keep leadership in the main context until a real teammate can be spawned.
- For read-only exploration or verification, use direct `Agent(...)` without `team_name` when the user allows standalone advisory agents; this path can remain available even when team tmux pane allocation fails.
- For concrete execution that truly requires team-assigned agents, pause and ask the user to close panes or approve a main-context/manual fallback.
- To recover team routing, ask the user which panes may be closed, close only approved Claude/agent panes, then spawn a uniquely named real teammate such as `boutpp-reviewer`; do not reuse reserved metadata names like `team-lead`.
- Do not close non-Claude user application panes, including `Warp-x86_64.AppImage`, unless the user explicitly names that pane for closure.
- After successful spawn, verify routing with `SendMessage(to="<real-teammate>", ...)` and wait for an actual response before relying on that teammate for coordination or acceptance.
- Prefer a stable team shape for long-running projects: `team-lead` as metadata/main-context identity, `<project>-leader` as real long-term coordinator, `<project>-reviewer` as real long-term acceptance reviewer, and direct single-use agents for bounded read-only explore/verifier bursts.
- Report the fallback or recovery path explicitly so the user knows whether work continued via `SendMessage`, direct read-only agent, main-context execution, or a newly spawned teammate.

## Leader Prompt Skeleton

```text
You are the project leader for <project/task>. Maintain task state, preserve long-term project schematization, recommend the next direction, and protect report truthfulness.

Context:
- Goal: <goal>
- Scope: <in-scope modules/cases>
- Non-goals: <excluded work>
- Completed: <artifacts/tests/docs>
- Evidence roots: <paths>
- Current status: <what is done/pending>
- Non-claims: <what cannot be concluded>
- Blueprint/plan/roadmap docs: <paths>
- README/index refs: <paths>
- Approval state: <needs user selection | direction already approved>
- Routing mode: <team-based execution | advisory-only>

Return a concise guidance memo with current state, next actions, schema updates, reviewer lanes, risks, and direction options or implementation lanes as appropriate. If execution is needed, assign it through team-tracked agents rather than background agents. Do not edit files unless explicitly assigned documentation work.
```

## Completion Check

The workflow is complete only when:

- shared tasks reflect current state;
- implementation work has focused evidence or validation;
- reviewer/verifier acceptance is explicit;
- the persistent leader teammate has returned a final verdict (`complete` or `needs changes`);
- if the leader says `needs changes`, the tasks are reopened or continued instead of closed;
- leader follow-ups are classified as in-scope now or backlog;
- final handoff includes truthful next directions when meaningful;
- team resources are shut down only after acceptance and follow-up handling.

## References

- Internal workflow pattern extracted from MHE benchmark/report coordination sessions.
- Related skill: `direction-evaluator` for standalone feasibility/value-gain star scoring of recommendations and directions.
- Related skill: `mhe-benchmark-iteration` for benchmark-specific execution/reporting rules.
