from datetime import datetime
from pathlib import Path
from typing import Any
import os
import shutil
import subprocess
import sys

from PySide6.QtCore import QThread, QUrl
from PySide6.QtGui import QAction, QDesktopServices, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QWidget,
)

from src.core.authentication_worker import AuthenticationWorker
from src.core.connection_worker import ConnectionWorker
from src.core.extraction_worker import ExtractionWorker
from src.core.update_worker import UpdateWorker
from src.gui.dialogs.login_dialog import LoginDialog
from src.gui.pages.about_page import AboutPage
from src.gui.pages.connection_page import ConnectionPage
from src.gui.pages.dashboard_page import DashboardPage
from src.gui.pages.extraction_page import ExtractionPage
from src.gui.pages.settings_page import SettingsPage
from src.gui.pages.user_profile_page import UserProfilePage
from src.gui.widgets.sidebar import Sidebar
from src.services.branding_service import BrandingService
from src.services.browser_service import BrowserService
from src.services.comparison_service import ComparisonService
from src.services.connection_profile_service import ConnectionProfileService
from src.services.connection_state_service import ConnectionStateService
from src.services.generated_file_service import GeneratedFileService
from src.services.reset_service import ResetService
from src.services.settings_service import SettingsService
from src.services.theme_service import apply_theme
from src.services.user_profile_service import UserProfileService
from src.utils.app_paths import application_folder, config_folder
from src.utils.version import APP_NAME, APP_VERSION


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()

        self.settings_service = SettingsService()
        self.branding_service = BrandingService()
        self.browser_service = BrowserService()
        self.comparison_service = ComparisonService()
        self.generated_file_service = GeneratedFileService()
        self.reset_service = ResetService()
        self.user_profile_service = UserProfileService()
        self.connection_profile_service = ConnectionProfileService()
        self.connection_state_service = ConnectionStateService()

        self.current_settings = (
            self.settings_service.load_settings()
        )

        self.current_user_profile = (
            self.user_profile_service.load_profile()
        )

        self.extraction_thread: QThread | None = None
        self.extraction_worker: ExtractionWorker | None = None

        self.connection_thread: QThread | None = None
        self.connection_worker: ConnectionWorker | None = None
        self.connection_test_target = "settings"

        self.authentication_thread: QThread | None = None
        self.authentication_worker: AuthenticationWorker | None = None
        self.pending_authentication_profile: dict[str, Any] = {}
        self.pending_authentication_password = ""
        self.pending_authentication_remember = False

        self.update_thread: QThread | None = None
        self.update_worker: UpdateWorker | None = None
        self.available_release_information: dict[str, Any] = {}
        self.prepared_update_information: dict[str, Any] = {}
        self.install_update_after_thread = False
        self.allow_close_for_update = False

        self.connection_test_url = ""
        self.connection_test_system_name = "A-SEAT"

        self.setWindowTitle(
            APP_NAME
        )
        self.resize(1200, 760)
        self.setMinimumSize(950, 620)

        self._build_interface()
        self._build_menu()

        self.settings_page.load_settings(
            self.current_settings
        )

        self.user_profile_page.load_profile(
            self.current_user_profile
        )

        self._load_connection_page()

        self._refresh_branding_views()

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
            self._check_for_updates,
            self._install_available_update,
            self._reset_application_data,
            self._upload_custom_logo,
            self._restore_default_logo,
            self.branding_service,
        )

        self.about_page = AboutPage(
            branding_service=self.branding_service,
            organisation_name=self._system_name(),
        )

        self.user_profile_page = UserProfilePage(
            self._save_user_profile
        )

        self.connection_page = ConnectionPage(
            self._save_connection_profile_from_page,
            self._test_connection_from_page,
            self._authenticate_connection_profile,
            self._disconnect_active_profile,
            self._open_system,
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
        self.page_stack.addWidget(
            self.about_page
        )
        self.page_stack.addWidget(
            self.user_profile_page
        )
        self.page_stack.addWidget(
            self.connection_page
        )

        self.sidebar = Sidebar(
            self._change_page,
            branding_service=self.branding_service,
            use_custom_logo=bool(
                self.current_settings.get(
                    "use_custom_logo",
                    False,
                )
            ),
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

    def _refresh_branding_views(self) -> None:
        """Refresh branding throughout the application."""

        use_custom_logo = bool(
            self.current_settings.get(
                "use_custom_logo",
                False,
            )
        )

        self.sidebar.refresh_branding(
            use_custom_logo=use_custom_logo
        )

        self.about_page.refresh_branding(
            use_custom_logo=use_custom_logo,
            organisation_name=self._system_name(),
        )

        self.settings_page.refresh_branding_preview(
            use_custom_logo
        )

    def _upload_custom_logo(
        self,
        source_path: str,
    ) -> None:
        """Install and activate a custom organisation logo."""

        self.branding_service.install_custom_logo(
            source_path
        )

        self.current_settings[
            "use_custom_logo"
        ] = True

        self.settings_service.save_settings(
            self.current_settings
        )

        self._refresh_branding_views()

    def _restore_default_logo(self) -> None:
        """Remove custom branding and restore the default logo."""

        self.branding_service.restore_default_logo()

        self.current_settings[
            "use_custom_logo"
        ] = False

        self.settings_service.save_settings(
            self.current_settings
        )

        self._refresh_branding_views()

    def _build_menu(self) -> None:
        """Create the professional application menu bar."""

        menu_bar = self.menuBar()
        menu_bar.setNativeMenuBar(
            False
        )

        file_menu = menu_bar.addMenu(
            "&File"
        )

        self.open_latest_action = QAction(
            "Open Latest Output",
            self,
        )
        self.open_latest_action.setShortcut(
            QKeySequence(
                "Ctrl+O"
            )
        )
        self.open_latest_action.setStatusTip(
            "Open the most recent extraction output file."
        )
        self.open_latest_action.triggered.connect(
            self._open_latest_output
        )
        file_menu.addAction(
            self.open_latest_action
        )

        self.open_output_folder_action = QAction(
            "Open Output Folder",
            self,
        )
        self.open_output_folder_action.setShortcut(
            QKeySequence(
                "Ctrl+Shift+O"
            )
        )
        self.open_output_folder_action.setStatusTip(
            "Open the configured extraction output folder."
        )
        self.open_output_folder_action.triggered.connect(
            self._open_output_folder
        )
        file_menu.addAction(
            self.open_output_folder_action
        )

        file_menu.addSeparator()

        exit_action = QAction(
            "Exit",
            self,
        )
        exit_action.setShortcut(
            QKeySequence(
                "Alt+F4"
            )
        )
        exit_action.triggered.connect(
            self.close
        )
        file_menu.addAction(
            exit_action
        )

        extraction_menu = menu_bar.addMenu(
            "&Extraction"
        )

        extract_progress_action = QAction(
            "Extract Progress",
            self,
        )
        extract_progress_action.setShortcut(
            QKeySequence(
                "Ctrl+E"
            )
        )
        extract_progress_action.setStatusTip(
            "Open the extraction page."
        )
        extract_progress_action.triggered.connect(
            lambda: self._change_page(1)
        )
        extraction_menu.addAction(
            extract_progress_action
        )

        open_system_action = QAction(
            "Open A-SEAT",
            self,
        )
        open_system_action.setShortcut(
            QKeySequence(
                "Ctrl+Shift+E"
            )
        )
        open_system_action.setStatusTip(
            "Open the configured A-SEAT system in the default browser."
        )
        open_system_action.triggered.connect(
            self._open_system
        )
        extraction_menu.addAction(
            open_system_action
        )

        view_menu = menu_bar.addMenu(
            "&View"
        )

        navigation_actions = [
            (
                "Dashboard",
                "Ctrl+1",
                0,
            ),
            (
                "Connection",
                "Ctrl+2",
                5,
            ),
            (
                "User Profile",
                "Ctrl+3",
                4,
            ),
            (
                "Audit Progress",
                "Ctrl+4",
                1,
            ),
            (
                "Settings",
                "Ctrl+5",
                2,
            ),
            (
                "About",
                "Ctrl+6",
                3,
            ),
        ]

        for (
            label,
            shortcut,
            page_index,
        ) in navigation_actions:
            action = QAction(
                label,
                self,
            )
            action.setShortcut(
                QKeySequence(
                    shortcut
                )
            )
            action.triggered.connect(
                lambda checked=False, index=page_index: (
                    self._change_page(
                        index
                    )
                )
            )
            view_menu.addAction(
                action
            )

        view_menu.addSeparator()

        self.toggle_sidebar_action = QAction(
            "Hide Sidebar",
            self,
        )
        self.toggle_sidebar_action.setShortcut(
            QKeySequence(
                "Ctrl+B"
            )
        )
        self.toggle_sidebar_action.triggered.connect(
            self._toggle_sidebar
        )
        view_menu.addAction(
            self.toggle_sidebar_action
        )

        tools_menu = menu_bar.addMenu(
            "&Tools"
        )

        test_connection_action = QAction(
            "Test System Connection",
            self,
        )
        test_connection_action.setStatusTip(
            "Run the configured system connection test."
        )
        test_connection_action.triggered.connect(
            self._menu_test_connection
        )
        tools_menu.addAction(
            test_connection_action
        )

        check_updates_action = QAction(
            "Check for Updates",
            self,
        )
        check_updates_action.setShortcut(
            QKeySequence(
                "Ctrl+U"
            )
        )
        check_updates_action.triggered.connect(
            self._menu_check_updates
        )
        tools_menu.addAction(
            check_updates_action
        )

        tools_menu.addSeparator()

        open_data_folder_action = QAction(
            "Open Application Data Folder",
            self,
        )
        open_data_folder_action.triggered.connect(
            self._open_application_data_folder
        )
        tools_menu.addAction(
            open_data_folder_action
        )

        tools_menu.addSeparator()

        reset_action = QAction(
            "Reset Application Data",
            self,
        )
        reset_action.triggered.connect(
            self._menu_reset_application
        )
        tools_menu.addAction(
            reset_action
        )

        help_menu = menu_bar.addMenu(
            "&Help"
        )

        shortcuts_action = QAction(
            "Keyboard Shortcuts",
            self,
        )
        shortcuts_action.setShortcut(
            QKeySequence(
                "F1"
            )
        )
        shortcuts_action.triggered.connect(
            self._show_keyboard_shortcuts
        )
        help_menu.addAction(
            shortcuts_action
        )

        help_menu.addSeparator()

        about_action = QAction(
            f"About {APP_NAME}",
            self,
        )
        about_action.triggered.connect(
            lambda: self._change_page(3)
        )
        help_menu.addAction(
            about_action
        )

        menu_bar.setStyleSheet(
            """
            QMenuBar {
                background-color: palette(window);
                color: palette(window-text);
                border-bottom: 1px solid palette(mid);
                padding: 3px 6px;
            }

            QMenuBar::item {
                background-color: transparent;
                padding: 7px 12px;
                border-radius: 5px;
            }

            QMenuBar::item:selected {
                background-color: palette(alternate-base);
            }

            QMenu {
                background-color: palette(base);
                color: palette(text);
                border: 1px solid palette(mid);
                padding: 6px;
            }

            QMenu::item {
                padding: 8px 34px 8px 12px;
                border-radius: 5px;
            }

            QMenu::item:selected {
                background-color: palette(highlight);
                color: palette(highlighted-text);
            }

            QMenu::separator {
                height: 1px;
                background-color: palette(mid);
                margin: 5px 8px;
            }
            """
        )

    def _toggle_sidebar(self) -> None:
        """Show or hide the navigation sidebar."""

        should_show = (
            not self.sidebar.isVisible()
        )

        self.sidebar.setVisible(
            should_show
        )

        self.toggle_sidebar_action.setText(
            (
                "Hide Sidebar"
                if should_show
                else "Show Sidebar"
            )
        )

    def _open_latest_output(self) -> None:
        """Open the latest extraction output file."""

        latest_output = Path(
            str(
                self.current_settings.get(
                    "latest_output_file",
                    "",
                )
            ).strip()
        )

        if not str(
            latest_output
        ).strip() or not latest_output.is_file():
            QMessageBox.warning(
                self,
                "Latest Output Not Available",
                (
                    "No latest output file is available. "
                    "Run an extraction first or confirm that the "
                    "previous file has not been moved or deleted."
                ),
            )
            return

        opened = QDesktopServices.openUrl(
            QUrl.fromLocalFile(
                str(
                    latest_output.resolve()
                )
            )
        )

        if not opened:
            QMessageBox.critical(
                self,
                "Unable to Open Output",
                (
                    "The latest output could not be opened "
                    "with the default application."
                ),
            )

    def _open_output_folder(self) -> None:
        """Open the configured output folder."""

        output_folder = Path(
            str(
                self.current_settings.get(
                    "output_folder",
                    "",
                )
            ).strip()
        )

        if not str(
            output_folder
        ).strip() or not output_folder.is_dir():
            QMessageBox.warning(
                self,
                "Output Folder Not Available",
                (
                    "Open Settings and select a valid output folder."
                ),
            )
            self._change_page(
                2
            )
            return

        opened = QDesktopServices.openUrl(
            QUrl.fromLocalFile(
                str(
                    output_folder.resolve()
                )
            )
        )

        if not opened:
            QMessageBox.critical(
                self,
                "Unable to Open Folder",
                "The configured output folder could not be opened.",
            )

    def _open_application_data_folder(self) -> None:
        """Open the local application data folder."""

        data_folder = config_folder()

        try:
            data_folder.mkdir(
                parents=True,
                exist_ok=True,
            )
        except OSError as error:
            QMessageBox.critical(
                self,
                "Application Data Folder",
                (
                    "The application data folder could not be created."
                    f"\n\n{error}"
                ),
            )
            return

        opened = QDesktopServices.openUrl(
            QUrl.fromLocalFile(
                str(
                    data_folder.resolve()
                )
            )
        )

        if not opened:
            QMessageBox.critical(
                self,
                "Unable to Open Folder",
                "The application data folder could not be opened.",
            )

    def _menu_test_connection(self) -> None:
        """Navigate to Settings and start the connection test."""

        self._change_page(
            5
        )

        self.connection_page.test_server_button.click()

    def _menu_check_updates(self) -> None:
        """Navigate to Settings and check for updates."""

        self._change_page(
            2
        )

        self.settings_page.check_updates_button.click()

    def _menu_reset_application(self) -> None:
        """Navigate to Settings and show the reset confirmation."""

        self._change_page(
            2
        )

        self.settings_page.reset_application_button.click()

    def _show_keyboard_shortcuts(self) -> None:
        """Display the available application shortcuts."""

        QMessageBox.information(
            self,
            "Keyboard Shortcuts",
            (
                "Navigation\n"
                "Ctrl+1    Dashboard\n"
                "Ctrl+2    Connection\n"
                "Ctrl+3    User Profile\n"
                "Ctrl+4    Audit Progress\n"
                "Ctrl+5    Settings\n"
                "Ctrl+6    About\n\n"
                "Application\n"
                "Ctrl+E    Open Extract Progress\n"
                "Ctrl+O    Open latest output\n"
                "Ctrl+Shift+O    Open output folder\n"
                "Ctrl+B    Show or hide the sidebar\n"
                "Ctrl+U    Check for updates\n"
                "F1        Show keyboard shortcuts\n"
                "Alt+F4    Exit"
            ),
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

        try:
            comparison = (
                self.comparison_service.compare_latest_snapshots()
            )

            self.dashboard_page.show_comparison(
                comparison
            )

        except Exception as error:
            self.dashboard_page.show_comparison_error(
                str(error)
            )

    def _reset_application_data(
        self,
    ) -> None:
        """Reset application data and restart with default settings."""

        if (
            self.extraction_thread is not None
            and self.extraction_thread.isRunning()
        ):
            self.settings_page.set_reset_busy(
                False
            )

            QMessageBox.warning(
                self,
                "Extraction in Progress",
                (
                    "Wait for the current extraction to finish "
                    "before resetting the application."
                ),
            )
            return

        if (
            self.connection_thread is not None
            and self.connection_thread.isRunning()
        ):
            self.settings_page.set_reset_busy(
                False
            )

            QMessageBox.warning(
                self,
                "Connection Test in Progress",
                (
                    "Wait for the connection test to finish "
                    "before resetting the application."
                ),
            )
            return

        if (
            self.authentication_thread is not None
            and self.authentication_thread.isRunning()
        ):
            self.settings_page.set_reset_busy(
                False
            )

            QMessageBox.warning(
                self,
                "Authentication in Progress",
                (
                    "Wait for the authentication test to finish "
                    "before resetting the application."
                ),
            )
            return

        if (
            self.update_thread is not None
            and self.update_thread.isRunning()
        ):
            self.settings_page.set_reset_busy(
                False
            )

            QMessageBox.warning(
                self,
                "Update in Progress",
                (
                    "Wait for the update operation to finish "
                    "before resetting the application."
                ),
            )
            return

        try:
            result = (
                self.reset_service.reset_application_data()
            )

        except Exception as error:
            self.settings_page.set_reset_busy(
                False
            )

            QMessageBox.critical(
                self,
                "Reset Failed",
                (
                    "The application data could not be reset.\n\n"
                    f"{error}"
                ),
            )
            return

        failed_items = result.get(
            "failed_items",
            [],
        )

        if failed_items:
            self.settings_page.set_reset_busy(
                False
            )

            failure_lines = []

            for item in failed_items[:5]:
                if isinstance(
                    item,
                    dict,
                ):
                    failure_lines.append(
                        (
                            f"{item.get('path', 'Unknown item')}: "
                            f"{item.get('error', 'Unknown error')}"
                        )
                    )
                else:
                    failure_lines.append(
                        str(item)
                    )

            if len(failed_items) > 5:
                failure_lines.append(
                    (
                        f"...and {len(failed_items) - 5} "
                        "additional item(s)."
                    )
                )

            QMessageBox.critical(
                self,
                "Reset Incomplete",
                (
                    "Some application data could not be removed.\n\n"
                    + "\n".join(failure_lines)
                    + "\n\nClose any open exported files and try again."
                ),
            )
            return

        deleted_outputs = int(
            result.get(
                "generated_files_deleted",
                0,
            )
        )

        deleted_items = int(
            result.get(
                "deleted_count",
                0,
            )
        )

        QMessageBox.information(
            self,
            "Application Reset Complete",
            (
                "The application data has been reset successfully.\n\n"
                f"Generated output files deleted: {deleted_outputs}\n"
                f"Application items removed: {deleted_items}\n\n"
                "The application will now restart with default settings."
            ),
        )

        self._restart_after_reset()

    def _restart_after_reset(
        self,
    ) -> None:
        """Start a fresh application process and close this one."""

        try:
            if getattr(
                sys,
                "frozen",
                False,
            ):
                command = [
                    sys.executable,
                ]

                working_folder = Path(
                    sys.executable
                ).resolve().parent

            else:
                project_folder = (
                    Path(__file__)
                    .resolve()
                    .parents[2]
                )

                command = [
                    sys.executable,
                    str(
                        project_folder
                        / "main.py"
                    ),
                ]

                working_folder = project_folder

            subprocess.Popen(
                command,
                cwd=str(
                    working_folder
                ),
                close_fds=True,
            )

            self.allow_close_for_update = True

            application = QApplication.instance()

            if application is not None:
                application.quit()

        except Exception as error:
            self.settings_page.set_reset_busy(
                False
            )

            QMessageBox.critical(
                self,
                "Restart Failed",
                (
                    "The application data was reset, but the "
                    "application could not restart automatically.\n\n"
                    f"{error}\n\n"
                    "Close and reopen the application manually."
                ),
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

    def _load_connection_page(
        self,
    ) -> None:
        """Load the active profile and its secure credential state."""

        profile = (
            self.connection_profile_service
            .get_active_profile()
        )

        state: dict[str, Any] = {
            "status": "authentication_required",
            "credential_available": False,
            "expires_at": "",
        }

        if profile is not None:
            try:
                state = (
                    self.connection_state_service
                    .get_status(profile)
                )
            except Exception as error:
                state = {
                    "status": "authentication_required",
                    "credential_available": False,
                    "expires_at": "",
                    "message": str(error),
                }

        self.connection_page.load_profile(
            profile,
            state,
        )

    def _save_connection_profile_from_page(
        self,
        profile_data: dict[str, str],
    ) -> dict[str, Any]:
        """Create or update the active connection profile."""

        profile_id = str(
            profile_data.get(
                "profile_id",
                "",
            )
        ).strip()

        profile_name = str(
            profile_data.get(
                "profile_name",
                "",
            )
        ).strip()

        system_name = str(
            profile_data.get(
                "system_name",
                "A-SEAT",
            )
        ).strip() or "A-SEAT"

        configured_url = str(
            profile_data.get(
                "configured_url",
                "",
            )
        ).strip()

        username = str(
            profile_data.get(
                "username",
                "",
            )
        ).strip()

        if profile_id:
            saved_profile = (
                self.connection_profile_service
                .update_profile(
                    profile_id,
                    profile_name=profile_name,
                    system_name=system_name,
                    configured_url=(
                        self.browser_service
                        .normalise_url(
                            configured_url
                        )
                    ),
                    username=username,
                )
            )
        else:
            saved_profile = (
                self.connection_profile_service
                .create_profile(
                    profile_name=profile_name,
                    system_name=system_name,
                    configured_url=configured_url,
                    username=username,
                    make_active=True,
                )
            )

        self.current_settings[
            "system_name"
        ] = saved_profile.get(
            "system_name",
            "A-SEAT",
        )

        self.current_settings[
            "aseat_url"
        ] = saved_profile.get(
            "configured_url",
            "",
        )

        self.current_settings[
            "saved_username"
        ] = saved_profile.get(
            "username",
            "",
        )

        self.current_settings[
            "remember_username"
        ] = bool(
            saved_profile.get(
                "username",
                "",
            )
        )

        self.settings_service.save_settings(
            self.current_settings
        )

        self.connection_page.load_profile(
            saved_profile,
            self.connection_state_service.get_status(
                saved_profile
            ),
        )

        self.extraction_page.set_system_name(
            self._system_name()
        )

        return saved_profile

    def _test_connection_from_page(
        self,
        profile_data: dict[str, str],
    ) -> None:
        """Save the profile and test server reachability."""

        saved_profile = (
            self._save_connection_profile_from_page(
                profile_data
            )
        )

        self.connection_test_target = (
            "connection"
        )

        self._test_system_connection(
            str(
                saved_profile.get(
                    "configured_url",
                    "",
                )
            )
        )

    def _authenticate_connection_profile(
        self,
        profile_data: dict[str, str],
        password: str,
        remember_for_five_days: bool,
    ) -> None:
        """Validate the active profile credentials in the background."""

        if self.authentication_thread is not None:
            return

        saved_profile = (
            self._save_connection_profile_from_page(
                profile_data
            )
        )

        self.pending_authentication_profile = dict(
            saved_profile
        )
        self.pending_authentication_password = password
        self.pending_authentication_remember = bool(
            remember_for_five_days
        )

        self.authentication_thread = QThread(
            self
        )

        self.authentication_worker = AuthenticationWorker(
            configured_url=str(
                saved_profile.get(
                    "configured_url",
                    "",
                )
            ),
            username=str(
                saved_profile.get(
                    "username",
                    "",
                )
            ),
            password=password,
            show_browser=False,
        )

        self.authentication_worker.moveToThread(
            self.authentication_thread
        )

        self.authentication_thread.started.connect(
            self.authentication_worker.run
        )

        self.authentication_worker.authentication_completed.connect(
            self._authentication_completed
        )

        self.authentication_worker.authentication_failed.connect(
            self._authentication_failed
        )

        self.authentication_worker.finished.connect(
            self.authentication_thread.quit
        )

        self.authentication_worker.finished.connect(
            self.authentication_worker.deleteLater
        )

        self.authentication_thread.finished.connect(
            self.authentication_thread.deleteLater
        )

        self.authentication_thread.finished.connect(
            self._authentication_thread_finished
        )

        self.authentication_thread.start()

    def _authentication_completed(
        self,
        result: dict[str, Any],
    ) -> None:
        """Store a credential only after A-SEAT authentication succeeds."""

        profile = dict(
            self.pending_authentication_profile
        )

        password = (
            self.pending_authentication_password
        )

        remember = (
            self.pending_authentication_remember
        )

        try:
            saved_profile = (
                self.connection_state_service
                .save_credential(
                    profile_id=str(
                        profile.get(
                            "profile_id",
                            "",
                        )
                    ),
                    configured_url=str(
                        profile.get(
                            "configured_url",
                            "",
                        )
                    ),
                    username=str(
                        profile.get(
                            "username",
                            "",
                        )
                    ),
                    password=password,
                    remember_for_five_days=remember,
                )
            )

            expires_at = str(
                saved_profile.get(
                    "credential_expires_at",
                    "",
                )
            )

            self.connection_page.show_authentication_success(
                remembered=remember,
                expires_at=expires_at,
            )

        except Exception as error:
            self.connection_page.show_authentication_failure(
                str(error)
            )

        finally:
            self.pending_authentication_password = ""

    def _authentication_failed(
        self,
        message: str,
    ) -> None:
        """Display failed A-SEAT authentication."""

        self.pending_authentication_password = ""

        self.connection_page.show_authentication_failure(
            message
        )

    def _authentication_thread_finished(
        self,
    ) -> None:
        """Clear authentication-worker references."""

        self.authentication_worker = None
        self.authentication_thread = None
        self.pending_authentication_profile = {}
        self.pending_authentication_password = ""
        self.pending_authentication_remember = False

    def _disconnect_active_profile(
        self,
    ) -> None:
        """Delete the active profile credential."""

        profile = (
            self.connection_profile_service
            .get_active_profile()
        )

        if profile is None:
            self.connection_page.show_disconnected()
            return

        try:
            self.connection_state_service.disconnect(
                profile
            )

            self.connection_page.show_disconnected()

        except Exception as error:
            QMessageBox.critical(
                self,
                "Disconnect Failed",
                str(error),
            )

    def _save_user_profile(
        self,
        profile: dict[str, Any],
    ) -> None:
        """Save the current Windows user's profile."""

        self.current_user_profile = (
            self.user_profile_service.save_profile(
                profile
            )
        )

    def _save_settings(
        self,
        settings: dict[str, Any],
    ) -> None:
        """Save application preferences and preserve connection data."""

        updated_settings = dict(
            self.current_settings
        )

        updated_settings.update(
            settings
        )

        self.current_settings = (
            updated_settings
        )

        self.settings_service.save_settings(
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

    def _save_update_check_result(
        self,
        status: str,
        checked_at: str,
        current_version: str,
        latest_version: str = "",
        release_name: str = "",
        message: str = "",
    ) -> None:
        """Save the latest GitHub update-check result."""

        self.current_settings[
            "last_update_check_status"
        ] = status

        self.current_settings[
            "last_update_check_time"
        ] = checked_at

        self.current_settings[
            "last_update_check_current_version"
        ] = current_version

        self.current_settings[
            "last_update_check_latest_version"
        ] = latest_version

        self.current_settings[
            "last_update_check_release_name"
        ] = release_name

        self.current_settings[
            "last_update_check_message"
        ] = message

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

        active_profile = (
            self.connection_profile_service
            .get_active_profile()
        )

        system_url = ""

        if active_profile is not None:
            system_url = str(
                active_profile.get(
                    "configured_url",
                    "",
                )
            ).strip()

        if not system_url:
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
        """Validate and start an extraction using the active profile."""

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

        active_profile = (
            self.connection_profile_service
            .get_active_profile()
        )

        system_name = self._system_name()
        system_url = ""
        username = ""
        password = ""

        if active_profile is not None:
            system_name = str(
                active_profile.get(
                    "system_name",
                    system_name,
                )
            ).strip() or system_name

            system_url = str(
                active_profile.get(
                    "configured_url",
                    "",
                )
            ).strip()

            username = str(
                active_profile.get(
                    "username",
                    "",
                )
            ).strip()

            try:
                password = (
                    self.connection_state_service
                    .retrieve_password(
                        active_profile
                    )
                    or ""
                )
            except Exception as error:
                QMessageBox.warning(
                    self,
                    "Stored Credential Unavailable",
                    (
                        "The saved A-SEAT credential could not be "
                        "retrieved. Enter the password manually or "
                        "reconnect from the Connection page.\n\n"
                        f"{error}"
                    ),
                )
                password = ""

        if not system_url:
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
                    "Open Connection and configure the "
                    f"{system_name} address before continuing."
                ),
            )

            self._change_page(5)
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

        if not username or not password:
            remembered_username = (
                username
                or str(
                    self.current_settings.get(
                        "saved_username",
                        "",
                    )
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

        password = ""

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

        records = [
            dict(record)
            for record in result.get(
                "records",
                [],
            )
            if isinstance(
                record,
                dict,
            )
        ]

        completed_datetime = datetime.now()

        completed_at = completed_datetime.strftime(
            "%d %B %Y, %H:%M"
        )

        self._save_latest_output(
            output_paths=output_paths,
            completed_at=completed_at,
            record_count=record_count,
        )

        processing_errors: list[str] = []

        try:
            self.generated_file_service.register_files(
                output_paths
            )
        except Exception as error:
            processing_errors.append(
                "Generated output files could not be registered: "
                f"{error}"
            )

        try:
            if records:
                self.comparison_service.save_snapshot(
                    records=records,
                    extracted_at=completed_datetime,
                )

            comparison = (
                self.comparison_service.compare_latest_snapshots()
            )

            self.dashboard_page.show_comparison(
                comparison
            )

        except Exception as error:
            comparison_error = str(error)

            processing_errors.append(
                "The progress comparison could not be updated: "
                f"{comparison_error}"
            )

            self.dashboard_page.show_comparison_error(
                comparison_error
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

        completion_message = (
            f"{record_count} audit records were extracted.\n\n"
            "The output file has been created successfully."
        )

        if processing_errors:
            completion_message += (
                "\n\nThe extraction succeeded, but the following "
                "supporting tasks could not be completed:\n- "
                + "\n- ".join(processing_errors)
            )

        QMessageBox.information(
            self,
            "Extraction Completed",
            completion_message,
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

        active_profile = (
            self.connection_profile_service
            .get_active_profile()
        )

        system_name = self._system_name()

        if active_profile is not None:
            system_name = str(
                active_profile.get(
                    "system_name",
                    system_name,
                )
            ).strip() or system_name

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

            if self.connection_test_target == "connection":
                self.connection_page.show_server_success(
                    str(
                        result.get(
                            "message",
                            "A-SEAT login page detected.",
                        )
                    )
                )
            else:
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

            if self.connection_test_target == "connection":
                self.connection_page.show_server_failure(
                    message
                )
            else:
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

        if self.connection_test_target == "connection":
            self.connection_page.show_server_failure(
                message
            )
        else:
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
        self.connection_test_target = "settings"

    def _check_for_updates(self) -> None:
        """Start a GitHub update check."""

        if self.update_thread is not None:
            return

        self.update_thread = QThread(
            self
        )

        self.update_worker = UpdateWorker(
            operation="check"
        )

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
        """Save and display the GitHub update-check result."""

        checked_at = datetime.now().strftime(
            "%d %B %Y, %H:%M"
        )

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
            self.available_release_information = dict(
                result
            )

            self._save_update_check_result(
                status="update_available",
                checked_at=checked_at,
                current_version=current_version,
                latest_version=latest_version,
                release_name=release_name,
            )

            self.settings_page.show_update_available(
                current_version=current_version,
                latest_version=latest_version,
                release_name=release_name,
                checked_at=checked_at,
            )
        else:
            self.available_release_information = {}

            self._save_update_check_result(
                status="up_to_date",
                checked_at=checked_at,
                current_version=current_version,
                latest_version=latest_version,
                release_name=release_name,
            )

            self.settings_page.show_no_update(
                current_version=current_version,
                checked_at=checked_at,
            )

    def _update_check_failed(
        self,
        message: str,
    ) -> None:
        """Save and display a failed update check."""

        checked_at = datetime.now().strftime(
            "%d %B %Y, %H:%M"
        )

        self.available_release_information = {}

        self._save_update_check_result(
            status="failed",
            checked_at=checked_at,
            current_version=APP_VERSION,
            message=message,
        )

        self.settings_page.show_update_failure(
            current_version=APP_VERSION,
            message=message,
            checked_at=checked_at,
        )

    def _install_available_update(self) -> None:
        """Download and prepare the available application update."""

        if self.update_thread is not None:
            return

        if not self.available_release_information:
            QMessageBox.information(
                self,
                "Check for Updates",
                (
                    "Check for updates again before downloading "
                    "and installing a release."
                ),
            )
            return

        if not getattr(
            sys,
            "frozen",
            False,
        ):
            QMessageBox.information(
                self,
                "Packaged Application Required",
                (
                    "Automatic installation can only be tested from "
                    "the packaged application. The source-code version "
                    "can still check and prepare releases."
                ),
            )
            return

        latest_version = str(
            self.available_release_information.get(
                "latest_version",
                "",
            )
        )

        if bool(
            self.current_settings.get(
                "ask_before_update",
                True,
            )
        ):
            answer = QMessageBox.question(
                self,
                "Install Update",
                (
                    f"Download and install version {latest_version}?\n\n"
                    "The application will close and restart. "
                    "Your configuration will be preserved."
                ),
                (
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No
                ),
                QMessageBox.StandardButton.No,
            )

            if answer != QMessageBox.StandardButton.Yes:
                return

        self.settings_page.set_update_install_busy(
            True
        )

        self.update_thread = QThread(
            self
        )

        self.update_worker = UpdateWorker(
            operation="prepare",
            release_information=(
                self.available_release_information
            ),
        )

        self.update_worker.moveToThread(
            self.update_thread
        )

        self.update_thread.started.connect(
            self.update_worker.run
        )

        self.update_worker.download_progress.connect(
            self.settings_page.show_update_download_progress
        )

        self.update_worker.update_prepared.connect(
            self._update_prepared
        )

        self.update_worker.update_preparation_failed.connect(
            self._update_preparation_failed
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

    def _update_prepared(
        self,
        result: dict[str, Any],
    ) -> None:
        """Store the prepared update until its worker thread closes."""

        self.prepared_update_information = dict(
            result
        )

        latest_version = str(
            result.get(
                "latest_version",
                "",
            )
        )

        self.settings_page.show_update_ready(
            latest_version
        )

        self.install_update_after_thread = True

    def _update_preparation_failed(
        self,
        message: str,
    ) -> None:
        """Display an update download or preparation failure."""

        self.install_update_after_thread = False
        self.prepared_update_information = {}

        self.settings_page.show_update_install_failure(
            message
        )

    def _locate_packaged_updater(self) -> Path:
        """Locate the updater included with the packaged application."""

        app_folder = application_folder()

        candidates = [
            (
                app_folder
                / "_internal"
                / "A-SEAT Updater.exe"
            ),
            app_folder / "A-SEAT Updater.exe",
        ]

        for candidate in candidates:
            if candidate.is_file():
                return candidate

        raise RuntimeError(
            "The packaged A-SEAT updater executable could not be found."
        )

    def _launch_external_updater(self) -> None:
        """Copy and launch the updater outside the application folder."""

        information = dict(
            self.prepared_update_information
        )

        self.prepared_update_information = {}
        self.install_update_after_thread = False

        try:
            source_updater = self._locate_packaged_updater()

            workspace = Path(
                str(
                    information.get(
                        "workspace",
                        "",
                    )
                )
            ).resolve()

            payload_folder = Path(
                str(
                    information.get(
                        "payload_folder",
                        "",
                    )
                )
            ).resolve()

            latest_version = str(
                information.get(
                    "latest_version",
                    "",
                )
            ).strip()

            if not workspace.is_dir():
                raise RuntimeError(
                    "The prepared update workspace could not be found."
                )

            if not payload_folder.is_dir():
                raise RuntimeError(
                    "The prepared update package could not be found."
                )

            updater_copy = (
                workspace
                / "A-SEAT Updater.exe"
            )

            shutil.copy2(
                source_updater,
                updater_copy,
            )

            target_folder = application_folder()

            command = [
                str(updater_copy),
                "--source",
                str(payload_folder),
                "--target",
                str(target_folder),
                "--workspace",
                str(workspace),
                "--pid",
                str(os.getpid()),
                "--version",
                latest_version,
            ]

            subprocess.Popen(
                command,
                cwd=str(workspace),
                creationflags=(
                    subprocess.CREATE_NEW_PROCESS_GROUP
                    | subprocess.DETACHED_PROCESS
                ),
                close_fds=True,
            )

            self.allow_close_for_update = True

            application = QApplication.instance()

            if application is not None:
                application.quit()

        except Exception as error:
            self.settings_page.show_update_install_failure(
                str(error)
            )

            QMessageBox.critical(
                self,
                "Update Could Not Start",
                str(error),
            )

    def _update_thread_finished(
        self,
    ) -> None:
        """Clear update-worker references and launch a prepared update."""

        self.update_worker = None
        self.update_thread = None

        if self.install_update_after_thread:
            self._launch_external_updater()

    def closeEvent(self, event) -> None:
        """Prevent closure while background work is running."""

        if self.allow_close_for_update:
            event.accept()
            return

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
            self.authentication_thread is not None
            and self.authentication_thread.isRunning()
        ):
            QMessageBox.warning(
                self,
                "Authentication in Progress",
                (
                    "Wait for the authentication test "
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