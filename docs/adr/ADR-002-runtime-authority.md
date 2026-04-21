# ADR-002: Internal graph model is authoritative

## Status
Accepted

## Decision
The runtime-authoritative representation is the internal graph model. XML is an import and configuration format only.

## Rationale
This keeps runtime behavior independent from configuration syntax and lets the system validate, stage, and version candidate graphs consistently.
