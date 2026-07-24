import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from src.gui.main_window import MainWindow
from src.services.settings_service import SettingsService
from src.services.theme_service import apply_theme
from src.utils.version import APP_NAME, APP_VERSION


class AuditProgressExtractorApplication:
    """Controls application startup and shutdown."""

    def __init__(self) -> None:
        self.qt_application = QApplication(sys.argv)

        self.qt_application.setApplicationName(APP_NAME)
        self.qt_application.setApplicationVersion(APP_VERSION)

        # Explicit font size prevents the QFont point-size warning.
        self.qt_application.setFont(QFont("Segoe UI", 10))

        settings_service = SettingsService()
        settings = settings_service.load_settings()

        selected_theme = settings.get("theme", "Light")
        apply_theme(self.qt_application, selected_theme)

        self.main_window = MainWindow()

    def run(self) -> int:
        self.main_window.show()
        return self.qt_application.exec()