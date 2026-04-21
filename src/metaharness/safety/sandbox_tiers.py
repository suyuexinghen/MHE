"""Sandbox tiers and risk-based selector.

The roadmap mandates three sandbox tiers (V8/WASM, gVisor, Firecracker)
plus a selector that chooses one given the proposal's risk profile.
Real sandboxing is environment-specific; this module provides the
abstraction with a safe in-process fallback so callers can ship a
uniform interface and plug real backends in later.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol


class RiskTier(str, Enum):
    """Risk tier assessed for a proposal or component."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SandboxTier(str, Enum):
    """Available sandbox tiers, ordered by isolation strength."""

    V8_WASM = "v8_wasm"
    GVISOR = "gvisor"
    FIRECRACKER = "firecracker"


_TIER_ORDER: dict[SandboxTier, int] = {
    SandboxTier.V8_WASM: 0,
    SandboxTier.GVISOR: 1,
    SandboxTier.FIRECRACKER: 2,
}


@dataclass(slots=True)
class SandboxExecutionResult:
    """Structured result from a sandbox execution attempt."""

    tier: SandboxTier
    success: bool
    output: Any = None
    error: str | None = None
    metrics: dict[str, Any] | None = None


class SandboxAdapter(Protocol):
    """Protocol implemented by all sandbox backends."""

    tier: SandboxTier

    def execute(
        self, code: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> SandboxExecutionResult: ...


@dataclass(slots=True)
class InProcessAdapter:
    """Fallback adapter that runs callables directly in-process.

    Used when a real sandbox backend is not configured. It is *not* a
    security boundary - callers must still match the tier's risk profile.
    """

    tier: SandboxTier = SandboxTier.V8_WASM

    def execute(
        self, code: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> SandboxExecutionResult:
        try:
            output = code(*args, **kwargs)
            return SandboxExecutionResult(tier=self.tier, success=True, output=output)
        except Exception as exc:  # pragma: no cover - defensive
            return SandboxExecutionResult(tier=self.tier, success=False, error=str(exc))


def v8_wasm_adapter() -> SandboxAdapter:
    """Return the default V8/WASM-tier adapter (in-process fallback)."""

    return InProcessAdapter(tier=SandboxTier.V8_WASM)


def gvisor_adapter() -> SandboxAdapter:
    """Return the default gVisor-tier adapter (in-process fallback)."""

    return InProcessAdapter(tier=SandboxTier.GVISOR)


def firecracker_adapter() -> SandboxAdapter:
    """Return the default Firecracker-tier adapter (in-process fallback)."""

    return InProcessAdapter(tier=SandboxTier.FIRECRACKER)


class RiskTierSelector:
    """Maps a :class:`RiskTier` to the minimum required sandbox tier.

    Callers pass the adapters they have available; the selector picks
    the cheapest one that meets or exceeds the mandated floor. If no
    adapter qualifies, an error is raised so the proposal never runs.
    """

    def __init__(
        self,
        *,
        mapping: dict[RiskTier, SandboxTier] | None = None,
        adapters: list[SandboxAdapter] | None = None,
    ) -> None:
        self.mapping: dict[RiskTier, SandboxTier] = mapping or {
            RiskTier.LOW: SandboxTier.V8_WASM,
            RiskTier.MEDIUM: SandboxTier.GVISOR,
            RiskTier.HIGH: SandboxTier.FIRECRACKER,
            RiskTier.CRITICAL: SandboxTier.FIRECRACKER,
        }
        self.adapters: list[SandboxAdapter] = list(adapters or [])

    def register(self, adapter: SandboxAdapter) -> None:
        self.adapters.append(adapter)

    def required_tier(self, risk: RiskTier) -> SandboxTier:
        return self.mapping[risk]

    def select(self, risk: RiskTier) -> SandboxAdapter:
        required = self.required_tier(risk)
        floor_rank = _TIER_ORDER[required]
        eligible = [a for a in self.adapters if _TIER_ORDER[a.tier] >= floor_rank]
        if not eligible:
            raise LookupError(
                f"No sandbox adapter satisfies floor tier {required.value} for risk {risk.value}"
            )
        # Prefer the cheapest tier that still satisfies the floor.
        eligible.sort(key=lambda a: _TIER_ORDER[a.tier])
        return eligible[0]

    def run(
        self,
        risk: RiskTier,
        code: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> SandboxExecutionResult:
        return self.select(risk).execute(code, *args, **kwargs)
