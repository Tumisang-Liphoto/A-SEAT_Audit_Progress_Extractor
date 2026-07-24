import shutil
from pathlib import Path
from typing import Any

from src.services.generated_file_service import GeneratedFileService
from src.utils.app_paths import config_folder


class ResetService:
    """
    Resets locally stored application data.

    The service deletes only files that belong to the application:
    registered exports, saved settings, extraction snapshots and the
    generated-file registry.
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

        self.extraction_history_folder = (
            self.config_folder
            / "extraction_history"
        )

        self.generated_file_service = (
            GeneratedFileService()
        )

    def reset_application_data(
        self,
    ) -> dict[str, Any]:
        """
        Delete application configuration, extraction history and
        registered output files.

        A result dictionary is returned so the GUI can show exactly
        what was deleted and whether any items could not be removed.
        """

        deleted_items: list[str] = []
        missing_items: list[str] = []
        failed_items: list[dict[str, str]] = []

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

        self._delete_folder(
            self.extraction_history_folder,
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
        Return a summary of the data that would be removed.

        This method does not delete anything.
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
        """
        Remove the registry if output deletion left it behind.

        The registry normally deletes itself, but this provides a
        final cleanup attempt.
        """

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
        """Delete one application-owned file."""

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
        """Delete one application-owned folder recursively."""

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