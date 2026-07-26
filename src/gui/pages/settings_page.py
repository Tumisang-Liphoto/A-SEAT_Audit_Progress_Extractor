from collections.abc import Callable
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QInputDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.services.branding_service import BrandingService
from src.utils.version import APP_VERSION


class SettingsPage(QWidget):
    """Application settings page."""

    def __init__(
        self,
        on_save_settings: Callable[[dict[str, Any]], None],
        on_check_updates: Callable[[], None],
        on_install_update: Callable[[], None],
        on_reset_application: Callable[[], None],
        on_upload_logo: Callable[[str], None],
        on_restore_default_logo: Callable[[], None],
        branding_service: BrandingService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setObjectName("contentPage")

        self._on_save_settings = on_save_settings
        self._on_check_updates = on_check_updates
        self._on_install_update = on_install_update
        self._on_reset_application = on_reset_application
        self._on_upload_logo = on_upload_logo
        self._on_restore_default_logo = on_restore_default_logo
        self.branding_service = branding_service

        self._use_custom_logo = False

        self._build_interface()

    def _build_interface(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        root_layout.setSpacing(0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(
            QFrame.Shape.NoFrame
        )
        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        content_widget = QWidget()
        content_widget.setObjectName("contentPage")

        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(
            32,
            28,
            32,
            28,
        )
        layout.setSpacing(18)

        heading = QLabel("Settings")
        heading.setObjectName("pageHeading")

        description = QLabel(
            "Configure appearance, exports, branding, updates "
            "and local application data."
        )
        description.setObjectName("pageDescription")
        description.setWordWrap(True)

        settings_card = QFrame()
        settings_card.setObjectName("formCard")

        settings_layout = QVBoxLayout(
            settings_card
        )
        settings_layout.setContentsMargins(
            24,
            22,
            24,
            22,
        )
        settings_layout.setSpacing(16)

        form = QFormLayout()
        form.setSpacing(14)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(
            [
                "Light",
                "Dark",
                "Blue",
                "High Contrast",
            ]
        )

        output_folder_widget = QWidget()
        output_folder_layout = QHBoxLayout(
            output_folder_widget
        )
        output_folder_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.output_folder_input = QLineEdit()
        self.output_folder_input.setReadOnly(
            True
        )

        browse_button = QPushButton(
            "Browse"
        )
        browse_button.clicked.connect(
            self._select_output_folder
        )

        output_folder_layout.addWidget(
            self.output_folder_input
        )
        output_folder_layout.addWidget(
            browse_button
        )

        self.show_browser_during_extraction = QCheckBox(
            "Show the browser window during extraction"
        )

        self.startup_update_check = QCheckBox(
            "Automatically check GitHub for updates "
            "when the application starts"
        )

        self.ask_before_update = QCheckBox(
            "Ask for confirmation before downloading "
            "and installing an update"
        )

        form.addRow(
            "Theme:",
            self.theme_combo,
        )
        form.addRow(
            "Output folder:",
            output_folder_widget,
        )
        form.addRow(
            "",
            self.show_browser_during_extraction,
        )
        form.addRow(
            "",
            self.startup_update_check,
        )
        form.addRow(
            "",
            self.ask_before_update,
        )

        update_widget = QWidget()
        update_layout = QVBoxLayout(
            update_widget
        )
        update_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        update_layout.setSpacing(7)

        self.check_updates_button = QPushButton(
            "Check for Updates"
        )
        self.check_updates_button.setMaximumWidth(
            180
        )
        self.check_updates_button.clicked.connect(
            self._check_for_updates
        )

        self.install_update_button = QPushButton(
            "Download and Install"
        )
        self.install_update_button.setObjectName(
            "primaryButton"
        )
        self.install_update_button.setMaximumWidth(
            190
        )
        self.install_update_button.setVisible(
            False
        )
        self.install_update_button.clicked.connect(
            self._install_update
        )

        self.update_progress_bar = QProgressBar()
        self.update_progress_bar.setRange(
            0,
            100,
        )
        self.update_progress_bar.setValue(
            0
        )
        self.update_progress_bar.setTextVisible(
            True
        )
        self.update_progress_bar.setVisible(
            False
        )

        self.update_status_label = QLabel(
            (
                f"Current version: {APP_VERSION}\n"
                "Update status: Not checked\n"
                "Last checked: Never"
            )
        )
        self.update_status_label.setObjectName(
            "statusLabel"
        )
        self.update_status_label.setWordWrap(
            True
        )

        update_layout.addWidget(
            self.check_updates_button
        )
        update_layout.addWidget(
            self.install_update_button
        )
        update_layout.addWidget(
            self.update_progress_bar
        )
        update_layout.addWidget(
            self.update_status_label
        )

        form.addRow(
            "Application updates:",
            update_widget,
        )

        button_layout = QHBoxLayout()

        self.save_button = QPushButton(
            "Save Settings"
        )
        self.save_button.setObjectName(
            "primaryButton"
        )
        self.save_button.clicked.connect(
            self._save_settings
        )

        button_layout.addStretch()
        button_layout.addWidget(
            self.save_button
        )

        settings_layout.addLayout(
            form
        )
        settings_layout.addLayout(
            button_layout
        )

        layout.addWidget(
            heading
        )
        layout.addWidget(
            description
        )
        layout.addWidget(
            settings_card
        )

        branding_card = QFrame()
        branding_card.setObjectName("formCard")

        branding_layout = QVBoxLayout(
            branding_card
        )
        branding_layout.setContentsMargins(
            24,
            22,
            24,
            22,
        )
        branding_layout.setSpacing(12)

        branding_heading = QLabel(
            "Organisation Branding"
        )
        branding_heading.setObjectName(
            "sectionHeading"
        )

        branding_description = QLabel(
            "Upload your organisation's logo for the sidebar and "
            "About page. AFROSAI-E attribution will remain visible "
            "throughout the application."
        )
        branding_description.setObjectName(
            "pageDescription"
        )
        branding_description.setWordWrap(
            True
        )

        branding_content = QHBoxLayout()
        branding_content.setSpacing(18)

        self.logo_preview_label = QLabel()
        self.logo_preview_label.setObjectName(
            "brandingLogoPreview"
        )
        self.logo_preview_label.setFixedSize(
            190,
            120,
        )
        self.logo_preview_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        branding_controls = QVBoxLayout()
        branding_controls.setSpacing(9)

        self.branding_status_label = QLabel(
            "Using the default AFROSAI-E logo."
        )
        self.branding_status_label.setObjectName(
            "statusLabel"
        )
        self.branding_status_label.setWordWrap(
            True
        )

        branding_button_layout = QHBoxLayout()
        branding_button_layout.setSpacing(8)

        self.upload_logo_button = QPushButton(
            "Upload Logo"
        )
        self.upload_logo_button.setMaximumWidth(
            150
        )
        self.upload_logo_button.clicked.connect(
            self._upload_logo
        )

        self.restore_logo_button = QPushButton(
            "Restore Default"
        )
        self.restore_logo_button.setMaximumWidth(
            160
        )
        self.restore_logo_button.clicked.connect(
            self._restore_default_logo
        )

        branding_button_layout.addWidget(
            self.upload_logo_button
        )
        branding_button_layout.addWidget(
            self.restore_logo_button
        )
        branding_button_layout.addStretch()

        branding_help = QLabel(
            "Supported formats: PNG, JPG, JPEG and ICO. "
            "A transparent PNG is recommended."
        )
        branding_help.setObjectName(
            "pageDescription"
        )
        branding_help.setWordWrap(
            True
        )

        branding_controls.addWidget(
            self.branding_status_label
        )
        branding_controls.addLayout(
            branding_button_layout
        )
        branding_controls.addWidget(
            branding_help
        )
        branding_controls.addStretch()

        branding_content.addWidget(
            self.logo_preview_label
        )
        branding_content.addLayout(
            branding_controls,
            1,
        )

        branding_layout.addWidget(
            branding_heading
        )
        branding_layout.addWidget(
            branding_description
        )
        branding_layout.addLayout(
            branding_content
        )

        layout.addWidget(
            branding_card
        )

        reset_card = QFrame()
        reset_card.setObjectName("formCard")

        reset_layout = QVBoxLayout(
            reset_card
        )
        reset_layout.setContentsMargins(
            24,
            22,
            24,
            22,
        )
        reset_layout.setSpacing(10)

        reset_heading = QLabel(
            "Reset Application Data"
        )
        reset_heading.setObjectName(
            "sectionHeading"
        )

        reset_description = QLabel(
            "Permanently remove saved settings, extraction history "
            "and output files created by this application. Unrelated "
            "files in the output folder will not be deleted."
        )
        reset_description.setWordWrap(True)
        reset_description.setObjectName(
            "pageDescription"
        )

        self.reset_application_button = QPushButton(
            "Reset Application"
        )
        self.reset_application_button.setObjectName(
            "dangerButton"
        )
        self.reset_application_button.setMaximumWidth(
            190
        )
        self.reset_application_button.clicked.connect(
            self._confirm_reset_application
        )

        reset_layout.addWidget(
            reset_heading
        )
        reset_layout.addWidget(
            reset_description
        )
        reset_layout.addSpacing(4)
        reset_layout.addWidget(
            self.reset_application_button,
            alignment=Qt.AlignmentFlag.AlignLeft,
        )

        layout.addWidget(
            reset_card
        )
        layout.addStretch()

        scroll_area.setWidget(
            content_widget
        )
        root_layout.addWidget(
            scroll_area
        )

        self.setStyleSheet(
            """
            QPushButton#dangerButton {
                background-color: #b91c1c;
                color: white;
                border: 1px solid #991b1b;
                border-radius: 7px;
                padding: 9px 16px;
                font-weight: 700;
            }

            QPushButton#dangerButton:hover {
                background-color: #991b1b;
            }

            QPushButton#dangerButton:pressed {
                background-color: #7f1d1d;
            }

            QPushButton#dangerButton:disabled {
                background-color: #9ca3af;
                border-color: #9ca3af;
                color: #f3f4f6;
            }

            QLabel#sectionHeading {
                background-color: transparent;
                font-size: 15px;
                font-weight: 700;
            }

            QLabel#brandingLogoPreview {
                background-color: palette(alternate-base);
                border: 1px solid palette(mid);
                border-radius: 10px;
            }
            """
        )

    def load_settings(
        self,
        settings: dict[str, Any],
    ) -> None:
        """Load and display saved settings."""

        theme_name = str(
            settings.get(
                "theme",
                "Light",
            )
        )

        theme_index = self.theme_combo.findText(
            theme_name
        )

        if theme_index >= 0:
            self.theme_combo.setCurrentIndex(
                theme_index
            )

        self.output_folder_input.setText(
            str(
                settings.get(
                    "output_folder",
                    "",
                )
            )
        )

        self.show_browser_during_extraction.setChecked(
            bool(
                settings.get(
                    "show_browser_during_extraction",
                    True,
                )
            )
        )

        self.startup_update_check.setChecked(
            bool(
                settings.get(
                    "check_updates_on_startup",
                    True,
                )
            )
        )

        self.ask_before_update.setChecked(
            bool(
                settings.get(
                    "ask_before_update",
                    True,
                )
            )
        )

        self._use_custom_logo = bool(
            settings.get(
                "use_custom_logo",
                False,
            )
        )

        self.refresh_branding_preview(
            self._use_custom_logo
        )


        self.restore_update_status(
            settings
        )

    def restore_update_status(
        self,
        settings: dict[str, Any],
    ) -> None:
        """Restore the most recent update-check result."""

        self.install_update_button.setVisible(
            False
        )
        self.update_progress_bar.setVisible(
            False
        )

        status = str(
            settings.get(
                "last_update_check_status",
                "",
            )
        ).strip().lower()

        checked_at = str(
            settings.get(
                "last_update_check_time",
                "",
            )
        ).strip()

        latest_version = str(
            settings.get(
                "last_update_check_latest_version",
                "",
            )
        ).strip()

        release_name = str(
            settings.get(
                "last_update_check_release_name",
                "",
            )
        ).strip()

        message = str(
            settings.get(
                "last_update_check_message",
                "",
            )
        ).strip()

        if not status:
            self.update_status_label.setText(
                (
                    f"Current version: {APP_VERSION}\n"
                    "Update status: Not checked\n"
                    "Last checked: Never"
                )
            )

            self.update_status_label.setStyleSheet(
                """
                QLabel {
                    background-color: transparent;
                    font-weight: 600;
                }
                """
            )
            return

        if status == "up_to_date":
            self.show_no_update(
                current_version=APP_VERSION,
                checked_at=checked_at,
            )
            return

        if status == "update_available":
            self.show_update_available(
                current_version=APP_VERSION,
                latest_version=latest_version or "Unknown",
                release_name=release_name,
                checked_at=checked_at,
                allow_install=False,
            )
            return

        self.show_update_failure(
            current_version=APP_VERSION,
            message=message or "The previous update check failed.",
            checked_at=checked_at,
        )

    def _check_for_updates(self) -> None:
        """Request a GitHub update check."""

        self.set_update_check_busy(
            True
        )

        self._on_check_updates()

    def _install_update(self) -> None:
        """Request download and installation of the available update."""

        self._on_install_update()

    def set_update_check_busy(
        self,
        busy: bool,
    ) -> None:
        """Enable or disable the update-check controls."""

        self.check_updates_button.setEnabled(
            not busy
        )

        self.install_update_button.setEnabled(
            not busy
        )

        self.check_updates_button.setText(
            "Checking..."
            if busy
            else "Check for Updates"
        )

        if busy:
            self.update_status_label.setText(
                (
                    f"Current version: {APP_VERSION}\n"
                    "Update status: Checking GitHub...\n"
                    "Last checked: In progress"
                )
            )

            self.update_status_label.setStyleSheet(
                """
                QLabel {
                    color: #d97706;
                    background-color: transparent;
                    font-weight: 600;
                }
                """
            )

    def show_no_update(
        self,
        current_version: str,
        checked_at: str = "",
    ) -> None:
        """Show that the installed version is current."""

        self.set_update_check_busy(
            False
        )

        self.install_update_button.setVisible(
            False
        )
        self.update_progress_bar.setVisible(
            False
        )

        last_checked = checked_at or "Unknown"

        self.update_status_label.setText(
            (
                f"Current version: {current_version}\n"
                "Update status: Application is up to date\n"
                f"Last checked: {last_checked}"
            )
        )

        self.update_status_label.setStyleSheet(
            """
            QLabel {
                color: #15803d;
                background-color: transparent;
                font-weight: 700;
            }
            """
        )

    def show_update_available(
        self,
        current_version: str,
        latest_version: str,
        release_name: str,
        checked_at: str = "",
        allow_install: bool = True,
    ) -> None:
        """Show that a newer release is available."""

        self.set_update_check_busy(
            False
        )

        self.install_update_button.setVisible(
            allow_install
        )
        self.install_update_button.setEnabled(
            allow_install
        )
        self.update_progress_bar.setVisible(
            False
        )

        last_checked = checked_at or "Unknown"

        status_text = (
            f"Current version: {current_version}\n"
            f"Update status: Version {latest_version} is available\n"
            f"Last checked: {last_checked}"
        )

        if release_name:
            status_text += (
                f"\n{release_name}"
            )

        self.update_status_label.setText(
            status_text
        )

        self.update_status_label.setStyleSheet(
            """
            QLabel {
                color: #2563eb;
                background-color: transparent;
                font-weight: 700;
            }
            """
        )

    def show_update_failure(
        self,
        current_version: str,
        message: str,
        checked_at: str = "",
    ) -> None:
        """Show an update-check error."""

        self.set_update_check_busy(
            False
        )

        self.install_update_button.setVisible(
            False
        )
        self.update_progress_bar.setVisible(
            False
        )

        last_checked = checked_at or "Unknown"

        self.update_status_label.setText(
            (
                f"Current version: {current_version}\n"
                "Update status: Check failed\n"
                f"Last checked: {last_checked}\n"
                f"{message}"
            )
        )

        self.update_status_label.setStyleSheet(
            """
            QLabel {
                color: #dc2626;
                background-color: transparent;
                font-weight: 700;
            }
            """
        )

    def set_update_install_busy(
        self,
        busy: bool,
    ) -> None:
        """Enable or disable controls during update preparation."""

        self.check_updates_button.setEnabled(
            not busy
        )
        self.install_update_button.setEnabled(
            not busy
        )
        self.install_update_button.setText(
            "Preparing Update..."
            if busy
            else "Download and Install"
        )

        self.update_progress_bar.setVisible(
            busy
        )

        if busy:
            self.update_progress_bar.setValue(
                0
            )

    def show_update_download_progress(
        self,
        percentage: int,
        message: str,
    ) -> None:
        """Display update download and verification progress."""

        self.set_update_install_busy(
            True
        )

        self.update_progress_bar.setValue(
            max(
                0,
                min(
                    percentage,
                    100,
                ),
            )
        )

        self.update_status_label.setText(
            (
                f"Current version: {APP_VERSION}\n"
                f"Update status: {message}\n"
                f"Progress: {percentage}%"
            )
        )

        self.update_status_label.setStyleSheet(
            """
            QLabel {
                color: #d97706;
                background-color: transparent;
                font-weight: 700;
            }
            """
        )

    def show_update_ready(
        self,
        latest_version: str,
    ) -> None:
        """Show that the update is ready to be installed."""

        self.set_update_install_busy(
            False
        )

        self.update_progress_bar.setVisible(
            True
        )
        self.update_progress_bar.setValue(
            100
        )

        self.update_status_label.setText(
            (
                f"Current version: {APP_VERSION}\n"
                f"Update status: Version {latest_version} "
                "is ready to install\n"
                "The application will now close and restart."
            )
        )

        self.update_status_label.setStyleSheet(
            """
            QLabel {
                color: #15803d;
                background-color: transparent;
                font-weight: 700;
            }
            """
        )

    def show_update_install_failure(
        self,
        message: str,
    ) -> None:
        """Display a download or update-preparation failure."""

        self.set_update_install_busy(
            False
        )

        self.update_progress_bar.setVisible(
            False
        )
        self.install_update_button.setVisible(
            True
        )
        self.install_update_button.setEnabled(
            True
        )

        self.update_status_label.setText(
            (
                f"Current version: {APP_VERSION}\n"
                "Update status: Download or preparation failed\n"
                f"{message}"
            )
        )

        self.update_status_label.setStyleSheet(
            """
            QLabel {
                color: #dc2626;
                background-color: transparent;
                font-weight: 700;
            }
            """
        )

    def _upload_logo(self) -> None:
        """Select and install a custom organisation logo."""

        selected_file, _ = QFileDialog.getOpenFileName(
            self,
            "Select Organisation Logo",
            "",
            (
                "Image Files (*.png *.jpg *.jpeg *.ico);;"
                "PNG Files (*.png);;"
                "JPEG Files (*.jpg *.jpeg);;"
                "Icon Files (*.ico)"
            ),
        )

        if not selected_file:
            return

        try:
            self._on_upload_logo(
                selected_file
            )

            self._use_custom_logo = True

            self.refresh_branding_preview(
                True
            )

            QMessageBox.information(
                self,
                "Logo Updated",
                (
                    "The organisation logo has been updated "
                    "successfully."
                ),
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Logo Could Not Be Updated",
                str(error),
            )

    def _restore_default_logo(self) -> None:
        """Restore the built-in AFROSAI-E organisation logo."""

        if not self._use_custom_logo:
            QMessageBox.information(
                self,
                "Default Logo Active",
                (
                    "The default AFROSAI-E logo is already active."
                ),
            )
            return

        answer = QMessageBox.question(
            self,
            "Restore Default Logo",
            (
                "Remove the custom organisation logo and restore "
                "the default AFROSAI-E logo?"
            ),
            (
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
            ),
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            self._on_restore_default_logo()

            self._use_custom_logo = False

            self.refresh_branding_preview(
                False
            )

            QMessageBox.information(
                self,
                "Default Logo Restored",
                (
                    "The default AFROSAI-E logo has been restored."
                ),
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Logo Could Not Be Restored",
                str(error),
            )

    def refresh_branding_preview(
        self,
        use_custom_logo: bool,
    ) -> None:
        """Refresh the logo preview shown in Settings."""

        self._use_custom_logo = bool(
            use_custom_logo
        )

        try:
            logo_path = (
                self.branding_service.get_active_logo_path(
                    use_custom_logo=(
                        self._use_custom_logo
                    )
                )
            )

            pixmap = QPixmap(
                str(logo_path)
            )

            if pixmap.isNull():
                raise RuntimeError(
                    "The active logo could not be displayed."
                )

            scaled = pixmap.scaled(
                170,
                100,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

            self.logo_preview_label.setText("")
            self.logo_preview_label.setPixmap(
                scaled
            )

            if (
                self._use_custom_logo
                and self.branding_service.has_custom_logo()
            ):
                self.branding_status_label.setText(
                    "Using a custom organisation logo."
                )
                self.restore_logo_button.setEnabled(
                    True
                )
            else:
                self._use_custom_logo = False
                self.branding_status_label.setText(
                    "Using the default AFROSAI-E logo."
                )
                self.restore_logo_button.setEnabled(
                    False
                )

        except Exception as error:
            self.logo_preview_label.setPixmap(
                QPixmap()
            )
            self.logo_preview_label.setText(
                "Logo unavailable"
            )
            self.branding_status_label.setText(
                str(error)
            )
            self.restore_logo_button.setEnabled(
                False
            )

    def _confirm_reset_application(
        self,
    ) -> None:
        """Require the user to type RESET before continuing."""

        warning_message = (
            "This will permanently delete:\n\n"
            "• saved application settings\n"
            "• connection profiles and saved credentials\n"
            "• the local user profile\n"
            "• extraction comparison history\n"
            "• the uploaded organisation logo\n"
            "• Excel and CSV files registered as created by this application\n\n"
            "Unrelated files in the selected output folder will not be deleted.\n"
            "This action cannot be undone.\n\n"
            "Type RESET below to continue."
        )

        confirmation_text, accepted = (
            QInputDialog.getText(
                self,
                "Reset Application Data",
                warning_message,
            )
        )

        if not accepted:
            return

        if confirmation_text.strip() != "RESET":
            QMessageBox.warning(
                self,
                "Reset Cancelled",
                (
                    "The confirmation text did not match RESET. "
                    "No application data was deleted."
                ),
            )
            return

        final_answer = QMessageBox.question(
            self,
            "Final Reset Confirmation",
            (
                "Are you sure you want to reset the application now?\n\n"
                "The application will restart after the reset."
            ),
            (
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
            ),
            QMessageBox.StandardButton.No,
        )

        if final_answer != QMessageBox.StandardButton.Yes:
            return

        self.set_reset_busy(
            True
        )

        self._on_reset_application()

    def set_reset_busy(
        self,
        busy: bool,
    ) -> None:
        """Disable the reset button while data is being removed."""

        self.reset_application_button.setEnabled(
            not busy
        )

        self.reset_application_button.setText(
            "Resetting..."
            if busy
            else "Reset Application"
        )

    @staticmethod
    def _normalise_url(
        url: str,
    ) -> str:
        return (
            url.strip()
            .lower()
            .rstrip("/")
        )

    def _save_settings(self) -> None:
        """Save application preferences."""

        settings: dict[str, Any] = {
            "theme": (
                self.theme_combo.currentText()
            ),
            "output_folder": (
                self.output_folder_input.text().strip()
            ),
            "show_browser_during_extraction": (
                self.show_browser_during_extraction.isChecked()
            ),
            "check_updates_on_startup": (
                self.startup_update_check.isChecked()
            ),
            "ask_before_update": (
                self.ask_before_update.isChecked()
            ),
            "use_custom_logo": (
                self._use_custom_logo
            ),
        }

        self._on_save_settings(
            settings
        )

        QMessageBox.information(
            self,
            "Settings Saved",
            "The application settings have been saved.",
        )

    def _select_output_folder(self) -> None:
        selected_folder = (
            QFileDialog.getExistingDirectory(
                self,
                "Select Default Output Folder",
            )
        )

        if selected_folder:
            self.output_folder_input.setText(
                selected_folder
            )