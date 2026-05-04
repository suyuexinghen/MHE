# Project Leader Document Structure

Use this reference when project leadership needs durable schematization across blueprint, plan, roadmap, README, and handoff artifacts.

## Document Timescales

Use four document classes with distinct horizons and audiences:

- **Blueprint**: longest horizon. Captures whole-system architecture, durable design principles, phase structure, strategic constraints, vocabulary, decision frames, and long-term handoff context.
- **Plan**: phase horizon, user-facing. Captures the goal, scope, non-goals, acceptance criteria, options, risks, and selected direction for one phase or major work slice.
- **Roadmap**: implementation horizon, agent-facing. Expands a plan into ordered steps, file targets, dependencies, validation commands, commit boundaries, reviewer gates, and stop/continue criteria.
- **README / index**: navigation horizon. Captures valuable references, artifact lists, evidence roots, report links, and reading paths.

## Schematization Rules

- A blueprint can contain multiple phases; each phase may have one plan and one roadmap.
- A plan explains what and why for humans; a roadmap explains how and in what order for agents.
- Do not mix speculative long-horizon vision into a near-term roadmap unless it is explicitly marked as future scope.
- Prefer updating existing blueprint, plan, roadmap, README, or index files over creating new files unless the project has no suitable home.
- Keep schema updates evidence-grounded and avoid turning speculative ideas into completed facts.
- At handoff, use the macro schema to offer multiple future directions separated by goal and tradeoff.

## Roadmap Report After Approval

After direction approval, the leader should produce or assign a roadmap report as a durable markdown artifact when the work needs multi-agent execution.

The report should include:

- document classification: blueprint vs plan vs roadmap;
- phase goal and non-goals;
- implementation steps in order;
- file targets and expected artifacts;
- validation commands and acceptance criteria;
- commit boundaries when commits are authorized;
- reviewer/verifier gates;
- known non-claims and future backlog;
- handoff notes for future sessions.

The roadmap should be agent-facing and implementation-ready. It should not replace the user-facing plan; it should add execution detail for the approved plan.
