from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from src.services.connection_profile_service import (
    ConnectionProfileService,
)
from src.services.credential_service import CredentialService


class ConnectionStateService:
    """Manage credential retention and authentication state."""

    RETENTION_DAYS = 5

    def __init__(self) -> None:
        self.profile_service = ConnectionProfileService()
        self.credential_service = CredentialService()

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _parse_datetime(value: str) -> datetime | None:
        clean_value = value.strip()

        if not clean_value:
            return None

        try:
            parsed = datetime.fromisoformat(clean_value)
        except ValueError:
            return None

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed.astimezone(timezone.utc)

    def save_credential(
        self,
        *,
        profile_id: str,
        configured_url: str,
        username: str,
        password: str,
        remember_for_five_days: bool,
    ) -> dict[str, Any]:
        """Store or discard the credential according to user choice."""

        now = self._now()

        if remember_for_five_days:
            self.credential_service.store_password(
                profile_id=profile_id,
                configured_url=configured_url,
                username=username,
                password=password,
            )

            expires_at = now + timedelta(
                days=self.RETENTION_DAYS
            )

            return self.profile_service.update_profile(
                profile_id,
                username=username.strip(),
                credential_saved_at=now.isoformat(),
                credential_expires_at=expires_at.isoformat(),
                last_authenticated_at=now.isoformat(),
                last_authentication_status="connected",
            )

        self.credential_service.delete_password(
            profile_id=profile_id,
            configured_url=configured_url,
            username=username,
        )

        return self.profile_service.update_profile(
            profile_id,
            username=username.strip(),
            credential_saved_at="",
            credential_expires_at="",
            last_authenticated_at=now.isoformat(),
            last_authentication_status="connected_for_current_task",
        )

    def get_status(
        self,
        profile: dict[str, Any],
    ) -> dict[str, Any]:
        """Return the current credential state for one profile."""

        profile_id = str(
            profile.get("profile_id", "")
        ).strip()

        configured_url = str(
            profile.get("configured_url", "")
        ).strip()

        username = str(
            profile.get("username", "")
        ).strip()

        expires_at = self._parse_datetime(
            str(
                profile.get(
                    "credential_expires_at",
                    "",
                )
            )
        )

        if expires_at is None:
            return {
                "status": "authentication_required",
                "credential_available": False,
                "expires_at": "",
            }

        if self._now() >= expires_at:
            self.disconnect(profile)

            return {
                "status": "expired",
                "credential_available": False,
                "expires_at": expires_at.isoformat(),
            }

        password = self.credential_service.retrieve_password(
            profile_id=profile_id,
            configured_url=configured_url,
            username=username,
        )

        if password is None:
            return {
                "status": "authentication_required",
                "credential_available": False,
                "expires_at": expires_at.isoformat(),
            }

        return {
            "status": "credential_stored",
            "credential_available": True,
            "expires_at": expires_at.isoformat(),
        }

    def retrieve_password(
        self,
        profile: dict[str, Any],
    ) -> str | None:
        """Retrieve a usable stored password or expire it."""

        status = self.get_status(profile)

        if not status.get(
            "credential_available",
            False,
        ):
            return None

        return self.credential_service.retrieve_password(
            profile_id=str(
                profile.get("profile_id", "")
            ),
            configured_url=str(
                profile.get("configured_url", "")
            ),
            username=str(
                profile.get("username", "")
            ),
        )

    def disconnect(
        self,
        profile: dict[str, Any],
    ) -> dict[str, Any]:
        """Delete the saved credential and clear its metadata."""

        profile_id = str(
            profile.get("profile_id", "")
        ).strip()

        configured_url = str(
            profile.get("configured_url", "")
        ).strip()

        username = str(
            profile.get("username", "")
        ).strip()

        if profile_id and configured_url and username:
            self.credential_service.delete_password(
                profile_id=profile_id,
                configured_url=configured_url,
                username=username,
            )

        return self.profile_service.update_profile(
            profile_id,
            credential_saved_at="",
            credential_expires_at="",
            last_authentication_status=(
                "authentication_required"
            ),
        )

    def disconnect_all(self) -> dict[str, Any]:
        """Delete saved credentials for every known profile."""

        data = self.profile_service.load()
        deleted_count = 0
        failed_items: list[dict[str, str]] = []

        for profile in data.get("profiles", []):
            try:
                profile_id = str(
                    profile.get("profile_id", "")
                ).strip()

                configured_url = str(
                    profile.get("configured_url", "")
                ).strip()

                username = str(
                    profile.get("username", "")
                ).strip()

                if not (
                    profile_id
                    and configured_url
                    and username
                ):
                    continue

                deleted = (
                    self.credential_service
                    .delete_password(
                        profile_id=profile_id,
                        configured_url=configured_url,
                        username=username,
                    )
                )

                if deleted:
                    deleted_count += 1

            except Exception as error:
                failed_items.append(
                    {
                        "profile_id": str(
                            profile.get(
                                "profile_id",
                                "",
                            )
                        ),
                        "error": str(error),
                    }
                )

        return {
            "success": not failed_items,
            "deleted_count": deleted_count,
            "failed_items": failed_items,
        }
