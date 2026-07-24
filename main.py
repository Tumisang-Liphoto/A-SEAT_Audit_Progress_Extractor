import sys
import traceback

from PySide6.QtWidgets import QApplication, QMessageBox

from src.core.application import AuditProgressExtractorApplication


def main() -> int:
    try:
        application = AuditProgressExtractorApplication()
        return application.run()

    except Exception:
        error_details = traceback.format_exc()
        print(error_details)

        qt_application = QApplication.instance()

        if qt_application is None:
            qt_application = QApplication(sys.argv)

        QMessageBox.critical(
            None,
            "Application Startup Error",
            error_details,
        )

        return 1


if __name__ == "__main__":
    sys.exit(main())