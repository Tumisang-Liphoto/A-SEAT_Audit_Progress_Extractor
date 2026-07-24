from typing import Any

from PySide6.QtCore import QObject, Signal, Slot

from src.services.update_service import UpdateService


class UpdateWorker(QObject):
    """Runs update operations outside the GUI thread."""

    update_check_completed = Signal(dict)
    update_check_failed = Signal(str)

    download_progress = Signal(int, str)
    update_prepared = Signal(dict)
    update_preparation_failed = Signal(str)

    finished = Signal()

    def __init__(
        self,
        operation: str = "check",
        release_information: dict[str, Any] | None = None,
    ) -> None:
        super().__init__()

        self.operation = operation.strip().lower()

        self.release_information = (
            dict(release_information)
            if release_information is not None
            else {}
        )

    @Slot()
    def run(self) -> None:
        """Perform the requested update operation."""

        try:
            service = UpdateService()

            if self.operation == "check":
                result = service.check_for_update()

                self.update_check_completed.emit(
                    result
                )

                return

            if self.operation == "prepare":
                if not self.release_information:
                    raise RuntimeError(
                        "No update release information was supplied."
                    )

                result = service.prepare_update(
                    release_information=(
                        self.release_information
                    ),
                    progress_callback=(
                        self._report_download_progress
                    ),
                )

                self.update_prepared.emit(
                    result
                )

                return

            raise RuntimeError(
                f"Unknown update operation: {self.operation}"
            )

        except Exception as error:
            message = str(error)

            if self.operation == "prepare":
                self.update_preparation_failed.emit(
                    message
                )
            else:
                self.update_check_failed.emit(
                    message
                )

        finally:
            self.finished.emit()

    def _report_download_progress(
        self,
        percentage: int,
        message: str,
    ) -> None:
        """Send download progress to the GUI thread."""

        self.download_progress.emit(
            percentage,
            message,
        )