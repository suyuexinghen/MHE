from __future__ import annotations

CAP_LEAN_ORCHESTRATE_WORKFLOW = "lean.orchestrate.workflow"
CAP_LEAN_PROBE_ENVIRONMENT = "lean.probe.environment"
CAP_LEAN_COMPILE_BLUEPRINT = "lean.compile.blueprint"
CAP_LEAN_PREPARE_WORKSPACE = "lean.prepare.workspace"
CAP_LEAN_EXECUTE_PROOF = "lean.execute.proof"
CAP_LEAN_VALIDATE_RESULT = "lean.validate.result"
CAP_LEAN_EVALUATE_POLICY = "lean.evaluate.policy"
CAP_LEAN_BUILD_EVIDENCE = "lean.build.evidence"

CANONICAL_CAPABILITIES = frozenset(
    {
        CAP_LEAN_ORCHESTRATE_WORKFLOW,
        CAP_LEAN_PROBE_ENVIRONMENT,
        CAP_LEAN_COMPILE_BLUEPRINT,
        CAP_LEAN_PREPARE_WORKSPACE,
        CAP_LEAN_EXECUTE_PROOF,
        CAP_LEAN_VALIDATE_RESULT,
        CAP_LEAN_EVALUATE_POLICY,
        CAP_LEAN_BUILD_EVIDENCE,
    }
)
