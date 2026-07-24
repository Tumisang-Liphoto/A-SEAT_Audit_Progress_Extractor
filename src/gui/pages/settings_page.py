from collections.abc import Callable
from typing import Any

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class SettingsPage(QWidget):
    """Application settings page."""

    def __init__(
        self,
        on_save_settings: Callable[[dict[str, Any]], None],
        on_test_connection: Callable[[str], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setObjectName("contentPage")

        self._on_save_settings = on_save_settings
        self._on_test_connection = on_test_connection

        self._restoring_settings = False
        self._last_tested_url = ""

        self._build_interface()

    def _build_interface(self) -> None:
        layout = QVBoxLayout(self)
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
            "Configure appearance, system access, exports "
            "and application updates."
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

        self.system_name_input = QLineEdit()
        self.system_name_input.setPlaceholderText(
            "Enter your organisation's system name"
        )
        self.system_name_input.setClearButtonEnabled(True)

        self.system_url_input = QLineEdit()
        self.system_url_input.setPlaceholderText(
            "For example: http://10.1.6.133/system/dashboard/"
        )
        self.system_url_input.textChanged.connect(
            self._system_url_changed
        )

        connection_widget = QWidget()
        connection_layout = QVBoxLayout(
            connection_widget
        )
        connection_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        connection_layout.setSpacing(7)

        self.test_connection_button = QPushButton(
            "Test Connection"
        )
        self.test_connection_button.setMaximumWidth(160)
        self.test_connection_button.clicked.connect(
            self._test_connection
        )

        self.connection_status_label = QLabel(
            "Connection Status: Not tested"
        )
        self.connection_status_label.setObjectName(
            "statusLabel"
        )
        self.connection_status_label.setWordWrap(True)

        connection_layout.addWidget(
            self.test_connection_button
        )
        connection_layout.addWidget(
            self.connection_status_label
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
        self.output_folder_input.setReadOnly(True)

        browse_button = QPushButton("Browse")
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
            "System name:",
            self.system_name_input,
        )
        form.addRow(
            "System URL:",
            self.system_url_input,
        )
        form.addRow(
            "",
            connection_widget,
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

        button_layout = QHBoxLayout()

        self.check_updates_button = QPushButton(
            "Check for Updates"
        )

        self.save_button = QPushButton(
            "Save Settings"
        )
        self.save_button.setObjectName(
            "primaryButton"
        )
        self.save_button.clicked.connect(
            self._save_settings
        )

        button_layout.addWidget(
            self.check_updates_button
        )
        button_layout.addStretch()
        button_layout.addWidget(
            self.save_button
        )

        settings_layout.addLayout(form)
        settings_layout.addLayout(
            button_layout
        )

        layout.addWidget(heading)
        layout.addWidget(description)
        layout.addWidget(settings_card)
        layout.addStretch()

    def load_settings(
        self,
        settings: dict[str, Any],
    ) -> None:
        """Load and display saved application settings."""

        self._restoring_settings = True

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

        self.system_name_input.setText(
            str(
                settings.get(
                    "system_name",
                    "A-SEAT",
                )
            )
        )

        self.system_url_input.setText(
            str(
                settings.get(
                    "aseat_url",
                    "",
                )
            )
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

        self._restoring_settings = False

        self.restore_connection_status(
            settings
        )

    def restore_connection_status(
        self,
        settings: dict[str, Any],
    ) -> None:
        """Restore the saved connection-test result."""

        current_url = self._normalise_url(
            self.system_url_input.text()
        )

        tested_url = self._normalise_url(
            str(
                settings.get(
                    "connection_tested_url",
                    "",
                )
            )
        )

        self._last_tested_url = tested_url

        test_status = str(
            settings.get(
                "connection_test_status",
                "",
            )
        ).lower()

        tested_at = str(
            settings.get(
                "connection_tested_at",
                "",
            )
        ).strip()

        message = str(
            settings.get(
                "connection_test_message",
                "",
            )
        ).strip()

        if not test_status or not tested_url:
            self.show_connection_not_tested()
            return

        if current_url != tested_url:
            self.show_connection_not_tested(
                different_address=True
            )
            return

        if test_status == "successful":
            status_text = (
                "Connection Status: Last test successful"
            )

            if tested_at:
                status_text += (
                    f"\nLast tested: {tested_at}"
                )

            self.connection_status_label.setText(
                status_text
            )

            self._set_success_style()
            return

        status_text = (
            "Connection Status: Last test failed"
        )

        if tested_at:
            status_text += (
                f"\nLast tested: {tested_at}"
            )

        if message:
            status_text += (
                f"\n{message}"
            )

        self.connection_status_label.setText(
            status_text
        )

        self._set_failure_style()

    def _system_url_changed(
        self,
        new_url: str,
    ) -> None:
        """Reset the displayed test result when the URL changes."""

        if self._restoring_settings:
            return

        normalised_url = self._normalise_url(
            new_url
        )

        if (
            self._last_tested_url
            and normalised_url == self._last_tested_url
        ):
            return

        self.show_connection_not_tested(
            different_address=bool(
                normalised_url
            )
        )

    def _test_connection(self) -> None:
        system_name = (
            self.system_name_input.text().strip()
        )

        system_url = (
            self.system_url_input.text().strip()
        )

        if not system_name:
            QMessageBox.warning(
                self,
                "System Name Required",
                "Enter the name of your system.",
            )

            self.system_name_input.setFocus()
            return

        if not system_url:
            QMessageBox.warning(
                self,
                "System Address Required",
                (
                    f"Enter the {system_name} URL before "
                    "testing the connection."
                ),
            )

            self.system_url_input.setFocus()
            return

        self.set_connection_test_busy(True)

        self._on_test_connection(
            system_url
        )

    def set_connection_test_busy(
        self,
        busy: bool,
    ) -> None:
        self.test_connection_button.setEnabled(
            not busy
        )

        self.system_url_input.setEnabled(
            not busy
        )

        self.system_name_input.setEnabled(
            not busy
        )

        self.test_connection_button.setText(
            "Testing..."
            if busy
            else "Test Connection"
        )

        if busy:
            self.connection_status_label.setText(
                "Connection Status: Testing..."
            )

            self.connection_status_label.setStyleSheet(
                """
                QLabel {
                    color: #d97706;
                    background-color: transparent;
                    font-weight: 600;
                }
                """
            )

    def show_connection_success(
        self,
        result: dict[str, Any],
        tested_at: str = "",
        tested_url: str = "",
    ) -> None:
        """Display a successful connection test."""

        self.set_connection_test_busy(False)

        self._last_tested_url = self._normalise_url(
            tested_url
            or self.system_url_input.text()
        )

        status_text = (
            "Connection Status: Successful"
        )

        if tested_at:
            status_text += (
                f"\nLast tested: {tested_at}"
            )

        self.connection_status_label.setText(
            status_text
        )

        self._set_success_style()

    def show_connection_warning(
        self,
        result: dict[str, Any],
        tested_at: str = "",
        tested_url: str = "",
    ) -> None:
        """Display a connection test that did not confirm login."""

        self.set_connection_test_busy(False)

        self._last_tested_url = self._normalise_url(
            tested_url
            or self.system_url_input.text()
        )

        system_name = (
            self.system_name_input.text().strip()
            or "A-SEAT"
        )

        message = str(
            result.get(
                "message",
                (
                    f"The {system_name} login page "
                    "was not confirmed."
                ),
            )
        )

        status_text = (
            "Connection Status: Failed"
        )

        if tested_at:
            status_text += (
                f"\nLast tested: {tested_at}"
            )

        status_text += (
            f"\n{message}"
        )

        self.connection_status_label.setText(
            status_text
        )

        self._set_failure_style()

    def show_connection_failure(
        self,
        message: str,
        tested_at: str = "",
        tested_url: str = "",
    ) -> None:
        """Display a failed connection test."""

        self.set_connection_test_busy(False)

        self._last_tested_url = self._normalise_url(
            tested_url
            or self.system_url_input.text()
        )

        status_text = (
            "Connection Status: Failed"
        )

        if tested_at:
            status_text += (
                f"\nLast tested: {tested_at}"
            )

        if message:
            status_text += (
                f"\n{message}"
            )

        self.connection_status_label.setText(
            status_text
        )

        self._set_failure_style()

    def show_connection_not_tested(
        self,
        different_address: bool = False,
    ) -> None:
        """Display a neutral connection status."""

        self.set_connection_test_busy(False)

        if different_address:
            text = (
                "Connection Status: "
                "Not tested for this address"
            )
        else:
            text = (
                "Connection Status: Not tested"
            )

        self.connection_status_label.setText(
            text
        )

        self.connection_status_label.setStyleSheet(
            """
            QLabel {
                background-color: transparent;
                font-weight: 600;
            }
            """
        )

    def _set_success_style(self) -> None:
        self.connection_status_label.setStyleSheet(
            """
            QLabel {
                color: #15803d;
                background-color: transparent;
                font-weight: 700;
            }
            """
        )

    def _set_failure_style(self) -> None:
        self.connection_status_label.setStyleSheet(
            """
            QLabel {
                color: #dc2626;
                background-color: transparent;
                font-weight: 700;
            }
            """
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
        system_name = (
            self.system_name_input.text().strip()
        )

        if not system_name:
            QMessageBox.warning(
                self,
                "System Name Required",
                "Enter the name of your system.",
            )

            self.system_name_input.setFocus()
            return

        settings: dict[str, Any] = {
            "theme": (
                self.theme_combo.currentText()
            ),
            "system_name": system_name,
            "aseat_url": (
                self.system_url_input.text().strip()
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