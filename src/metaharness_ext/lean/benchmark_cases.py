from __future__ import annotations

from typing import Any

from metaharness.benchmark_drivers.models import BenchmarkCaseSpec, MetricReference

LEAN_TRUE_SOURCE = """theorem main : True := by
  trivial
"""

LEAN_IMPLICATION_SOURCE = """theorem main (p q : Prop) (hp : p) (hpq : p -> q) : q := by
  exact hpq hp
"""

LEAN_CONJUNCTION_SOURCE = """theorem main (p q : Prop) (h : p ∧ q) : q ∧ p := by
  exact And.intro h.right h.left
"""

LEAN_NEGATION_SOURCE = """theorem main (p q : Prop) (hpq : p -> q) (hnq : ¬ q) : ¬ p := by
  intro hp
  exact hnq (hpq hp)
"""

LEAN_EXISTS_SWAP_SOURCE = """theorem main (α : Type) (p q : α -> Prop) (h : ∃ x, p x ∧ q x) : ∃ x, q x ∧ p x := by
  cases h with
  | intro x hx =>
      exact Exists.intro x (And.intro hx.right hx.left)
"""

LEAN_REPAIR_SOURCE = """theorem main : True := by
  trivial
"""

LEAN_SORRY_STRESS_SOURCE = """theorem main : True := by
  trivial
"""

LEAN_MATHLIB_SENTINEL_SOURCE = """import Mathlib

theorem main (n : Nat) : n + 0 = n := by
  simpa using Nat.add_zero n
"""

LEAN_PROJECT_HELPER_SOURCE = """theorem helper (p q : Prop) (hp : p) (hpq : p -> q) : q := by
  exact hpq hp
"""

LEAN_PROJECT_MAIN_SOURCE = """import Helper

theorem main (p q r : Prop) (hp : p) (hpq : p -> q) (hqr : q -> r) : r := by
  exact hqr (helper p q hp hpq)
"""

LEAN_BLUEPRINT_DOMAIN_SOURCE = """structure ProofNode (proposition : Prop) where
  proof : proposition
"""

LEAN_BLUEPRINT_PROOF_SOURCE = """import Blueprint.Domain

def swapNode (p q : Prop) (node : ProofNode (p ∧ q)) : ProofNode (q ∧ p) :=
  { proof := And.intro node.proof.right node.proof.left }
"""

LEAN_BLUEPRINT_MAIN_SOURCE = """import Blueprint.Proof

theorem main (p q : Prop) (h : p ∧ q) : q ∧ p := by
  exact (swapNode p q { proof := h }).proof
"""

EXPECTED_METRICS = [
    "environment_ready",
    "proof_status",
    "sorry_count",
    "error_count",
    "elapsed_seconds",
]

REFERENCE_METRICS = {
    "environment_ready": MetricReference(value=1.0, tolerance=0.0),
    "proof_status": MetricReference(value=1.0, tolerance=0.0),
    "sorry_count": MetricReference(value=0.0, tolerance=0.0),
    "error_count": MetricReference(value=0.0, tolerance=0.0),
}

CLAIM_BOUNDARY = (
    "formal proof workflow evidence only; no theorem-discovery or solver-superiority claim"
)
TOOLCHAIN = "leanprover/lean4:v4.14.0"
CURATED_CASE_REVIEW = {
    "review_status": "lean_validated_engineer_curated",
    "external_review_required": True,
    "external_review_manifest": "lean_human_review_manifest.json",
    "human_math_review": "pending_external_signoff",
}


