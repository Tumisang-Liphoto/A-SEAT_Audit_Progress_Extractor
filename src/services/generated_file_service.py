import json
from pathlib import Path
from typing import Any

from src.utils.app_paths import config_folder


class GeneratedFileService:
    """
    Records output files created by the application and safely
    removes them when application data is reset.
    """

    ALLOWED_EXTENSIONS = {
        ".xlsx",
        ".csv",
    }

    ALLOWED_FILENAME_PREFIXES = {
        "A-SEAT_Audit_Progress",
    }

    def __init__(self) -> None:
        self.registry_file = (
            config_folder()
            / "generated_files.json"
        )

    def register_files(
        self,
        file_paths: list[str],
    ) -> None:
        """Add generated output files to the local registry."""

        registered_files = self.load_registered_files()

        registered_set = {
            str(path)
            for path in registered_files
        }

        for file_path in file_paths:
            cleaned_path = str(
                file_path
            ).strip()

            if not cleaned_path:
                continue

            path = Path(
                cleaned_path
            ).expanduser()

            try:
                resolved_path = path.resolve()
            except OSError:
                continue

            if not self._is_allowed_generated_file(
                resolved_path
            ):
                continue

            registered_set.add(
                str(resolved_path)
            )

        self._save_registry(
            sorted(
                registered_set
            )
        )

    def load_registered_files(
        self,
    ) -> list[Path]:
        """Load registered file paths."""

        if not self.registry_file.is_file():
            return []

        try:
            with self.registry_file.open(
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(
                    file
                )

        except (
            OSError,
            json.JSONDecodeError,
        ):
            return []

        if not isinstance(
            data,
            dict,
        ):
            return []

        raw_files = data.get(
            "generated_files",
            [],
        )

        if not isinstance(
            raw_files,
            list,
        ):
            return []

        files: list[Path] = []

        for value in raw_files:
            cleaned_value = str(
                value
            ).strip()

            if not cleaned_value:
                continue

            files.append(
                Path(
                    cleaned_value
                )
            )

        return files

    def delete_registered_files(
        self,
    ) -> dict[str, Any]:
        """
        Delete registered application-generated files.

        Files are deleted only when their extension and filename
        match the application's known export pattern.
        """

        deleted_files: list[str] = []
        missing_files: list[str] = []
        failed_files: list[dict[str, str]] = []

        for file_path in self.load_registered_files():
            try:
                resolved_path = (
                    file_path.expanduser().resolve()
                )
            except OSError as error:
                failed_files.append(
                    {
                        "path": str(file_path),
                        "error": str(error),
                    }
                )
                continue

            if not self._is_allowed_generated_file(
                resolved_path
            ):
                failed_files.append(
                    {
                        "path": str(resolved_path),
                        "error": (
                            "The file does not match the "
                            "application export pattern."
                        ),
                    }
                )
                continue

            if not resolved_path.exists():
                missing_files.append(
                    str(resolved_path)
                )
                continue

            if not resolved_path.is_file():
                failed_files.append(
                    {
                        "path": str(resolved_path),
                        "error": (
                            "The registered path is not a file."
                        ),
                    }
                )
                continue

            try:
                resolved_path.unlink()

                deleted_files.append(
                    str(resolved_path)
                )

                self._remove_empty_parent_folder(
                    resolved_path.parent
                )

            except OSError as error:
                failed_files.append(
                    {
                        "path": str(resolved_path),
                        "error": str(error),
                    }
                )

        self.clear_registry()

        return {
            "deleted_count": len(
                deleted_files
            ),
            "missing_count": len(
                missing_files
            ),
            "failed_count": len(
                failed_files
            ),
            "deleted_files": deleted_files,
            "missing_files": missing_files,
            "failed_files": failed_files,
        }

    def clear_registry(self) -> None:
        """Delete the generated-file registry."""

        if not self.registry_file.exists():
            return

        try:
            self.registry_file.unlink()
        except OSError as error:
            raise RuntimeError(
                "The generated-file registry could not be removed."
            ) from error

    def _save_registry(
        self,
        file_paths: list[str],
    ) -> None:
        """Save the generated-file registry atomically."""

        self.registry_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_file = (
            self.registry_file.with_suffix(
                ".json.tmp"
            )
        )

        registry_data = {
            "generated_files": file_paths,
        }

        with temporary_file.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                registry_data,
                file,
                indent=4,
            )

        temporary_file.replace(
            self.registry_file
        )

    @classmethod
    def _is_allowed_generated_file(
        cls,
        file_path: Path,
    ) -> bool:
        """Confirm that a path matches an application export."""

        if (
            file_path.suffix.lower()
            not in cls.ALLOWED_EXTENSIONS
        ):
            return False

        return any(
            file_path.name.startswith(
                prefix
            )
            for prefix in cls.ALLOWED_FILENAME_PREFIXES
        )

    @staticmethod
    def _remove_empty_parent_folder(
        folder: Path,
    ) -> None:
        """
        Remove an empty monthly output folder.

        The configured root output folder is not removed because
        only the immediate parent of a generated file is checked.
        """

        try:
            if (
                folder.is_dir()
                and not any(
                    folder.iterdir()
                )
            ):
                folder.rmdir()

        except OSError:
            pass