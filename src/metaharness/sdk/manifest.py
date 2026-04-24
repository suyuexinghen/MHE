"""Manifest models for Meta-Harness components."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from metaharness.sdk.contracts import (
    CapabilityRequirement,
    EventPort,
    InputPort,
    OutputPort,
    SlotIntent,
)


class ComponentType(str, Enum):
    """Supported component taxonomies.

    The wiki / master roadmap uses ``CORE``, ``TEMPLATE``, ``META``, and
    ``GOVERNANCE``. ``CUSTOM`` is retained as a legacy alias for
    user-space/workspace components that do not fit any of the above.
    """

    CORE = "core"
    TEMPLATE = "template"
    META = "meta"
    GOVERNANCE = "governance"
    CUSTOM = "custom"


#: Backward-compatible alias.
ComponentKind = ComponentType


class CredentialPolicySpec(BaseModel):
    """Credential policy requirements declared by a component."""

    requires_subject: bool = False
    allow_inline_credentials: bool = True
    required_claims: list[str] = Field(default_factory=list)


class SandboxPolicySpec(BaseModel):
    """Sandbox policy requirements declared by a component."""

    tier: str | None = None


class SafetySpec(BaseModel):
    """Safety metadata for a component."""

    protected: bool = False
    mutability: str = "mutable"
    sandbox_profile: str | None = None
    hot_swap: bool = True


class PolicySpec(BaseModel):
    """Execution and promotion policies declared by a component."""

    credentials: CredentialPolicySpec = Field(default_factory=CredentialPolicySpec)
    sandbox: SandboxPolicySpec = Field(default_factory=SandboxPolicySpec)

    @model_validator(mode="after")
    def sync_legacy_sandbox_profile(self) -> "PolicySpec":
        return self


class ContractSpec(BaseModel):
    """Port and capability declarations."""

    inputs: list[InputPort] = Field(default_factory=list)
    outputs: list[OutputPort] = Field(default_factory=list)
    events: list[EventPort] = Field(default_factory=list)
    provides: list[CapabilityRequirement] = Field(default_factory=list)
    requires: list[CapabilityRequirement] = Field(default_factory=list)
    slots: list[SlotIntent] = Field(default_factory=list)


class DependencySpec(BaseModel):
    """Declared cross-component dependencies resolved during boot."""

    components: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)


class ComponentManifest(BaseModel):
    """Manifest describing a component implementation.

    Mirrors the wiki schema plus the extended roadmap fields: stable ``id``
    (defaults to ``name``), required ``harness_version``, optional ``deps`` /
    ``bins`` / ``env`` requirements, module-level ``provides`` / ``requires``
    capability strings used during dependency resolution, and backward-compatible
    execution policy declarations for credentials and sandboxing.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: str | None = None
    name: str
    version: str
    kind: ComponentType
    entry: str
    harness_version: str = ">=0.1.0"
    contracts: ContractSpec
    safety: SafetySpec = Field(default_factory=SafetySpec)
    policy: PolicySpec = Field(default_factory=PolicySpec)
    state_schema_version: int = 1
    deps: DependencySpec = Field(default_factory=DependencySpec)
    bins: list[str] = Field(default_factory=list)
    env: list[str] = Field(default_factory=list)
    provides: list[str] = Field(default_factory=list)
    requires: list[str] = Field(default_factory=list)
    default_impl: str | None = None
    enabled: bool = True

    @model_validator(mode="after")
    def sync_legacy_policy_fields(self) -> "ComponentManifest":
        if self.policy.sandbox.tier is None and self.safety.sandbox_profile is not None:
            self.policy.sandbox.tier = self.safety.sandbox_profile
        return self

    def resolved_id(self) -> str:
        """Return the stable component id (falls back to ``name``)."""

        return self.id or self.name

    def all_provided_capabilities(self) -> list[str]:
        """Union of module-level ``provides`` and contract-level provides."""

        contract = [c.name for c in self.contracts.provides]
        return sorted(set(self.provides) | set(contract))

    def all_required_capabilities(self) -> list[str]:
        """Union of module-level ``requires`` and contract-level requires."""

        contract = [c.name for c in self.contracts.requires]
        return sorted(set(self.requires) | set(contract))
