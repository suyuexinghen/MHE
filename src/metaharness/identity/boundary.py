"""Minimal in-memory identity boundary for protected component edges."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import uuid4


@dataclass(slots=True)
class SubjectIdentity:
    """Public subject identity carried across normal component flows."""

    subject_id: str
    issuer: str = "mhe.identity.memory"
    claims: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class IdentityAttestation:
    """Attestation that binds a subject to optional protected credentials."""

    attestation_id: str
    subject: SubjectIdentity

    def public_view(self) -> dict[str, Any]:
        """Return the non-sensitive attestation payload safe for normal routing."""

        return {
            "attestation_id": self.attestation_id,
            "subject": asdict(self.subject),
        }


class InMemoryIdentityBoundary:
    """Separates sensitive credentials from ordinary component payloads."""

    def __init__(self) -> None:
        self._credentials: dict[str, dict[str, str]] = {}

    def issue_attestation(
        self,
        subject_id: str,
        *,
        claims: dict[str, str] | None = None,
        credentials: dict[str, str] | None = None,
    ) -> IdentityAttestation:
        """Create an attestation and retain any sensitive credentials privately."""

        attestation = IdentityAttestation(
            attestation_id=f"att-{uuid4().hex}",
            subject=SubjectIdentity(subject_id=subject_id, claims=dict(claims or {})),
        )
        if credentials:
            self._credentials[attestation.attestation_id] = dict(credentials)
        return attestation

    def expose_payload(
        self,
        payload: dict[str, Any],
        *,
        attestation: IdentityAttestation,
    ) -> dict[str, Any]:
        """Return a sanitized payload with public identity material only."""

        exposed = dict(payload)
        exposed["subject"] = attestation.subject.subject_id
        exposed["attestation"] = attestation.public_view()
        return exposed

    def credentials_for(self, attestation_id: str) -> dict[str, str] | None:
        """Return protected credentials for a previously issued attestation."""

        credentials = self._credentials.get(attestation_id)
        if credentials is None:
            return None
        return dict(credentials)
