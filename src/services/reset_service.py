import shutil
from pathlib import Path
from typing import Any

from src.services.branding_service import BrandingService
from src.services.connection_profile_service import (
    ConnectionProfileService,
)
from src.services.connection_state_service import (
    ConnectionStateService,
)
from src.services.generated_file_service import GeneratedFileService
from src.services.user_profile_service import UserProfileService
from src.utils.app_paths import config_folder


class ResetService:
    """
    Reset application-owned data safely.

    The reset removes registered exports, settings, extraction
    snapshots, branding, connection profiles and saved A-SEAT
    credentials. Unknown files are never deleted.
    """

    def __init__(self) -> None:
        self.config_folder = config_folder()

        self.settings_file = (
            self.config_folder
            / "user_settings.json"
        )

        self.settings_temp_file = (
            self.config_folder
            / "user_settings.json.tmp"
        )

        self.connection_profile_service = (
            ConnectionProfileService()
        )

        self.connection_state_service = (
            ConnectionStateService()
        )

        self.connection_profiles_file = (
            self.connection_profile_service.file_path
        )

        self.connection_profiles_temp_file = (
            self.connection_profiles_file.with_suffix(
                ".json.tmp"
            )
        )

        self.user_profile_service = UserProfileService()

        self.user_profile_file = (
            self.user_profile_service.profile_file
        )

        self.user_profile_temp_file = (
            self.user_profile_file.with_suffix(
                ".json.tmp"
            )
        )

        self.extraction_history_folder = (
            self.config_folder
            / "extraction_history"
        )

        self.generated_file_service = (
            GeneratedFileService()
        )

        self.branding_service = (
            BrandingService()
        )

        self.branding_folder = (
            self.branding_service.branding_folder
        )

    def reset_application_data(
        self,
    ) -> dict[str, Any]:
        """
        Delete application configuration and registered outputs.

        Saved credentials are deleted from Windows Credential Manager
        before their connection-profile metadata is removed.
        """

        deleted_items: list[str] = []
        missing_items: list[str] = []
        failed_items: list[dict[str, str]] = []

        credential_result = (
            self._delete_saved_credentials()
        )

        for failed_credential in credential_result.get(
            "failed_items",
            [],
        ):
            failed_items.append(
                {
                    "path": (
                        "Windows Credential Manager"
                    ),
                    "error": str(
                        failed_credential.get(
                            "error",
                            "Credential deletion failed.",
                        )
                    ),
                }
            )

        generated_result = (
            self._delete_registered_output_files()
        )

        deleted_items.extend(
            generated_result.get(
                "deleted_files",
                [],
            )
        )

        missing_items.extend(
            generated_result.get(
                "missing_files",
                [],
            )
        )

        failed_items.extend(
            generated_result.get(
                "failed_files",
                [],
            )
        )

        self._delete_file(
            self.settings_file,
            deleted_items,
            missing_items,
            failed_items,
        )

        self._delete_file(
            self.settings_temp_file,
            deleted_items,
            missing_items,
            failed_items,
        )

        self._delete_file(
            self.connection_profiles_file,
            deleted_items,
            missing_items,
            failed_items,
        )

        self._delete_file(
            self.connection_profiles_temp_file,
            deleted_items,
            missing_items,
            failed_items,
        )

        self._delete_file(
            self.user_profile_file,
            deleted_items,
            missing_items,
            failed_items,
        )

        self._delete_file(
            self.user_profile_temp_file,
            deleted_items,
            missing_items,
            failed_items,
        )

        self._delete_folder(
            self.extraction_history_folder,
            deleted_items,
            missing_items,
            failed_items,
        )

        self._delete_folder(
            self.branding_folder,
            deleted_items,
            missing_items,
            failed_items,
        )

        self._delete_registry_if_still_present(
            deleted_items,
            missing_items,
            failed_items,
        )

        self._remove_empty_config_folder()

        return {
            "success": not failed_items,
            "deleted_count": len(
                deleted_items
            ),
            "missing_count": len(
                missing_items
            ),
            "failed_count": len(
                failed_items
            ),
            "deleted_items": deleted_items,
            "missing_items": missing_items,
            "failed_items": failed_items,
            "credentials_deleted": int(
                credential_result.get(
                    "deleted_count",
                    0,
                )
            ),
            "credentials_failed": len(
                credential_result.get(
                    "failed_items",
                    [],
                )
            ),
            "generated_files_deleted": int(
                generated_result.get(
                    "deleted_count",
                    0,
                )
            ),
            "generated_files_missing": int(
                generated_result.get(
                    "missing_count",
                    0,
                )
            ),
            "generated_files_failed": int(
                generated_result.get(
                    "failed_count",
                    0,
                )
            ),
        }

    def preview_reset(
        self,
    ) -> dict[str, Any]:
        """
        Return a non-destructive summary of data to be removed.

        This method does not retrieve, expose or delete passwords.
        """

        registered_files = (
            self.generated_file_service
            .load_registered_files()
        )

        existing_registered_files = [
            str(path)
            for path in registered_files
            if path.is_file()
        ]

        snapshot_count = 0

        if self.extraction_history_folder.is_dir():
            try:
                snapshot_count = sum(
                    1
                    for path
                    in self.extraction_history_folder.iterdir()
                    if (
                        path.is_file()
                        and path.suffix.lower()
                        == ".json"
                    )
                )
            except OSError:
                snapshot_count = 0

        profile_data = (
            self.connection_profile_service.load()
        )

        profiles = profile_data.get(
            "profiles",
            [],
        )

        credential_metadata_count = sum(
            1
            for profile in profiles
            if str(
                profile.get(
                    "credential_expires_at",
                    "",
                )
            ).strip()
        )

        return {
            "registered_file_count": len(
                registered_files
            ),
            "existing_registered_file_count": len(
                existing_registered_files
            ),
            "snapshot_count": snapshot_count,
            "settings_exist": (
                self.settings_file.is_file()
            ),
            "registry_exists": (
                self.generated_file_service
                .registry_file
                .is_file()
            ),
            "custom_branding_exists": (
                self.branding_folder.is_dir()
            ),
            "connection_profile_count": len(
                profiles
            ),
            "saved_credential_count": (
                credential_metadata_count
            ),
            "connection_profiles_exist": (
                self.connection_profiles_file.is_file()
            ),
            "user_profile_exists": (
                self.user_profile_file.is_file()
            ),
        }

    def _delete_saved_credentials(
        self,
    ) -> dict[str, Any]:
        """Delete all known A-SEAT credentials securely."""

        try:
            return (
                self.connection_state_service
                .disconnect_all()
            )

        except Exception as error:
            return {
                "success": False,
                "deleted_count": 0,
                "failed_items": [
                    {
                        "profile_id": "",
                        "error": str(error),
                    }
                ],
            }

    def _delete_registered_output_files(
        self,
    ) -> dict[str, Any]:
        """Delete output files listed in the safe registry."""

        try:
            return (
                self.generated_file_service
                .delete_registered_files()
            )

        except Exception as error:
            return {
                "deleted_count": 0,
                "missing_count": 0,
                "failed_count": 1,
                "deleted_files": [],
                "missing_files": [],
                "failed_files": [
                    {
                        "path": str(
                            self.generated_file_service
                            .registry_file
                        ),
                        "error": str(error),
                    }
                ],
            }

    def _delete_registry_if_still_present(
        self,
        deleted_items: list[str],
        missing_items: list[str],
        failed_items: list[dict[str, str]],
    ) -> None:
        """Remove a registry left behind after output deletion."""

        registry_file = (
            self.generated_file_service
            .registry_file
        )

        if not registry_file.exists():
            return

        self._delete_file(
            registry_file,
            deleted_items,
            missing_items,
            failed_items,
        )

    @staticmethod
    def _delete_file(
        file_path: Path,
        deleted_items: list[str],
        missing_items: list[str],
        failed_items: list[dict[str, str]],
    ) -> None:
        """Delete one known application-owned file."""

        if not file_path.exists():
            missing_items.append(
                str(file_path)
            )
            return

        if not file_path.is_file():
            failed_items.append(
                {
                    "path": str(file_path),
                    "error": (
                        "The expected file path is not a file."
                    ),
                }
            )
            return

        try:
            file_path.unlink()

            deleted_items.append(
                str(file_path)
            )

        except OSError as error:
            failed_items.append(
                {
                    "path": str(file_path),
                    "error": str(error),
                }
            )

    @staticmethod
    def _delete_folder(
        folder_path: Path,
        deleted_items: list[str],
        missing_items: list[str],
        failed_items: list[dict[str, str]],
    ) -> None:
        """Delete one known application-owned folder recursively."""

        if not folder_path.exists():
            missing_items.append(
                str(folder_path)
            )
            return

        if not folder_path.is_dir():
            failed_items.append(
                {
                    "path": str(folder_path),
                    "error": (
                        "The expected folder path is not a folder."
                    ),
                }
            )
            return

        try:
            shutil.rmtree(
                folder_path
            )

            deleted_items.append(
                str(folder_path)
            )

        except OSError as error:
            failed_items.append(
                {
                    "path": str(folder_path),
                    "error": str(error),
                }
            )

    def _remove_empty_config_folder(
        self,
    ) -> None:
        """
        Remove the configuration folder only when it is empty.

        Unknown files are never deleted.
        """

        try:
            if (
                self.config_folder.is_dir()
                and not any(
                    self.config_folder.iterdir()
                )
            ):
                self.config_folder.rmdir()

        except OSError:
            pass
