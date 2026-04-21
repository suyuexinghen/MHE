"""Lifecycle phases for Meta-Harness components."""

from enum import Enum


class ComponentPhase(str, Enum):
    """Canonical component lifecycle phases."""

    DISCOVERED = "discovered"
    VALIDATED_STATIC = "validated_static"
    ASSEMBLED = "assembled"
    VALIDATED_DYNAMIC = "validated_dynamic"
    ACTIVATED = "activated"
    COMMITTED = "committed"
    FAILED = "failed"
    SUSPENDED = "suspended"
