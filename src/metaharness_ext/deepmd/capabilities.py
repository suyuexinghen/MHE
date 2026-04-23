from __future__ import annotations

CAP_DEEPMD_CASE_COMPILE = "deepmd.compile.case"
CAP_DEEPMD_ENV_PROBE = "deepmd.environment.probe"
CAP_DEEPMD_TRAIN_RUN = "deepmd.train.run"
CAP_DEEPMD_MODEL_FREEZE = "deepmd.model.freeze"
CAP_DEEPMD_MODEL_TEST = "deepmd.model.test"
CAP_DEEPMD_MODEL_COMPRESS = "deepmd.model.compress"
CAP_DEEPMD_MODEL_DEVI = "deepmd.model.devi"
CAP_DEEPMD_NEIGHBOR_STAT = "deepmd.dataset.neighbor_stat"
CAP_DPGEN_RUN = "deepmd.dpgen.run"
CAP_DPGEN_AUTOTEST = "deepmd.dpgen.autotest"
CAP_DEEPMD_VALIDATE = "deepmd.validation.check"
CAP_DEEPMD_STUDY = "deepmd.study.run"

CANONICAL_CAPABILITIES = frozenset(
    {
        CAP_DEEPMD_CASE_COMPILE,
        CAP_DEEPMD_ENV_PROBE,
        CAP_DEEPMD_TRAIN_RUN,
        CAP_DEEPMD_MODEL_FREEZE,
        CAP_DEEPMD_MODEL_TEST,
        CAP_DEEPMD_MODEL_COMPRESS,
        CAP_DEEPMD_MODEL_DEVI,
        CAP_DEEPMD_NEIGHBOR_STAT,
        CAP_DPGEN_RUN,
        CAP_DPGEN_AUTOTEST,
        CAP_DEEPMD_VALIDATE,
        CAP_DEEPMD_STUDY,
    }
)
