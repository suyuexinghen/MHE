# Optimizer Extension Points

The `metaharness.optimizer` package is built as a set of composable
units so operators can plug in their own strategies without touching
the core optimizer component. This document lists every extension
point and shows how to hook into it.

## 1. Triggers

`LayeredTriggerSystem` owns the five trigger layers:
`METRIC`, `EVENT`, `SCHEDULE`, `MANUAL`, and `COMPOSITE`. Register a
trigger once and the optimizer's `tick()` method evaluates it every
time the clock advances.

```python
from metaharness.optimizer.triggers import (
    LayeredTriggerSystem,
    Trigger,
    TriggerKind,
    TriggerThreshold,
)

triggers = LayeredTriggerSystem()
triggers.register(
    Trigger(
        trigger_id="latency-p95",
        kind=TriggerKind.METRIC,
        metric_name="task.latency.p95",
        threshold=TriggerThreshold(max_value=250.0, min_interval_seconds=60.0),
    )
)
```

Triggers can be disabled at runtime with
`triggers.set_enabled("latency-p95", False)`; they keep state so a
schedule trigger never fires twice inside its interval.

## 2. Proposer / Evaluator

`OptimizerComponent` takes optional `proposer` and `evaluator`
callables. Replace either to swap in a bespoke strategy while keeping
the governance-mediated commit semantics.

```python
from metaharness.components.optimizer import OptimizerComponent

def my_proposer(opt, observations):
    ...
    return [proposal_1, proposal_2]

def my_evaluator(opt, proposal, observations):
    ...
    return ProposalEvaluation(proposal_id=proposal.proposal_id, score=0.8)

optimizer = OptimizerComponent(proposer=my_proposer, evaluator=my_evaluator)
```

## 3. Fitness Evaluators

`FitnessEvaluator` maps a *kind* identifier to a callable returning
`RewardComponents`. Add new evaluators for new proposal shapes:

```python
from metaharness.optimizer.fitness import FitnessEvaluator, RewardComponents

fitness = FitnessEvaluator()

def score_task_result(result):
    return RewardComponents(
        success=result["passed"],
        efficiency=1.0 / max(result["latency"], 1e-3),
        safety=result["safety_score"],
    )

fitness.register("task_result", score_task_result)
```

`composite_fitness(components, weights=...)` converts
`RewardComponents` into a scalar; override the weights to bias the
optimizer toward specific signals.

## 4. Convergence & Dead-End

`TripleConvergence`, `DeadEndDetector`, and `NonMarkovianGuard` are
the three convergence primitives. They are data classes so you can
override any field per optimizer instance:

```python
optimizer.convergence = TripleConvergence(
    fitness_window=10,
    fitness_epsilon=1e-4,
    budget_limit=500,
    safety_floor=0.98,
    require_all=True,
)
```

For multi-branch search, create one `DeadEndDetector` with the
required `window` and call `record(path_id, score)` after each
iteration.

## 5. Search Strategies

`LocalParameterSearch` (Phase A), `TopologyTemplateSearch` (Phase B),
and `ConstrainedSynthesis` (Phase C) are standalone engines. They
share no mutable state, so you can mix and match them freely.

- **Phase A:** provide a `schema` dict mapping parameter names to
  iterables of candidate values plus an objective callable.
- **Phase B:** pass a `ContractPruner` instance; the search uses it to
  enumerate only legal `add_edge` / `remove_edge` / `swap_template`
  moves.
- **Phase C:** inject a `planner`, `applier`, `constraints`, and
  `scorer`. Plans that violate any constraint are silently dropped.

Use `BayesianOptimizer` when the action space is small and discrete,
and `RLEnhancement` when you want a fast-adapting softmax policy
alongside the search.

## 6. Action Space Funnel

`ActionSpaceFunnel` composes four pipelines:

1. `generators` — produce raw candidates.
2. `structural_filters` — drop malformed actions.
3. `contract_filters` — drop actions that break contracts
   (typically wraps `ContractPruner.legal_targets`).
4. `budget_filters` — drop actions that exceed resource budgets.

Set `funnel.scorer` to rank survivors. The funnel produces a sorted
list of `CandidateAction` objects; the top-N can be fed into
`MutationSubmitter.submit`.

## 7. Templates & Codegen

- **Registry:** `TemplateRegistry.register` / `list` / `find_by_kind`.
- **Slot-filling:** `SlotFillingEngine.bind` and `instantiate`.
- **Codegen:** `CodegenPipeline.render(...).write_all(...)`.
- **Migrations:** `MigrationAdapterSystem.register(MigrationAdapter(...))`
  then `system.migrate(component_id, from_version, to_version, state)`.

All four units are independent: you can adopt the migration adapter
system without also pulling in the codegen pipeline, for example.

## 8. State Encoder

`GINEncoder.encode(snapshot)` produces deterministic per-node and
graph-level embeddings. The encoder is pure Python; override `dim`,
`layers`, or `epsilon` to match the scale of your graphs. Wrap your
own encoder by subclassing and swapping the `_hash_vector` method.

## 9. Self-Growth Loop

A typical self-growth iteration using the extension surface:

```python
events = optimizer.tick(context)  # 1. triggers
if not events:
    return
batch = optimizer.propose_batch()
for proposal in batch:
    evaluation = optimizer.evaluate(proposal)
    optimizer.record_fitness(evaluation.score)
convergence = optimizer.check_convergence(budget_used=..., safety_score=...)
if convergence.converged:
    return
best = max(batch, key=lambda p: optimizer.evaluate(p).score)
record = optimizer.commit(best, submitter)
```

This loop preserves the invariant that the optimizer only writes via
`MutationSubmitter`, even when all other extension points have been
swapped for custom implementations.

## 10. Domain-Specific Optimizer Interactions

When the optimizer operates over domain-specific extensions such as
`metaharness_ext.nektar` or `metaharness_ext.ai4pde`, the same
extension points apply, but the action space and fitness signals are
domain-specific.

### 10.1 Nektar++ action space example

For the Nektar extension, optimizer proposals typically target:

- `NektarMutationAxis` values (e.g., `num_modes` sweeps)
- `postprocess_plan` composition changes
- Solver parameter overrides in `NektarProblemSpec.parameters`

Fitness evaluators can consume:

- `ConvergenceStudyReport.converged`
- `ConvergenceStudyReport.observed_order`
- `NektarValidationReport.passed`
- `ErrorSummary.max_l2`

### 10.2 AI4PDE action space example

For the AI4PDE extension, optimizer proposals typically target:

- `PDEPlan.parameter_overrides` (loss weights, collocation strategy)
- `PDEPlan.selected_method` (solver family switching)
- Template selection from `PDETemplate.catalog`

Fitness evaluators can consume:

- `ValidationBundle.next_action` (`ACCEPT`, `RETRY`, `ESCALATE`, `REPLAN`)
- `ValidationBundle.residual_metrics`
- `ScientificEvidenceBundle.artifact_hashes`
- `BudgetRecord` fields for resource-aware optimization

### 10.3 Shared constraint

Regardless of domain, the optimizer must still:

- respect `PROTECTED_SLOTS` declared by each extension
- route proposals through `MutationSubmitter`
- honor the staged lifecycle (candidate → validate → commit)

Both `metaharness_ext.nektar.slots.PROTECTED_SLOTS` and
`metaharness_ext.ai4pde.slots.PROTECTED_SLOTS` should be consulted
when building a `ContractPruner` for domain-specific optimization.