def _lean_case(
    *,
    case_id: str,
    description: str,
    lean_source: str,
    target_statement: str,
    metadata: dict[str, Any] | None = None,
    project_files: dict[str, str] | None = None,
    capability_gated: bool = False,
) -> BenchmarkCaseSpec:
    return BenchmarkCaseSpec(
        case_id=case_id,
        suite="lean-proof",
        task_family="lean_formal_proof",
        description=description,
        required_capabilities=["lean.execute.proof", "lean.validate.result"],
        source_reference={
            "theorem": target_statement,
            "toolchain": TOOLCHAIN,
        },
        expected_metrics=EXPECTED_METRICS,
        reference_metrics=REFERENCE_METRICS,
        problem_definition={
            "target_file": "Main.lean",
            "target_lemma": "main",
            "target_statement": target_statement,
            "lean_source": lean_source,
            "project_files": project_files or {},
            "toolchain": TOOLCHAIN,
        },
        capability_gated=capability_gated,
        metadata={
            "proposal_contract": "lean_proof_source_v1",
            "claim_boundary": CLAIM_BOUNDARY,
            "direct_fake_fallback_enabled": True,
            **(metadata or {}),
        },
    )


def lean_proof_case_catalog() -> dict[str, BenchmarkCaseSpec]:
    cases = [
        _lean_case(
            case_id="simple-true-proof",
            description="Lean theorem proof smoke for MHE gateway, direct Claude, and agent-mediated workflows.",
            lean_source=LEAN_TRUE_SOURCE,
            target_statement="theorem main : True",
            metadata={"theorem_family": "smoke"},
        ),
        _lean_case(
            case_id="implication-chain-proof",
            description="Lean proof challenge requiring use of assumptions and implication application.",
            lean_source=LEAN_IMPLICATION_SOURCE,
            target_statement="theorem main (p q : Prop) (hp : p) (hpq : p -> q) : q",
            metadata={
                "challenge_kind": "positive_nontrivial_proof",
                "theorem_family": "propositional_implication",
            },
        ),
        _lean_case(
            case_id="conjunction-swap-proof",
            description="Lean proof challenge requiring decomposition and reconstruction of a conjunction.",
            lean_source=LEAN_CONJUNCTION_SOURCE,
            target_statement="theorem main (p q : Prop) (h : p ∧ q) : q ∧ p",
            metadata={
                "challenge_kind": "positive_nontrivial_proof",
                "theorem_family": "propositional_conjunction",
            },
        ),
        _lean_case(
            case_id="negation-contrapositive-proof",
            description="Curated Lean proof challenge requiring implication use under negation introduction.",
            lean_source=LEAN_NEGATION_SOURCE,
            target_statement="theorem main (p q : Prop) (hpq : p -> q) (hnq : ¬ q) : ¬ p",
            metadata={
                "challenge_kind": "curated_nontrivial_proof",
                "theorem_family": "propositional_negation",
                **CURATED_CASE_REVIEW,
            },
        ),
        _lean_case(
            case_id="exists-conjunction-swap-proof",
            description="Curated Lean proof challenge requiring existential elimination and conjunction reconstruction.",
            lean_source=LEAN_EXISTS_SWAP_SOURCE,
            target_statement="theorem main (α : Type) (p q : α -> Prop) (h : ∃ x, p x ∧ q x) : ∃ x, q x ∧ p x",
            metadata={
                "challenge_kind": "curated_nontrivial_proof",
                "theorem_family": "first_order_exists",
                **CURATED_CASE_REVIEW,
            },
        ),
        _lean_case(
            case_id="malformed-proposal-repair",
            description="Controlled malformed proposal case where direct fails contract validation and agent repairs from case defaults.",
            lean_source=LEAN_REPAIR_SOURCE,
            target_statement="theorem main : True",
            metadata={
                "challenge_kind": "malformed_proposal_repair",
                "theorem_family": "contract_repair",
                "direct_fake_fallback_enabled": False,
                "agent_repair_expected": True,
            },
        ),
        _lean_case(
            case_id="underspecified-real-claude-stress",
            description="Stress case where the direct prompt asks for a proof idea instead of the proposal contract, while the agent lane can repair to the contract.",
            lean_source=LEAN_NEGATION_SOURCE,
            target_statement="theorem main (p q : Prop) (hpq : p -> q) (hnq : ¬ q) : ¬ p",
            metadata={
                "challenge_kind": "real_claude_underspecified_prompt_stress",
                "theorem_family": "stress_prompt",
                "direct_fake_fallback_enabled": False,
                "agent_repair_expected": True,
                "direct_prompt_style": "natural_language_noncontract",
                "agent_prompt_style": "contract_repair_from_stress",
            },
        ),
        _lean_case(
            case_id="malformed-json-real-claude-stress",
            description="Stress case where the direct prompt asks for JSON that omits required Lean source fields.",
            lean_source=LEAN_REPAIR_SOURCE,
            target_statement="theorem main : True",
            metadata={
                "challenge_kind": "real_claude_malformed_json_stress",
                "theorem_family": "stress_prompt",
                "direct_fake_fallback_enabled": False,
                "agent_repair_expected": True,
                "direct_prompt_style": "json_missing_lean_source",
                "agent_prompt_style": "contract_repair_from_stress",
            },
        ),
        _lean_case(
            case_id="sorry-proof-real-claude-stress",
            description="Stress case where the direct prompt asks for a proposal containing sorry, which must fail the contract.",
            lean_source=LEAN_SORRY_STRESS_SOURCE,
            target_statement="theorem main : True",
            metadata={
                "challenge_kind": "real_claude_sorry_contract_stress",
                "theorem_family": "stress_prompt",
                "direct_fake_fallback_enabled": False,
                "agent_repair_expected": True,
                "direct_prompt_style": "json_with_sorry_source",
                "agent_prompt_style": "contract_repair_from_stress",
            },
        ),
        _lean_case(
            case_id="project-helper-chain-proof",
            description="Project-scale Lean proof fixture with a helper theorem imported by the target proof.",
            lean_source=LEAN_PROJECT_MAIN_SOURCE,
            target_statement="theorem main (p q r : Prop) (hp : p) (hpq : p -> q) (hqr : q -> r) : r",
            metadata={
                "challenge_kind": "project_scale_positive_proof",
                "theorem_family": "project_helper",
            },
            project_files={"Helper.lean": LEAN_PROJECT_HELPER_SOURCE},
        ),
        _lean_case(
            case_id="blueprint-structure-project-proof",
            description="Blueprint-style Lean project fixture with domain and proof modules feeding the target theorem.",
            lean_source=LEAN_BLUEPRINT_MAIN_SOURCE,
            target_statement="theorem main (p q : Prop) (h : p ∧ q) : q ∧ p",
            metadata={
                "challenge_kind": "blueprint_style_project_fixture",
                "theorem_family": "blueprint_project",
                "blueprint_style": True,
                "mathlib_scale": False,
                "mathlib_scale_claim": "not_claimed",
            },
            project_files={
                "Blueprint/Domain.lean": LEAN_BLUEPRINT_DOMAIN_SOURCE,
                "Blueprint/Proof.lean": LEAN_BLUEPRINT_PROOF_SOURCE,
            },
        ),
        _lean_case(
            case_id="mathlib-add-zero-sentinel",
            description="Mathlib dependency-gated sentinel that records missing Mathlib-scale capability instead of overclaiming coverage.",
            lean_source=LEAN_MATHLIB_SENTINEL_SOURCE,
            target_statement="theorem main (n : Nat) : n + 0 = n",
            metadata={
                "challenge_kind": "mathlib_dependency_sentinel",
                "theorem_family": "mathlib_sentinel",
                "requires_mathlib": True,
                "mathlib_scale": True,
                "mathlib_scale_claim": "dependency_gated_not_promoted",
                "promotion_ready": False,
            },
            capability_gated=True,
        ),
    ]
    return {case.case_id: case for case in cases}


def get_lean_proof_cases(case_ids: list[str] | None = None) -> list[BenchmarkCaseSpec]:
    catalog = lean_proof_case_catalog()
    if not case_ids:
        return list(catalog.values())
    return [catalog[case_id] for case_id in case_ids]
