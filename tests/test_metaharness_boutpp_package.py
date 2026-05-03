from __future__ import annotations

from metaharness_ext import boutpp


def test_package_exports():
    assert hasattr(boutpp, "BoutPPCompilerComponent")
    assert hasattr(boutpp, "BoutPPValidatorComponent")
    assert hasattr(boutpp, "BoutPPUsageValidationRunner")
