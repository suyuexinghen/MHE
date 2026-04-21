from __future__ import annotations

PDE_GATEWAY_SLOT = "pde_gateway.primary"
PROBLEM_FORMULATOR_SLOT = "problem_formulator.primary"
METHOD_ROUTER_SLOT = "method_router.primary"
SOLVER_EXECUTOR_SLOT = "solver_executor.primary"
PHYSICS_VALIDATOR_SLOT = "physics_validator.primary"
EVIDENCE_MANAGER_SLOT = "evidence_manager.primary"
REFERENCE_SOLVER_SLOT = "reference_solver.primary"
EXPERIMENT_MEMORY_SLOT = "experiment_memory.primary"
KNOWLEDGE_ADAPTER_SLOT = "knowledge_adapter.primary"
ASSET_MEMORY_SLOT = "asset_memory.primary"
OBSERVABILITY_HUB_SLOT = "observability_hub.primary"
POLICY_GUARD_SLOT = "policy_guard.primary"

PROTECTED_SLOTS = frozenset(
    {
        EVIDENCE_MANAGER_SLOT,
        OBSERVABILITY_HUB_SLOT,
        POLICY_GUARD_SLOT,
        REFERENCE_SOLVER_SLOT,
    }
)
