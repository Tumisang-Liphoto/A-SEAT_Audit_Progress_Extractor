import json
from typing import Any

from src.utils.app_paths import config_folder


class UserProfileService:
    """Load and save non-sensitive user profile information."""

    SCHEMA_VERSION = 1
    FILE_NAME = "user_profile.json"

    def __init__(self) -> None:
        self.profile_folder = config_folder()
        self.profile_file = (
            self.profile_folder
            / self.FILE_NAME
        )

        self.default_profile: dict[str, Any] = {
            "schema_version": self.SCHEMA_VERSION,
            "preferred_name": "",
            "full_name": "",
            "job_title": "",
            "organisation": "",
            "directorate": "",
            "email_address": "",
            "phone_number": "",
        }

    def load_profile(self) -> dict[str, Any]:
        """Load the user profile or return a blank profile."""

        if not self.profile_file.is_file():
            return self.default_profile.copy()

        try:
            with self.profile_file.open(
                "r",
                encoding="utf-8",
            ) as file:
                saved_profile = json.load(file)

            if not isinstance(
                saved_profile,
                dict,
            ):
                return self.default_profile.copy()

            profile = self.default_profile.copy()
            profile.update(saved_profile)
            profile["schema_version"] = self.SCHEMA_VERSION

            return profile

        except (
            OSError,
            json.JSONDecodeError,
        ):
            return self.default_profile.copy()

    def save_profile(
        self,
        profile: dict[str, Any],
    ) -> dict[str, Any]:
        """Validate and save the user profile atomically."""

        payload = self.default_profile.copy()

        for key in payload:
            if key == "schema_version":
                continue

            payload[key] = str(
                profile.get(
                    key,
                    "",
                )
            ).strip()

        payload["schema_version"] = (
            self.SCHEMA_VERSION
        )

        self.profile_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_file = (
            self.profile_file.with_suffix(
                ".json.tmp"
            )
        )

        with temporary_file.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                payload,
                file,
                indent=4,
            )

        temporary_file.replace(
            self.profile_file
        )

        return payload

    def delete_profile(self) -> bool:
        """Delete the saved user profile."""

        deleted = False

        for file_path in (
            self.profile_file,
            self.profile_file.with_suffix(
                ".json.tmp"
            ),
        ):
            if not file_path.exists():
                continue

            file_path.unlink()
            deleted = True

        return deleted
