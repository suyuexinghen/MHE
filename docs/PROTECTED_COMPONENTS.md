# Protected Components

Protected components are pieces of the runtime that the optimizer is
*forbidden* from mutating. They exist to guarantee that self-growth
cycles cannot rewrite the control plane that supervises them.
ADR-004 captures the original decision; this document is the operator-
facing contract the runtime enforces at every layer.

## 1. Which Components Are Protected?

By default, components whose manifest declares `"safety.protected":
true` are treated as protected. In the baseline topology this applies
to:

- `policy.primary` — final governance veto; cannot be rewired.
- `observability.primary` — provenance sink; removing it would blind
  downstream audits.

### 1.1 Extension-protected slots

Domain-specific extensions can declare their own protected slots.
The runtime respects these as long as the extension's `PROTECTED_SLOTS`
set is visible to the validator.

**`metaharness_ext.nektar` protected slots:**

- `validator.primary` — the final validation gate for solver results;
  rewiring it would break the evidence chain for Nektar++ runs.

**`metaharness_ext.ai4pde` protected slots:**

- `evidence_manager.primary` — scientific evidence bundling; tampering
  would invalidate audit trails.
- `observability_hub.primary` — cross-solver telemetry aggregation.
- `policy_guard.primary` — domain-specific policy enforcement.
- `reference_solver.primary` — trusted baseline solver for comparison
  studies.

Operators can mark additional components as protected by editing their
manifest. The runtime only reads the flag; enforcement happens through
the safety chain.

## 2. What Protection Guarantees

When a component is protected:

1. **No incoming mutations.** The `ContractPruner` refuses to emit
   connection targets whose destination is a protected component.
2. **No outgoing edge rewiring.** Any optimizer-produced
   `add_edge` / `remove_edge` move that touches a protected component
   as source *or* target is dropped before the pipeline sees it.
3. **No template substitution.** Phase B `swap_template` moves that
   would overwrite a protected component are rejected.
4. **No hot-swap initiation without governance.** Even when the swap
   comes from an operator rather than the optimizer, the
   `HotSwapOrchestrator` records a checkpoint and passes control to
   the safety pipeline before replacing the component.

## 3. What Protection Does *Not* Guarantee

Protection is a *write* restriction, not a runtime sandbox. Protected
components still:

- run in the same process as non-protected components (use a
  `SandboxAdapter` if stronger isolation is required);
- receive inbound events through the EventBus;
- can be observed, traced, and benchmarked.

## 4. Operator Checklist

Before rolling a new component out as protected:

- [ ] Set `safety.protected = true` in the manifest.
- [ ] Add a governance reviewer hook; the default `PolicyComponent`
      hook is a good starting point.
- [ ] Wire the `PolicyVetoGate` into the pipeline ahead of
      `AutoRollback` so a veto interrupts commit before rollback is
      needed.
- [ ] Register explicit `MigrationAdapter` entries for every supported
      `state_schema_version` transition. Protected components cannot
      rely on ad-hoc migrations.
- [ ] Keep their manifests under version control; changes should go
      through review rather than hot reload.

## 5. Developer Checklist

When writing an optimizer extension, respect protection by:

- passing the current `ComponentRegistry` to `ContractPruner` so it
  can honour the protected flag;
- ensuring any custom action generator consults
  `ContractPruner.legal_targets(...)` before emitting candidates;
- never bypassing `MutationSubmitter` by calling the
  `ConnectionEngine` directly, even for read-only modifications.

## 6. Testing Protection

The existing test suite covers the core invariants:

- `test_validation.py` — verifies the validator rejects protected
  slot overrides.
- `test_contract_pruner` (inside `test_port_index_and_pruner.py`) —
  verifies pruning honours protected components and denied pairs.
- `test_optimizer.py::test_optimizer_emits_proposal_only` — verifies
  the optimizer has no direct write path.

For custom extensions, add a similar invariant test that attempts a
mutation against your protected component and asserts the mutation is
rejected.
