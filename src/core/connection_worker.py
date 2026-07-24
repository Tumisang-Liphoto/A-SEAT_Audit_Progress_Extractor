from PySide6.QtCore import QObject, Signal, Slot

from src.services.connection_service import ConnectionService


class ConnectionWorker(QObject):
    """Run the connection test outside the GUI thread."""

    test_completed = Signal(dict)
    test_failed = Signal(str)
    finished = Signal()

    def __init__(
        self,
        system_url: str,
        system_name: str = "A-SEAT",
    ) -> None:
        super().__init__()

        self.system_url = system_url
        self.system_name = (
            system_name.strip()
            or "A-SEAT"
        )

    @Slot()
    def run(self) -> None:
        """Test the connection and emit the result."""

        try:
            service = ConnectionService()

            result = service.test_connection(
                configured_url=self.system_url,
                system_name=self.system_name,
            )

            self.test_completed.emit(
                result
            )

        except Exception as error:
            self.test_failed.emit(
                str(error)
            )

        finally:
            self.finished.emit()