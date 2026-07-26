import json
import shutil
from typing import Any

from src.services.connection_profile_service import (
    ConnectionProfileService,
)
from src.utils.app_paths import config_folder, legacy_config_folder


class SettingsService:
    """Load and save per-user application settings."""

    def __init__(self) -> None:
        self.settings_folder = config_folder()
        self.settings_file = (
            self.settings_folder / "user_settings.json"
        )
        self.legacy_settings_file = (
            legacy_config_folder() / "user_settings.json"
        )

        self.default_settings: dict[str, Any] = {
            "schema_version": 2,
            "theme": "Light",
            "system_name": "A-SEAT",
            "aseat_url": "",
            "output_folder": "",
            "check_updates_on_startup": True,
            "ask_before_update": True,
            "show_browser_during_extraction": True,
            "remember_username": False,
            "saved_username": "",
            "active_connection_profile_id": "",
        }

    def _migrate_legacy_settings_file(self) -> None:
        """Copy legacy settings into LocalAppData once."""

        if self.settings_file.exists():
            return

        if not self.legacy_settings_file.is_file():
            return

        self.settings_folder.mkdir(parents=True, exist_ok=True)

        try:
            shutil.copy2(
                self.legacy_settings_file,
                self.settings_file,
            )
        except OSError:
            pass

    def load_settings(self) -> dict[str, Any]:
        """Load settings from disk or return defaults."""

        self._migrate_legacy_settings_file()

        if not self.settings_file.exists():
            return self.default_settings.copy()

        try:
            with self.settings_file.open("r", encoding="utf-8") as file:
                saved_settings = json.load(file)

            if not isinstance(saved_settings, dict):
                return self.default_settings.copy()

            settings = self.default_settings.copy()
            settings.update(saved_settings)
            settings["schema_version"] = 2

            profile_service = ConnectionProfileService()
            profile = profile_service.migrate_legacy_settings(settings)

            if profile is not None:
                settings["active_connection_profile_id"] = (
                    profile["profile_id"]
                )

            return settings

        except (OSError, json.JSONDecodeError):
            return self.default_settings.copy()

    def save_settings(
        self,
        settings: dict[str, Any],
    ) -> None:
        """Save settings atomically under LocalAppData."""

        self.settings_folder.mkdir(parents=True, exist_ok=True)

        payload = self.default_settings.copy()
        payload.update(settings)
        payload["schema_version"] = 2

        temporary_file = self.settings_file.with_suffix(".json.tmp")

        with temporary_file.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=4)

        temporary_file.replace(self.settings_file)
