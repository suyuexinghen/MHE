from __future__ import annotations

CAP_QCOMPUTE_CASE_COMPILE = "qcompute.compile.case"
CAP_QCOMPUTE_ENV_PROBE = "qcompute.environment.probe"
CAP_QCOMPUTE_CIRCUIT_COMPILE = "qcompute.circuit.compile"
CAP_QCOMPUTE_CIRCUIT_RUN = "qcompute.circuit.run"
CAP_QCOMPUTE_RESULT_VALIDATE = "qcompute.result.validate"
CAP_QCOMPUTE_EVIDENCE_BUILD = "qcompute.evidence.build"
CAP_QCOMPUTE_POLICY_EVALUATE = "qcompute.policy.evaluate"
CAP_QCOMPUTE_GOVERNANCE_REVIEW = "qcompute.governance.review"
CAP_QCOMPUTE_STUDY_RUN = "qcompute.study.run"

CANONICAL_CAPABILITIES = frozenset(
    {
        CAP_QCOMPUTE_CASE_COMPILE,
        CAP_QCOMPUTE_ENV_PROBE,
        CAP_QCOMPUTE_CIRCUIT_COMPILE,
        CAP_QCOMPUTE_CIRCUIT_RUN,
        CAP_QCOMPUTE_RESULT_VALIDATE,
        CAP_QCOMPUTE_EVIDENCE_BUILD,
        CAP_QCOMPUTE_POLICY_EVALUATE,
        CAP_QCOMPUTE_GOVERNANCE_REVIEW,
        CAP_QCOMPUTE_STUDY_RUN,
    }
)
