import json
from typing import Any

from src.utils.app_paths import config_folder


class SettingsService:
    """Loads and saves user application settings."""

    def __init__(self) -> None:
        self.settings_folder = config_folder()

        self.settings_file = (
            self.settings_folder
            / "user_settings.json"
        )

        self.default_settings: dict[str, Any] = {
            "theme": "Light",
            "system_name": "A-SEAT",
            "aseat_url": "",
            "output_folder": "",
            "check_updates_on_startup": True,
            "ask_before_update": True,
            "show_browser_during_extraction": True,
            "remember_username": False,
            "saved_username": "",
        }

    def load_settings(self) -> dict[str, Any]:
        """Load settings from disk or return defaults."""

        if not self.settings_file.exists():
            return self.default_settings.copy()

        try:
            with self.settings_file.open(
                "r",
                encoding="utf-8",
            ) as file:
                saved_settings = json.load(file)

            if not isinstance(
                saved_settings,
                dict,
            ):
                return self.default_settings.copy()

            settings = self.default_settings.copy()
            settings.update(saved_settings)

            return settings

        except (
            OSError,
            json.JSONDecodeError,
        ):
            return self.default_settings.copy()

    def save_settings(
        self,
        settings: dict[str, Any],
    ) -> None:
        """Save settings to disk."""

        self.settings_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_file = (
            self.settings_file.with_suffix(
                ".json.tmp"
            )
        )

        with temporary_file.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                settings,
                file,
                indent=4,
            )

        temporary_file.replace(
            self.settings_file
        )