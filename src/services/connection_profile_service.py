from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from src.services.aseat_url_service import ASeatUrlService
from src.utils.app_paths import config_folder


class ConnectionProfileService:
    """Load and save A-SEAT connection profiles."""

    SCHEMA_VERSION = 1
    FILE_NAME = "connection_profiles.json"

    def __init__(self) -> None:
        self.folder = config_folder()
        self.file_path = self.folder / self.FILE_NAME

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _default_data() -> dict[str, Any]:
        return {
            "schema_version": 1,
            "active_profile_id": "",
            "profiles": [],
        }

    def load(self) -> dict[str, Any]:
        """Load profile data, returning an empty structure if absent."""

        if not self.file_path.exists():
            return self._default_data()

        try:
            with self.file_path.open("r", encoding="utf-8") as file:
                data = json.load(file)

            if not isinstance(data, dict):
                return self._default_data()

            profiles = data.get("profiles", [])

            if not isinstance(profiles, list):
                profiles = []

            return {
                "schema_version": int(
                    data.get("schema_version", self.SCHEMA_VERSION)
                ),
                "active_profile_id": str(
                    data.get("active_profile_id", "")
                ).strip(),
                "profiles": profiles,
            }

        except (OSError, ValueError, json.JSONDecodeError):
            return self._default_data()

    def save(self, data: dict[str, Any]) -> None:
        """Save connection profiles atomically."""

        self.folder.mkdir(parents=True, exist_ok=True)

        payload = {
            "schema_version": self.SCHEMA_VERSION,
            "active_profile_id": str(
                data.get("active_profile_id", "")
            ).strip(),
            "profiles": list(data.get("profiles", [])),
        }

        temporary_file = self.file_path.with_suffix(".json.tmp")

        with temporary_file.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=4)

        temporary_file.replace(self.file_path)

    def create_profile(
        self,
        *,
        profile_name: str,
        system_name: str,
        configured_url: str,
        username: str,
        make_active: bool = True,
    ) -> dict[str, Any]:
        """Create and save one connection profile."""

        clean_name = profile_name.strip()
        clean_system_name = system_name.strip() or "A-SEAT"
        clean_username = username.strip()

        if not clean_name:
            raise ValueError("A connection profile name is required.")

        resolved = ASeatUrlService.resolve(configured_url)
        now = self._now_iso()

        profile = {
            "profile_id": uuid.uuid4().hex,
            "profile_name": clean_name,
            "system_name": clean_system_name,
            "configured_url": resolved.login_url,
            "username": clean_username,
            "created_at": now,
            "updated_at": now,
            "credential_saved_at": "",
            "credential_expires_at": "",
            "last_authenticated_at": "",
            "last_authentication_status": "authentication_required",
        }

        data = self.load()
        data["profiles"].append(profile)

        if make_active:
            data["active_profile_id"] = profile["profile_id"]

        self.save(data)
        return profile

    def get_active_profile(self) -> dict[str, Any] | None:
        """Return the active connection profile."""

        data = self.load()
        active_id = data.get("active_profile_id", "")

        for profile in data.get("profiles", []):
            if profile.get("profile_id") == active_id:
                return dict(profile)

        return None

    def update_profile(
        self,
        profile_id: str,
        **changes: Any,
    ) -> dict[str, Any]:
        """Update one profile and return the saved profile."""

        data = self.load()

        for profile in data.get("profiles", []):
            if profile.get("profile_id") != profile_id:
                continue

            allowed_fields = {
                "profile_name",
                "system_name",
                "configured_url",
                "username",
                "credential_saved_at",
                "credential_expires_at",
                "last_authenticated_at",
                "last_authentication_status",
            }

            for key, value in changes.items():
                if key in allowed_fields:
                    profile[key] = value

            profile["updated_at"] = self._now_iso()
            self.save(data)
            return dict(profile)

        raise ValueError("The connection profile could not be found.")

    def migrate_legacy_settings(
        self,
        settings: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Create the first profile from existing settings when needed."""

        existing = self.get_active_profile()

        if existing is not None:
            return existing

        configured_url = str(settings.get("aseat_url", "")).strip()

        if not configured_url:
            return None

        system_name = str(
            settings.get("system_name", "A-SEAT")
        ).strip() or "A-SEAT"

        username = str(settings.get("saved_username", "")).strip()

        return self.create_profile(
            profile_name=system_name,
            system_name=system_name,
            configured_url=configured_url,
            username=username,
            make_active=True,
        )
