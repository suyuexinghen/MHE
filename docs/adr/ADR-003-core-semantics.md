# ADR-003: Freeze core semantics

## Status
Accepted

## Decisions
- Manifest fields use `kind`, `entry`, `contracts`, `safety`, and `state_schema_version`.
- Visible lifecycle phases use the wiki's 8-phase model.
- Slot semantics distinguish `primary` and `secondary` bindings.
- Protected components require explicit override checks and cannot be directly mutated by optimizer code.

## Rationale
These are the highest-churn architectural decisions. Freezing them before implementation reduces downstream schema and API rework.
