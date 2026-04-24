"""Focused tests for the protected identity boundary integration."""

from __future__ import annotations

import asyncio

import pytest

from metaharness.components.gateway import GatewayComponent
from metaharness.components.policy import PolicyComponent
from metaharness.identity import InMemoryIdentityBoundary
from metaharness.sdk.manifest import ComponentManifest, ComponentType, ContractSpec
from metaharness.sdk.runtime import ComponentRuntime


def _gateway_manifest(**policy: object) -> ComponentManifest:
    return ComponentManifest(
        name="gateway",
        version="0.1.0",
        kind=ComponentType.CORE,
        entry="metaharness.components.gateway:GatewayComponent",
        contracts=ContractSpec(),
        policy=policy,
    )


def test_gateway_issues_sanitized_identity_payload() -> None:
    boundary = InMemoryIdentityBoundary()
    gateway = GatewayComponent(manifest=_gateway_manifest())
    asyncio.run(gateway.activate(ComponentRuntime(identity_boundary=boundary)))

    payload = gateway.issue_task(
        "fetch dataset",
        subject_id="service:gateway",
        credentials={"api_key": "top-secret", "session": "token-1"},
    )

    assert payload["task"] == "fetch dataset"
    assert payload["subject"] == "service:gateway"
    assert payload["attestation"]["subject"]["subject_id"] == "service:gateway"
    assert "credentials" not in payload
    assert "api_key" not in payload
    assert boundary.credentials_for(payload["attestation"]["attestation_id"]) == {
        "api_key": "top-secret",
        "session": "token-1",
    }


def test_policy_records_attestation_without_exposing_credentials() -> None:
    boundary = InMemoryIdentityBoundary()
    gateway = GatewayComponent(manifest=_gateway_manifest())
    policy = PolicyComponent()
    runtime = ComponentRuntime(identity_boundary=boundary)
    asyncio.run(gateway.activate(runtime))
    asyncio.run(policy.activate(runtime))

    payload = gateway.issue_task(
        "approve access",
        subject_id="user:alice",
        credentials={"refresh_token": "secret-refresh"},
    )
    record = policy.record(
        "allow",
        payload["subject"],
        attestation_id=payload["attestation"]["attestation_id"],
    )

    assert record == {
        "decision": "allow",
        "subject": "user:alice",
        "attestation_id": payload["attestation"]["attestation_id"],
        "credential_bound": "true",
    }
    assert "refresh_token" not in record.values()
    assert boundary.credentials_for(payload["attestation"]["attestation_id"]) == {
        "refresh_token": "secret-refresh"
    }


def test_gateway_enforces_subject_and_claim_requirements() -> None:
    boundary = InMemoryIdentityBoundary()
    gateway = GatewayComponent(
        manifest=_gateway_manifest(
            credentials={
                "requires_subject": True,
                "required_claims": ["scope"],
            }
        )
    )
    asyncio.run(gateway.activate(ComponentRuntime(identity_boundary=boundary)))

    with pytest.raises(ValueError, match="requires subject_id"):
        gateway.issue_task("fetch dataset")

    with pytest.raises(ValueError, match="missing required claims: scope"):
        gateway.issue_task("fetch dataset", subject_id="service:gateway")


def test_gateway_rejects_inline_credentials_when_policy_forbids_them() -> None:
    boundary = InMemoryIdentityBoundary()
    gateway = GatewayComponent(
        manifest=_gateway_manifest(credentials={"allow_inline_credentials": False})
    )
    asyncio.run(gateway.activate(ComponentRuntime(identity_boundary=boundary)))

    with pytest.raises(ValueError, match="forbids inline credentials"):
        gateway.issue_task(
            "fetch dataset",
            subject_id="service:gateway",
            credentials={"api_key": "secret"},
        )
