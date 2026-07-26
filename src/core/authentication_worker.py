from PySide6.QtCore import QObject, Signal, Slot

from src.services.authentication_service import (
    AuthenticationService,
)


class AuthenticationWorker(QObject):
    """Validate A-SEAT credentials outside the GUI thread."""

    authentication_completed = Signal(dict)
    authentication_failed = Signal(str)
    finished = Signal()

    def __init__(
        self,
        *,
        configured_url: str,
        username: str,
        password: str,
        show_browser: bool = False,
    ) -> None:
        super().__init__()

        self.configured_url = configured_url
        self.username = username
        self.password = password
        self.show_browser = show_browser

    @Slot()
    def run(self) -> None:
        """Run the authentication test and emit its result."""

        try:
            result = AuthenticationService.authenticate(
                configured_url=self.configured_url,
                username=self.username,
                password=self.password,
                show_browser=self.show_browser,
            )

            self.authentication_completed.emit(
                result
            )

        except Exception as error:
            self.authentication_failed.emit(
                str(error)
            )

        finally:
            self.password = ""
            self.finished.emit()
