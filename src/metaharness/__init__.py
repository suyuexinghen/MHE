"""Meta-Harness Engineering runtime."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

try:
    __version__ = _pkg_version("metaharness")
except PackageNotFoundError:  # pragma: no cover - source checkout fallback
    __version__ = "0.1.0"

__all__ = ["__version__"]
