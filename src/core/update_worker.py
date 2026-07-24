from PySide6.QtCore import QObject, Signal, Slot

from src.services.update_service import UpdateService


class UpdateWorker(QObject):
    """Runs the GitHub update check outside the GUI thread."""

    update_check_completed = Signal(dict)
    update_check_failed = Signal(str)
    finished = Signal()

    @Slot()
    def run(self) -> None:
        """Check GitHub for a newer release."""

        try:
            service = UpdateService()

            result = service.check_for_update()

            self.update_check_completed.emit(
                result
            )

        except Exception as error:
            self.update_check_failed.emit(
                str(error)
            )

        finally:
            self.finished.emit()