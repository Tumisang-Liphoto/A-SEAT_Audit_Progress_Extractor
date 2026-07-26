from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit

import keyring
from keyring.errors import KeyringError

from src.services.aseat_url_service import ASeatUrlService


@dataclass(frozen=True)
class CredentialReference:
    """Identifies one stored A-SEAT credential."""

    profile_id: str
    username: str
    service_name: str
    account_name: str


class CredentialService:
    """Store A-SEAT passwords in Windows Credential Manager."""

    SERVICE_PREFIX = "A-SEAT Utility"

    @classmethod
    def _normalised_host(cls, configured_url: str) -> str:
        resolved = ASeatUrlService.resolve(configured_url)
        parsed = urlsplit(resolved.origin_url)

        host = parsed.hostname or ""

        if parsed.port is not None:
            host = f"{host}:{parsed.port}"

        return host.lower()

    @classmethod
    def build_reference(
        cls,
        *,
        profile_id: str,
        configured_url: str,
        username: str,
    ) -> CredentialReference:
        """Create a stable credential reference."""

        clean_profile_id = profile_id.strip()
        clean_username = username.strip()

        if not clean_profile_id:
            raise ValueError("A connection profile ID is required.")

        if not clean_username:
            raise ValueError("A username is required.")

        host = cls._normalised_host(configured_url)

        service_name = f"{cls.SERVICE_PREFIX}:{host}"
        account_name = f"{clean_profile_id}:{clean_username}"

        return CredentialReference(
            profile_id=clean_profile_id,
            username=clean_username,
            service_name=service_name,
            account_name=account_name,
        )

    def store_password(
        self,
        *,
        profile_id: str,
        configured_url: str,
        username: str,
        password: str,
    ) -> CredentialReference:
        """Store a password securely for the current Windows user."""

        if not password:
            raise ValueError("A password is required.")

        reference = self.build_reference(
            profile_id=profile_id,
            configured_url=configured_url,
            username=username,
        )

        try:
            keyring.set_password(
                reference.service_name,
                reference.account_name,
                password,
            )
        except KeyringError as error:
            raise RuntimeError(
                "Windows Credential Manager could not store the "
                "A-SEAT password."
            ) from error

        return reference

    def retrieve_password(
        self,
        *,
        profile_id: str,
        configured_url: str,
        username: str,
    ) -> str | None:
        """Retrieve a stored password for the current Windows user."""

        reference = self.build_reference(
            profile_id=profile_id,
            configured_url=configured_url,
            username=username,
        )

        try:
            return keyring.get_password(
                reference.service_name,
                reference.account_name,
            )
        except KeyringError as error:
            raise RuntimeError(
                "Windows Credential Manager could not retrieve the "
                "A-SEAT password."
            ) from error

    def delete_password(
        self,
        *,
        profile_id: str,
        configured_url: str,
        username: str,
    ) -> bool:
        """Delete a stored password. Return False when none existed."""

        reference = self.build_reference(
            profile_id=profile_id,
            configured_url=configured_url,
            username=username,
        )

        try:
            existing = keyring.get_password(
                reference.service_name,
                reference.account_name,
            )

            if existing is None:
                return False

            keyring.delete_password(
                reference.service_name,
                reference.account_name,
            )

            return True

        except KeyringError as error:
            raise RuntimeError(
                "Windows Credential Manager could not delete the "
                "A-SEAT password."
            ) from error
