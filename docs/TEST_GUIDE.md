 User-Level Testing Guide for MHE

  Based on the documentation, here are the testing approaches from a user's
  perspective:

  ---
  1. Run the Built-in Demos

  Minimal topology (simplest path):
  PYTHONPATH=MHE/src python -m metaharness.demo

  Expanded topology (with planner, memory, async):
  PYTHONPATH=MHE/src python -m metaharness.cli demo --topology expanded --async-mode

  Verify: Both should produce structured output with runtime_status=runtime-ok and
  lifecycle states.

  ---
  ABACUS directed test tier

  The ABACUS extension has a focused directed suite that does not require a local
  ABACUS binary. Environment and execution behavior is covered with typed specs,
  patched probes, structured artifacts, and evidence-first validator fixtures.

  Run the full ABACUS directed suite from the repository root:
  PYTHONPATH=MHE/src pytest MHE/tests/test_metaharness_abacus_*.py -q

  Focused ABACUS files:
  PYTHONPATH=MHE/src pytest \
    MHE/tests/test_metaharness_abacus_manifest.py \
    MHE/tests/test_metaharness_abacus_gateway.py \
    MHE/tests/test_metaharness_abacus_environment.py \
    MHE/tests/test_metaharness_abacus_compiler.py \
    MHE/tests/test_metaharness_abacus_executor.py \
    MHE/tests/test_metaharness_abacus_validator.py \
    MHE/tests/test_metaharness_abacus_minimal_demo.py

  Coverage focus:
  - explicit manifest policy.sandbox / policy.credentials semantics
  - typed SCF / NSCF / relax / MD task boundaries
  - relax restart compatibility through typed restart_file_path
  - deterministic INPUT rendering for params and relax controls
  - required runtime asset grouping for pseudo, orbital, restart,
    charge-density, and pot_file inputs
  - family-aware executor artifact discovery under OUT.<suffix>/
  - evidence-first validator behavior, including strict NSCF running_nscf.log
    evidence and MD characteristic artifacts
  - protected validator governance outputs: issues, blocks_promotion,
    governance_state, ScoredEvidence, and canonical evidence_refs

  ---
  2. Validate Graph XML Files

  Structural validation only (checks XML shape):
  PYTHONPATH=MHE/src python -m metaharness.cli validate
  MHE/examples/graphs/minimal-happy-path.xml

  Structural + semantic validation (validates against manifests):
  PYTHONPATH=MHE/src python -m metaharness.cli validate \
    MHE/examples/graphs/minimal-expanded.xml \
    --manifests MHE/examples/manifests/baseline

  Test invalid graphs (expect non-zero exit codes):
  # Cycle detection (exit 3)
  PYTHONPATH=MHE/src python -m metaharness.cli validate
  MHE/examples/graphs/minimal-cycle.xml

  # Protected slot override (exit 3)
  PYTHONPATH=MHE/src python -m metaharness.cli validate
  MHE/examples/graphs/minimal-protected-slot-override.xml

  # Invalid contract (exit 3)
  PYTHONPATH=MHE/src python -m metaharness.cli validate
  MHE/examples/graphs/minimal-invalid-contract.xml

  ---
  3. Test the Safety Chain

  The four-tier pipeline: SandboxValidator → ABShadowTester → PolicyVeto →
  AutoRollback

  Test protected component enforcement by attempting to override a protected slot:
  - Edit a graph XML to bind policy.primary or observability.primary incorrectly
  - Run validation — it should reject with protected_slot_override issue

  Test hot-reload rollback by:
  - Starting a demo
  - Modifying the graph while running (if supported)
  - Observing that HotSwapOrchestrator checkpoints state before swapping

  ---
  4. Test the Optimizer (Self-Growth)

  Run benchmarks to exercise the optimizer:
  PYTHONPATH=MHE/src python -c "from metaharness.benchmarks import
  run_all_benchmarks; print(run_all_benchmarks())"

  Test optimizer triggers by:
  - Registering a metric trigger (e.g., task.latency.p95 > 250ms)
  - Observing whether OptimizerComponent.tick() emits events

  Test fitness evaluation by:
  - Submitting a proposal
  - Checking that FitnessEvaluator computes scores
  - Verifying convergence detection stops when TripleConvergence criteria are met

  ---
  5. Test Observability

  Generate traces and metrics:
  PYTHONPATH=MHE/src python -m metaharness.cli demo --topology expanded --trace-id
  my-test-run

  Check audit log:
  - Look for Merkle-anchored entries in the audit log
  - Verify entries include merkle_index and root hash

  Test counter-factual diagnosis by:
  - Running a failed candidate graph
  - Inspecting ObservabilityComponent for trajectory data

  ---
  6. Create and Load Custom Components

  Add a custom component (from EXTENSION_GUIDE.md):
  1. Subclass HarnessComponent
  2. Publish a manifest JSON with inputs, outputs, slots
  3. Wire it into a graph XML
  4. Validate and run

  Test template system:
  from metaharness.optimizer.templates.registry import TemplateRegistry
  from metaharness.optimizer.templates.slots import SlotFillingEngine

  registry = TemplateRegistry()
  # Register and instantiate templates
  engine = SlotFillingEngine()
  manifest, bindings = engine.instantiate(template, {"pool_size": 16})

  ---
  7. Test Version Compatibility

  Check API stability:
  PYTHONPATH=MHE/src python -m metaharness.cli version

  Test wire format compatibility:
  - Load older graph XML files (check schemaVersion attribute handling)
  - Verify manifests with different harness_version are rejected appropriately

  ---
  8. End-to-End Integration Scenarios
  Scenario: Happy path
  What to Test: Run minimal demo
  Expected Result: All lifecycle phases reach committed
  ────────────────────────────────────────
  Scenario: Cycle graph
  What to Test: Validate minimal-cycle.xml
  Expected Result: Exit code 3, cycle_detected issue
  ────────────────────────────────────────
  Scenario: Protected override
  What to Test: Validate minimal-protected-slot-override.xml
  Expected Result: Exit code 3, protected_slot_override
  ────────────────────────────────────────
  Scenario: Async routing
  What to Test: Run --async-mode
  Expected Result: Async event dispatch in trace
  ────────────────────────────────────────
  Scenario: Hot reload
  What to Test: Modify graph mid-flight
  Expected Result: Checkpoint saved, saga rollback available
  ────────────────────────────────────────
  Scenario: Optimizer convergence
  What to Test: Run benchmarks
  Expected Result: Fitness converges, budget limit respected
  ────────────────────────────────────────
  Scenario: Manifest version mismatch
  What to Test: Load manifest requiring newer harness
  Expected Result: Static validation rejects
  ---
  Summary Checklist

  - Minimal demo runs successfully
  - Expanded demo runs with async mode
  - Valid graphs pass structural validation
  - Valid graphs pass semantic validation
  - Cycle graph is rejected
  - Protected slot override is rejected
  - Invalid contracts detected
  - CLI exit codes are correct (0/2/3)
  - Observability traces generated
  - Audit log entries are Merkle-anchored
  - Benchmarks execute
  - Custom component can be loaded (if extending)
