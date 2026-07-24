from datetime import datetime
from pathlib import Path
from typing import Any

from PySide6.QtCore import QThread
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QWidget,
)

from src.core.connection_worker import ConnectionWorker
from src.core.extraction_worker import ExtractionWorker
from src.core.update_worker import UpdateWorker
from src.gui.dialogs.login_dialog import LoginDialog
from src.gui.pages.dashboard_page import DashboardPage
from src.gui.pages.extraction_page import ExtractionPage
from src.gui.pages.settings_page import SettingsPage
from src.gui.widgets.sidebar import Sidebar
from src.services.browser_service import BrowserService
from src.services.settings_service import SettingsService
from src.services.theme_service import apply_theme
from src.utils.version import APP_NAME, APP_VERSION


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()

        self.settings_service = SettingsService()
        self.browser_service = BrowserService()

        self.current_settings = (
            self.settings_service.load_settings()
        )

        self.extraction_thread: QThread | None = None
        self.extraction_worker: ExtractionWorker | None = None

        self.connection_thread: QThread | None = None
        self.connection_worker: ConnectionWorker | None = None

        self.update_thread: QThread | None = None
        self.update_worker: UpdateWorker | None = None

        self.connection_test_url = ""
        self.connection_test_system_name = "A-SEAT"

        self.setWindowTitle(
            f"{APP_NAME} - Version {APP_VERSION}"
        )
        self.resize(1200, 760)
        self.setMinimumSize(950, 620)

        self._build_interface()

        self.settings_page.load_settings(
            self.current_settings
        )

        self._restore_dashboard_state()

    def _system_name(self) -> str:
        """Return the configured local system name."""

        system_name = str(
            self.current_settings.get(
                "system_name",
                "A-SEAT",
            )
        ).strip()

        return system_name or "A-SEAT"

    def _build_interface(self) -> None:
        """Create the main application interface."""

        central_widget = QWidget()
        central_widget.setObjectName(
            "mainContainer"
        )

        main_layout = QHBoxLayout(
            central_widget
        )
        main_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        main_layout.setSpacing(0)

        self.page_stack = QStackedWidget()

        self.dashboard_page = DashboardPage()

        self.extraction_page = ExtractionPage(
            self._open_system,
            self._start_extraction,
            system_name=self._system_name(),
        )

        self.settings_page = SettingsPage(
            self._save_settings,
            self._test_system_connection,
            self._check_for_updates,
        )

        self.page_stack.addWidget(
            self.dashboard_page
        )
        self.page_stack.addWidget(
            self.extraction_page
        )
        self.page_stack.addWidget(
            self.settings_page
        )

        self.sidebar = Sidebar(
            self._change_page
        )

        main_layout.addWidget(
            self.sidebar
        )
        main_layout.addWidget(
            self.page_stack,
            1,
        )

        self.setCentralWidget(
            central_widget
        )

    def _restore_dashboard_state(self) -> None:
        """Restore the latest successful extraction details."""

        latest_output_file = str(
            self.current_settings.get(
                "latest_output_file",
                "",
            )
        )

        latest_extraction_date = str(
            self.current_settings.get(
                "latest_extraction_date",
                "",
            )
        )

        try:
            latest_record_count = int(
                self.current_settings.get(
                    "latest_record_count",
                    0,
                )
            )
        except (TypeError, ValueError):
            latest_record_count = 0

        self.dashboard_page.restore_latest_result(
            output_file=latest_output_file,
            completed_at=latest_extraction_date,
            record_count=latest_record_count,
        )

    def _change_page(
        self,
        page_index: int,
    ) -> None:
        """Display the selected page."""

        if 0 <= page_index < self.page_stack.count():
            self.page_stack.setCurrentIndex(
                page_index
            )

            self.sidebar.set_selected_page(
                page_index
            )

    def _save_settings(
        self,
        settings: dict[str, Any],
    ) -> None:
        """Save visible settings and preserve internal values."""

        previous_tested_url = self._normalise_url(
            str(
                self.current_settings.get(
                    "connection_tested_url",
                    "",
                )
            )
        )

        new_system_url = self._normalise_url(
            str(
                settings.get(
                    "aseat_url",
                    "",
                )
            )
        )

        updated_settings = dict(
            self.current_settings
        )

        updated_settings.update(
            settings
        )

        if (
            previous_tested_url
            and new_system_url != previous_tested_url
        ):
            updated_settings[
                "connection_test_status"
            ] = ""

            updated_settings[
                "connection_tested_url"
            ] = ""

            updated_settings[
                "connection_tested_at"
            ] = ""

            updated_settings[
                "connection_test_message"
            ] = ""

        self.current_settings = (
            updated_settings
        )

        self.extraction_page.set_system_name(
            self._system_name()
        )

        self.settings_service.save_settings(
            self.current_settings
        )

        self.settings_page.restore_connection_status(
            self.current_settings
        )

        application = QApplication.instance()

        if application is not None:
            apply_theme(
                application,
                str(
                    self.current_settings.get(
                        "theme",
                        "Light",
                    )
                ),
            )

    def _save_username_preference(
        self,
        username: str,
        remember_username: bool,
    ) -> None:
        """Save or remove the locally remembered username."""

        if remember_username:
            self.current_settings[
                "remember_username"
            ] = True

            self.current_settings[
                "saved_username"
            ] = username.strip()
        else:
            self.current_settings[
                "remember_username"
            ] = False

            self.current_settings[
                "saved_username"
            ] = ""

        self.settings_service.save_settings(
            self.current_settings
        )

    def _save_latest_output(
        self,
        output_paths: list[str],
        completed_at: str,
        record_count: int,
    ) -> str:
        """Save the latest successful output file."""

        cleaned_paths = [
            str(path).strip()
            for path in output_paths
            if str(path).strip()
        ]

        preferred_output = ""

        for path in cleaned_paths:
            if Path(path).suffix.lower() in {
                ".xlsx",
                ".xls",
            }:
                preferred_output = path
                break

        if not preferred_output:
            for path in cleaned_paths:
                if (
                    Path(path).suffix.lower()
                    == ".csv"
                ):
                    preferred_output = path
                    break

        if (
            not preferred_output
            and cleaned_paths
        ):
            preferred_output = (
                cleaned_paths[0]
            )

        if preferred_output:
            self.current_settings[
                "latest_output_file"
            ] = preferred_output

            self.current_settings[
                "latest_extraction_date"
            ] = completed_at

            self.current_settings[
                "latest_record_count"
            ] = record_count

            self.settings_service.save_settings(
                self.current_settings
            )

        return preferred_output

    def _save_connection_result(
        self,
        status: str,
        tested_url: str,
        tested_at: str,
        message: str = "",
    ) -> None:
        """Save the latest connection-test result."""

        self.current_settings[
            "connection_test_status"
        ] = status

        self.current_settings[
            "connection_tested_url"
        ] = tested_url.strip()

        self.current_settings[
            "connection_tested_at"
        ] = tested_at

        self.current_settings[
            "connection_test_message"
        ] = message.strip()

        self.settings_service.save_settings(
            self.current_settings
        )

    @staticmethod
    def _normalise_url(
        url: str,
    ) -> str:
        """Normalise an address for comparison."""

        return (
            url.strip()
            .lower()
            .rstrip("/")
        )

    def _open_system(self) -> None:
        """Open the configured system in the default browser."""

        system_name = self._system_name()

        system_url = str(
            self.current_settings.get(
                "aseat_url",
                "",
            )
        ).strip()

        if not system_url:
            QMessageBox.warning(
                self,
                f"{system_name} Address Not Configured",
                (
                    f"Open Settings and enter the "
                    f"{system_name} address before continuing."
                ),
            )

            self._change_page(2)
            return

        success, result = (
            self.browser_service.open_url(
                system_url
            )
        )

        if success:
            self.extraction_page.update_progress(
                0,
                (
                    f"{system_name} opened in the "
                    "default browser"
                ),
            )
        else:
            QMessageBox.critical(
                self,
                f"Unable to Open {system_name}",
                result,
            )

    def _start_extraction(
        self,
        request: dict[str, Any],
    ) -> None:
        """Validate and start an extraction."""

        system_name = self._system_name()

        if self.extraction_thread is not None:
            QMessageBox.information(
                self,
                "Extraction Already Running",
                (
                    "Wait for the current extraction "
                    "to finish."
                ),
            )
            return

        system_url = str(
            self.current_settings.get(
                "aseat_url",
                "",
            )
        ).strip()

        output_folder = str(
            self.current_settings.get(
                "output_folder",
                "",
            )
        ).strip()

        if not system_url:
            QMessageBox.warning(
                self,
                f"{system_name} Address Not Configured",
                (
                    f"Enter the {system_name} address "
                    "under Settings."
                ),
            )

            self._change_page(2)
            return

        if not output_folder:
            QMessageBox.warning(
                self,
                "Output Folder Not Configured",
                (
                    "Select an output folder "
                    "under Settings."
                ),
            )

            self._change_page(2)
            return

        remembered_username = str(
            self.current_settings.get(
                "saved_username",
                "",
            )
        )

        remember_username = bool(
            self.current_settings.get(
                "remember_username",
                False,
            )
        )

        login_dialog = LoginDialog(
            system_name=system_name,
            saved_username=remembered_username,
            remember_username=remember_username,
            parent=self,
        )

        if (
            login_dialog.exec()
            != QDialog.DialogCode.Accepted
        ):
            login_dialog.clear_password()
            login_dialog.deleteLater()
            return

        (
            username,
            password,
            remember_username,
        ) = login_dialog.credentials()

        self._save_username_preference(
            username=username,
            remember_username=remember_username,
        )

        login_dialog.clear_password()
        login_dialog.deleteLater()

        self.dashboard_page.set_extraction_started()

        self.extraction_page.reset_progress()
        self.extraction_page.set_busy(True)

        self.extraction_thread = QThread(
            self
        )

        self.extraction_worker = ExtractionWorker(
            aseat_url=system_url,
            username=username,
            password=password,
            output_folder=output_folder,
            output_format=str(
                request["output_format"]
            ),
            audit_year=str(
                request.get(
                    "audit_year",
                    "",
                )
            ),
            show_browser=bool(
                self.current_settings.get(
                    "show_browser_during_extraction",
                    True,
                )
            ),
        )

        self.extraction_worker.moveToThread(
            self.extraction_thread
        )

        self.extraction_thread.started.connect(
            self.extraction_worker.run
        )

        self.extraction_worker.progress_changed.connect(
            self.extraction_page.update_progress
        )

        self.extraction_worker.extraction_completed.connect(
            self._extraction_completed
        )

        self.extraction_worker.extraction_failed.connect(
            self._extraction_failed
        )

        self.extraction_worker.finished.connect(
            self.extraction_thread.quit
        )

        self.extraction_worker.finished.connect(
            self.extraction_worker.deleteLater
        )

        self.extraction_thread.finished.connect(
            self.extraction_thread.deleteLater
        )

        self.extraction_thread.finished.connect(
            self._extraction_thread_finished
        )

        self.extraction_thread.start()

    def _extraction_completed(
        self,
        result: dict[str, Any],
    ) -> None:
        """Handle a successful extraction."""

        record_count = int(
            result.get(
                "record_count",
                0,
            )
        )

        output_paths = [
            str(path)
            for path in result.get(
                "output_paths",
                [],
            )
        ]

        completed_at = datetime.now().strftime(
            "%d %B %Y, %H:%M"
        )

        self._save_latest_output(
            output_paths=output_paths,
            completed_at=completed_at,
            record_count=record_count,
        )

        self.extraction_page.show_completed(
            record_count,
            output_paths,
        )

        self.dashboard_page.set_extraction_completed(
            record_count=record_count,
            completed_at=completed_at,
            output_paths=output_paths,
        )

        QMessageBox.information(
            self,
            "Extraction Completed",
            (
                f"{record_count} audit records were extracted.\n\n"
                "The output file has been created successfully."
            ),
        )

    def _extraction_failed(
        self,
        message: str,
    ) -> None:
        """Handle a failed extraction."""

        self.extraction_page.show_failed(
            message
        )

        self.dashboard_page.set_extraction_failed(
            message
        )

        QMessageBox.critical(
            self,
            "Extraction Failed",
            message,
        )

    def _extraction_thread_finished(
        self,
    ) -> None:
        """Clear extraction-worker references."""

        self.extraction_page.set_busy(
            False
        )

        self.extraction_worker = None
        self.extraction_thread = None

    def _test_system_connection(
        self,
        system_url: str,
    ) -> None:
        """Start the configured system connection test."""

        if self.connection_thread is not None:
            return

        system_name = (
            self.settings_page.system_name_input
            .text()
            .strip()
            or "A-SEAT"
        )

        self.connection_test_url = (
            system_url.strip()
        )

        self.connection_test_system_name = (
            system_name
        )

        self.connection_thread = QThread(
            self
        )

        self.connection_worker = ConnectionWorker(
            system_url=system_url,
            system_name=system_name,
        )

        self.connection_worker.moveToThread(
            self.connection_thread
        )

        self.connection_thread.started.connect(
            self.connection_worker.run
        )

        self.connection_worker.test_completed.connect(
            self._connection_test_completed
        )

        self.connection_worker.test_failed.connect(
            self._connection_test_failed
        )

        self.connection_worker.finished.connect(
            self.connection_thread.quit
        )

        self.connection_worker.finished.connect(
            self.connection_worker.deleteLater
        )

        self.connection_thread.finished.connect(
            self.connection_thread.deleteLater
        )

        self.connection_thread.finished.connect(
            self._connection_thread_finished
        )

        self.connection_thread.start()

    def _connection_test_completed(
        self,
        result: dict[str, Any],
    ) -> None:
        """Save and display a completed connection test."""

        tested_at = datetime.now().strftime(
            "%d %B %Y, %H:%M"
        )

        if bool(
            result.get(
                "success",
                False,
            )
        ):
            self._save_connection_result(
                status="successful",
                tested_url=self.connection_test_url,
                tested_at=tested_at,
            )

            self.settings_page.show_connection_success(
                result=result,
                tested_at=tested_at,
                tested_url=self.connection_test_url,
            )
        else:
            message = str(
                result.get(
                    "message",
                    (
                        f"The "
                        f"{self.connection_test_system_name} "
                        "login page was not confirmed."
                    ),
                )
            )

            self._save_connection_result(
                status="failed",
                tested_url=self.connection_test_url,
                tested_at=tested_at,
                message=message,
            )

            self.settings_page.show_connection_warning(
                result=result,
                tested_at=tested_at,
                tested_url=self.connection_test_url,
            )

    def _connection_test_failed(
        self,
        message: str,
    ) -> None:
        """Save and display a failed connection test."""

        tested_at = datetime.now().strftime(
            "%d %B %Y, %H:%M"
        )

        self._save_connection_result(
            status="failed",
            tested_url=self.connection_test_url,
            tested_at=tested_at,
            message=message,
        )

        self.settings_page.show_connection_failure(
            message=message,
            tested_at=tested_at,
            tested_url=self.connection_test_url,
        )

    def _connection_thread_finished(
        self,
    ) -> None:
        """Clear connection-worker references."""

        self.connection_worker = None
        self.connection_thread = None
        self.connection_test_url = ""
        self.connection_test_system_name = (
            "A-SEAT"
        )

    def _check_for_updates(self) -> None:
        """Start a GitHub update check."""

        if self.update_thread is not None:
            return

        self.update_thread = QThread(
            self
        )

        self.update_worker = UpdateWorker()

        self.update_worker.moveToThread(
            self.update_thread
        )

        self.update_thread.started.connect(
            self.update_worker.run
        )

        self.update_worker.update_check_completed.connect(
            self._update_check_completed
        )

        self.update_worker.update_check_failed.connect(
            self._update_check_failed
        )

        self.update_worker.finished.connect(
            self.update_thread.quit
        )

        self.update_worker.finished.connect(
            self.update_worker.deleteLater
        )

        self.update_thread.finished.connect(
            self.update_thread.deleteLater
        )

        self.update_thread.finished.connect(
            self._update_thread_finished
        )

        self.update_thread.start()

    def _update_check_completed(
        self,
        result: dict[str, Any],
    ) -> None:
        """Display the GitHub update-check result."""

        current_version = str(
            result.get(
                "current_version",
                APP_VERSION,
            )
        )

        latest_version = str(
            result.get(
                "latest_version",
                current_version,
            )
        )

        release_name = str(
            result.get(
                "release_name",
                "",
            )
        )

        if bool(
            result.get(
                "update_available",
                False,
            )
        ):
            self.settings_page.show_update_available(
                latest_version=latest_version,
                release_name=release_name,
            )
        else:
            self.settings_page.show_no_update(
                current_version=current_version
            )

    def _update_check_failed(
        self,
        message: str,
    ) -> None:
        """Display a failed update check."""

        self.settings_page.show_update_failure(
            message
        )

    def _update_thread_finished(
        self,
    ) -> None:
        """Clear update-worker references."""

        self.update_worker = None
        self.update_thread = None

    def closeEvent(self, event) -> None:
        """Prevent closure while background work is running."""

        if (
            self.extraction_thread is not None
            and self.extraction_thread.isRunning()
        ):
            QMessageBox.warning(
                self,
                "Extraction in Progress",
                (
                    "An extraction is still running. "
                    "Wait for it to finish before "
                    "closing the application."
                ),
            )

            event.ignore()
            return

        if (
            self.connection_thread is not None
            and self.connection_thread.isRunning()
        ):
            QMessageBox.warning(
                self,
                "Connection Test in Progress",
                (
                    "Wait for the connection test "
                    "to finish before closing the application."
                ),
            )

            event.ignore()
            return

        if (
            self.update_thread is not None
            and self.update_thread.isRunning()
        ):
            QMessageBox.warning(
                self,
                "Update Check in Progress",
                (
                    "Wait for the update check to finish "
                    "before closing the application."
                ),
            )

            event.ignore()
            return

        event.accept()