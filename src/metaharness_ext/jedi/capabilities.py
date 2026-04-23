from __future__ import annotations

CAP_JEDI_CASE_COMPILE = "jedi.compile.case"
CAP_JEDI_ENV_PROBE = "jedi.environment.probe"
CAP_JEDI_SCHEMA = "jedi.schema.generate"
CAP_JEDI_VALIDATE_ONLY = "jedi.validate_only.run"
CAP_JEDI_REAL_RUN = "jedi.real_run.run"
CAP_JEDI_VALIDATE = "jedi.validation.check"
CAP_JEDI_SMOKE_POLICY = "jedi.smoke.policy"
CAP_JEDI_DIAGNOSTICS = "jedi.diagnostics.collect"
CAP_JEDI_STUDY = "jedi.study.run"

CANONICAL_CAPABILITIES = frozenset(
    {
        CAP_JEDI_CASE_COMPILE,
        CAP_JEDI_ENV_PROBE,
        CAP_JEDI_SCHEMA,
        CAP_JEDI_VALIDATE_ONLY,
        CAP_JEDI_REAL_RUN,
        CAP_JEDI_VALIDATE,
        CAP_JEDI_SMOKE_POLICY,
        CAP_JEDI_DIAGNOSTICS,
        CAP_JEDI_STUDY,
    }
)
