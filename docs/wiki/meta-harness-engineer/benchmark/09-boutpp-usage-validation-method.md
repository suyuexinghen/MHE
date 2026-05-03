# BOUT++ Usage Validation Method

> 版本：v0.1 | 状态：draft baseline | 面向 `metaharness_ext.boutpp` 的 usage-validation slice。

## Purpose

Define a benchmark-style usage-validation slice for the implemented BOUT++ extension baseline. The goal is not to prove a real local BOUT++ build, but to capture a repeatable comparison between:

- the extension lane that compiles typed run specs into `BOUT.inp` and command metadata;
- the direct CLI/manual workflow lane that reproduces the same compiled command shape;
- the agent-assisted lane that documents the same baseline through a prompt-based lane.

## Scope

In scope:

- a dry-run benchmark runner for BOUT++ usage validation;
- one canonical conduction-style case that exercises typed problem specs, `BOUT.inp` rendering, and command assembly;
- lane evidence files for extension, direct/manual, and agent-assisted workflows;
- comparison notes that preserve claim boundaries.

Out of scope:

- real BOUT++ binary execution;
- building BOUT++ from source;
- upstream solver-suite orchestration;
- physics correctness claims beyond the materialized baseline.

## Evidence Surface

The benchmark slice records:

- the typed `BoutPPProblemSpec` used for the case;
- the compiled `BoutPPRunPlan`;
- rendered `BOUT.inp` content;
- a lane-specific usage note describing the workflow shape;
- a lane summary that remains dry-run friendly.

## Acceptance

- The benchmark runner can materialize extension/direct/agent lane evidence for a conduction-style case without a local BOUT++ build.
- The case catalog and runner stay aligned with the implemented BOUT++ baseline.
- The docs keep the benchmark slice in the future-work bucket and do not claim real solver execution.
