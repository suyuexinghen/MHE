from __future__ import annotations

CAP_ABACUS_ENV_PROBE = "abacus.environment.probe"
CAP_ABACUS_CASE_COMPILE = "abacus.compile.case"
CAP_ABACUS_SCF_RUN = "abacus.scf.run"
CAP_ABACUS_NSCF_RUN = "abacus.nscf.run"
CAP_ABACUS_RELAX_RUN = "abacus.relax.run"
CAP_ABACUS_MD_RUN = "abacus.md.run"
CAP_ABACUS_VALIDATE = "abacus.validation.check"

CANONICAL_CAPABILITIES = frozenset(
    {
        CAP_ABACUS_ENV_PROBE,
        CAP_ABACUS_CASE_COMPILE,
        CAP_ABACUS_SCF_RUN,
        CAP_ABACUS_NSCF_RUN,
        CAP_ABACUS_RELAX_RUN,
        CAP_ABACUS_MD_RUN,
        CAP_ABACUS_VALIDATE,
    }
)
