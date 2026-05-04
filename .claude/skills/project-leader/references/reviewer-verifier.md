# Project Leader Reviewer and Verifier Gates

Use this reference when a project leader needs independent review, acceptance, follow-up classification, or safe shutdown.

## Review Separation

Do not let the same active context both author and accept claim-bearing or manager-facing work.

Use separate passes when the work affects:

- reports or product claims;
- scientific benchmark conclusions;
- roadmap direction;
- approval-gated implementation;
- handoff or stop recommendations;
- external-facing documentation.

## Blueprint / Plan / Roadmap Review Loop

Blueprint, plan, and roadmap artifacts should pass a separate review-and-improvement loop before they drive implementation:

- **Authoring pass**: leader or writer creates the artifact.
- **Review pass**: independent reviewer checks logical rigor, feasibility, scope boundaries, evidence support, and implementation readiness.
- **Improvement pass**: writer or improvement agent revises according to review comments.
- **Acceptance pass**: reviewer/verifier returns explicit `complete` or `needs changes` before the artifact becomes implementation guidance.

Reviewers should evaluate:

- whether claims follow from evidence;
- whether milestones are realistically implementable;
- whether blueprint, plan, and roadmap timescales are mixed incorrectly;
- whether non-goals and non-claims are explicit;
- whether agent-facing roadmap steps have file targets, validation commands, dependencies, and stop gates.

The main agent may continue directly after approval only when the reviewed-and-improved artifact is accepted or when the user explicitly waives this review loop.

## Reviewer / Verifier Coordination

Reviewer/verifier lanes are not optional when the task result is manager-facing, claim-bearing, risky, intended to close a work slice, or establishes a roadmap direction.

Ask the leader to suggest reviewers when:

- a report makes product or business claims;
- a benchmark result might overclaim numerical superiority;
- a new evidence artifact schema needs review;
- a roadmap or plan could over-broaden scope;
- a real-run failure could be runner bug vs dependency skip vs solver failure;
- completed docs need manager-facing clarity.

Use read-only Explore/Plan agents for review unless code edits are explicitly needed. The reviewer prompt should ask for an explicit verdict: `complete` or `needs changes`, list blocking/non-blocking issues, and state whether the leader may recommend stopping.

## Follow-Up Classification

When a verifier passes but identifies non-blocking follow-up:

- ask the leader to classify it before shutdown;
- complete it immediately only if it is tiny, in-scope, and improves evidence completeness without changing conclusions;
- otherwise record it as explicit future work in the final summary, backlog, roadmap, or handoff artifact.

## Completion and Shutdown

The workflow is complete only when:

- there is a named leader with a clear role;
- shared tasks reflect completed evidence and pending next steps;
- the leader owns active coordination while preparing a memo, schema update, or roadmap report;
- implementation work has focused validation or evidence;
- reviewer/verifier acceptance is explicit;
- non-blocking follow-ups are handled or captured;
- handoff recommendations include multiple future directions when more than one valid path exists;
- team resources are shut down and deleted only after verifier acceptance, leader stop recommendation, and explicit follow-up handling.

## Product / Business Analysis Lens

For manager-facing outputs, require the leader to translate evidence into:

- what the current product can truthfully claim;
- what remains an R&D capability gap;
- which next technical slice most improves product positioning;
- where agent + scientific software integration shows workflow value;
- what must be proven before claiming numerical or performance superiority.
