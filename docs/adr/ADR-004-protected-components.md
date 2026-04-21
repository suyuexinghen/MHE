# ADR-004: Protected components

## Status
Accepted

## Context
Certain core components (Policy, Identity, Evaluation-QC) act as
constitutional backstops: replacing them silently would let the optimizer or
operator override safety invariants. The master roadmap and the wiki describe
these components as *protected*, meaning their primary slot must not be rebound
or overwritten without an explicit human review gate.

## Decision
- Protection is declared in the manifest at ``safety.protected``. A component
  node in a graph may also carry ``protected=true`` for operator overrides.
- The semantic validator (``metaharness.core.validators.validate_graph``)
  rejects candidate graphs that attempt to bind more than one component to the
  primary slot of a protected component, emitting the
  ``protected_slot_override`` issue code.
- The optimizer has *no* write path into the registry or active graph. The only
  path from a mutation proposal to a committed graph is the
  :class:`metaharness.core.mutation.MutationSubmitter`, which in turn delegates
  to a governance reviewer (by default the Policy component's
  ``review_proposal``). Human review is therefore modelled as a pluggable
  reviewer callable rather than an in-band prompt.
- Protected components may still be upgraded through the staged candidate
  graph + atomic commit flow, but only when the reviewer explicitly approves
  the proposal.

## Rationale
Keeping protection metadata on the manifest makes it static, inspectable, and
testable. Centralising override rejection in the validator ensures all paths
(CLI, mutation submitter, demo harness, boot orchestrator) honour the same
policy. Funnelling every mutation through the reviewer keeps the Optimizer
truly proposal-only and prevents regressions that would otherwise leak
write authority into the meta layer.
