# Design and Method Documents

Use this reference when creating or auditing benchmark design documents.

## Purpose

A method document defines what the benchmark can and cannot prove before implementation starts. It prevents category errors, fake claims, and unreviewable experiments.

## Required Document Shape

A benchmark method document should include:

1. **Purpose** — what scientific workflow is being benchmarked.
2. **Scope and non-claims** — what is covered and explicitly not claimed.
3. **Suite and cases** — suite name, output root, first-round cases, and unsupported sentinel cases.
4. **Lanes** — extension, direct, and agent lane definitions.
5. **Artifacts** — expected files per lane and comparator outputs.
6. **Commands** — dry-run commands, focused case commands, compare commands, and real-run command when applicable.
7. **Comparator design** — summary-table columns, verdict taxonomy, bundle fields, and repeat aggregation shape.
8. **Approval gates** — suite approval manifests, blocked profiles, excluded claims, and evidence needed for stronger claims.
9. **Acceptance checklist** — objective completion criteria.
10. **Future bridge / backlog** — known missing capabilities and next implementation steps.

The QCompute × ABACUS method document is the clearest compact template: `Purpose`, `Scope and non-claims`, `Suite and cases`, `Lanes`, `Artifacts`, `Commands`, `Acceptance checklist`, and `Future bridge work`.

## Suite Onboarding Checklist

Before implementation, a new suite method doc should make these decisions explicit:

- suite name and output directory;
- first-round positive cases and skipped sentinel cases;
- shared `BenchmarkCaseSpec` fields and domain metric names;
- extension/direct/agent lane boundaries;
- dry-run command, real-solver command, real-Claude command, and compare command;
- artifact tree for each lane and comparison outputs;
- comparator columns and verdict labels;
- approval profiles, excluded claims, and promotion blockers;
- smallest implementation slices and validation commands.

## Category-Error Guardrail

Before defining cases, check whether two workflows solve the same scientific task.

- If they solve the same task, compare them in one suite.
- If they use different solver families or scientific objectives, split them into independent suites.
- Do not compare Octave numerical scripts against Nektar++ PDE solver cases as if one is a replacement for the other.
- Do not claim ABACUS DFT coverage from a QCompute Hamiltonian proxy.
- Do not compare PyCFD FVM residuals, Nektar L2/Linf errors, Fealpy FEM errors, Octave analytic errors, QCompute energy errors, or ABACUS converter status as one metric family.

## Case Catalog Requirements

Each benchmark case should map to a `BenchmarkCaseSpec` shape:

- `case_id`
- `suite`
- `task_family`
- `description`
- `required_capabilities`
- `source_reference`
- `expected_metrics`
- `reference_metrics` or tolerances
- `problem_definition`
- `metadata`
- `capability_gated` when support is incomplete

## Metrics by Domain

Use domain-specific metrics:

- **Octave**: absolute/relative error, endpoint error, residual, iterations, elapsed time.
- **Nektar**: L2/Linf error norms, variable names, solver status, parse status, elapsed time.
- **QCompute**: energy, energy error, qubit count, Pauli term count, shots completed, validation status.
- **ABACUS bridge**: source provenance, format support, converter status, Hamiltonian validation result.
- **PyCFD / FVM extensions**: residual_l1, residual_l2, wall_time_seconds, iterations, ncells, nnodes, nfaces, convergence_status. Validate against tolerance (default 1e-5), not exact-solution error norms. FVM solvers converge by residual decay; residual norms replace FEM L2/H1 error norms.

## Non-Claims Template

Use explicit non-claims whenever a suite is a proxy or dry-run:

```markdown
This benchmark does not claim:

- the MHE extension improves solver numerical accuracy;
- dry-run metrics are real solver measurements;
- unsupported source formats are converted;
- proxy cases cover the full upstream scientific package;
- evidence count alone proves workflow superiority.
```

## Method Doc Completion Criteria

A method doc is ready when a new implementer can answer:

- Which suite name should be passed to `benchmark-run`?
- Which cases are first-round positive cases?
- Which cases are explicit skipped sentinels?
- Which files must each lane write?
- What command generates dry-run outputs?
- What command is allowed to run real tools?
- What result is enough for a report, and what remains non-claimable?
