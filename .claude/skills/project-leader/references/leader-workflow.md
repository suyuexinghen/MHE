# Project Leader Workflow

Use this reference when launching a leader teammate, asking it for direction options, or coordinating approved implementation.

## Shared Task Frame

Before launching the teammate, brief it with:

- current project goal and non-goals;
- completed artifacts and evidence roots;
- current task status and blockers;
- required reports or manager-facing outputs;
- verification commands already run;
- non-claim boundaries that must not be crossed;
- current blueprint files that contain whole-project design or phase structure;
- current plan files that contain user-facing goals, options, and acceptance criteria;
- current roadmap files that contain implementation sequencing;
- current README/index files that contain valuable references, evidence roots, report lists, or navigation pointers;
- whether the user has already approved a direction or still needs to select one.

Keep the frame concise and evidence-based. Do not ask the leader to rediscover everything from scratch if the current state is already known.

## Launch Rules

Use a real team when the user asks for an agent teammate, team, visible project leader, ongoing coordination, roadmap implementation, or approval-gated multi-agent execution. Create the team first, then launch the leader with `team_name` so the teammate is visible in the roster and can own shared tasks.

Use a standalone Agent only for one-off advisory memos where team visibility is not requested.

Use the Agent tool with a planning/research-capable agent unless implementation is explicitly required. Name the teammate clearly, such as `benchmark-lead`, `report-lead`, `roadmap-lead`, or `product-lead`.

Project-leader teammates should run on Sonnet unless the user explicitly overrides the model in the current conversation.

Create a shared task for the leader's memo, schematization, roadmap report, or coordination responsibility. Assign it to the leader, mark it `in_progress`, then mark it complete when the leader returns or writes the artifact.

## Direction Options

When multiple valid future directions exist, ask the leader to present options before implementation:

- each option must include goal, value, tradeoff, scope, and likely validation evidence;
- rate each option on two dimensions: Feasibility and Value Gain;
- recommend one option first, but keep alternatives clear;
- ask the user to approve or select a direction unless they already authorized a specific direction in the current conversation;
- after approval, the leader may extend schematization, write the plan/roadmap report, and coordinate implementation.

## Dual-Dimension Rating

Rate each option on two independent dimensions from 1 to 5 stars:

- **Feasibility**: How easy is this to execute right now? Consider existing infrastructure, dependency availability, blast radius, flaky/unknown behavior, and whether new code surface is needed.
- **Value Gain**: How much does this improve evidence, claims, product positioning, or scientific completeness?

Recommend the option with the best joint score, but surface high-value/low-feasibility and low-value/high-feasibility choices separately so the user can choose strategically.

## Active Execution

Once the roadmap report is written and the direction is approved:

- create or update shared tasks for each roadmap step;
- assign implementation-capable agents only to concrete edit/test/doc tasks;
- keep the leader responsible for coordination, not self-approval;
- run focused validation after each implementation slice;
- commit after each completed phase only when the user authorized commits;
- ask a separate verifier for an explicit `complete` or `needs changes` verdict;
- ask the leader to classify verifier follow-ups as in-scope now vs backlog;
- shut down the team only after verifier acceptance, leader stop recommendation, and follow-up handling.

Default execution rule: once the leader gives concrete next-step guidance within an approved direction, continue directly without asking the user for confirmation. Pause for the real administrator/user only when the leader identifies a key product, scope, budget, risk, destructive action, external side effect, or scientific-design decision that requires administrator input.

## Handoff Behavior

When active work is complete or paused, ask the leader for multiple future directions from the project-wide schema, not only one next command. Good directions should differ by purpose, such as real-run evidence, scientific validation, product/reporting, architecture cleanup, or documentation/reference quality.

Present handoff directions as choices for the user. Do not auto-execute handoff options unless active leader-guided execution is still authorized.
