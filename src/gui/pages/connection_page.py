from collections.abc import Callable
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class ConnectionPage(QWidget):
    """Manage the active A-SEAT connection profile."""

    def __init__(
        self,
        on_save_profile: Callable[[dict[str, str]], dict[str, Any]],
        on_test_server: Callable[[dict[str, str]], None],
        on_authenticate: Callable[
            [dict[str, str], str, bool],
            None,
        ],
        on_disconnect: Callable[[], None],
        on_open_system: Callable[[], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._on_save_profile = on_save_profile
        self._on_test_server = on_test_server
        self._on_authenticate = on_authenticate
        self._on_disconnect = on_disconnect
        self._on_open_system = on_open_system

        self._active_profile_id = ""

        self.setObjectName("contentPage")

        self._build_interface()

    def _build_interface(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(
            QFrame.Shape.NoFrame
        )
        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        content = QWidget()
        content.setObjectName("contentPage")

        layout = QVBoxLayout(content)
        layout.setContentsMargins(
            34,
            30,
            34,
            34,
        )
        layout.setSpacing(18)

        heading = QLabel(
            "Connection"
        )
        heading.setObjectName(
            "pageHeading"
        )

        description = QLabel(
            "Configure and authenticate the active A-SEAT connection. "
            "Saved passwords are kept in Windows Credential Manager "
            "and never written to application configuration files."
        )
        description.setObjectName(
            "pageDescription"
        )
        description.setWordWrap(True)

        profile_card = QFrame()
        profile_card.setObjectName(
            "formCard"
        )

        profile_layout = QVBoxLayout(
            profile_card
        )
        profile_layout.setContentsMargins(
            24,
            22,
            24,
            24,
        )
        profile_layout.setSpacing(15)

        profile_title = QLabel(
            "Active Connection Profile"
        )
        profile_title.setObjectName(
            "cardValue"
        )

        profile_note = QLabel(
            "Only one profile is active in this phase. "
            "Support for switching between multiple profiles "
            "will be added later."
        )
        profile_note.setObjectName(
            "cardDescription"
        )
        profile_note.setWordWrap(True)

        profile_layout.addWidget(
            profile_title
        )
        profile_layout.addWidget(
            profile_note
        )

        form = QFormLayout()
        form.setHorizontalSpacing(24)
        form.setVerticalSpacing(14)

        self.profile_name_input = QLineEdit()
        self.profile_name_input.setPlaceholderText(
            "For example: Office A-SEAT"
        )

        self.system_name_input = QLineEdit()
        self.system_name_input.setPlaceholderText(
            "A-SEAT"
        )

        self.system_url_input = QLineEdit()
        self.system_url_input.setPlaceholderText(
            "https://example.org/system/"
        )

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText(
            "A-SEAT username"
        )

        form.addRow(
            "Profile name:",
            self.profile_name_input,
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
            "Username:",
            self.username_input,
        )

        profile_layout.addLayout(form)

        profile_buttons = QHBoxLayout()

        self.save_profile_button = QPushButton(
            "Save Profile"
        )
        self.save_profile_button.clicked.connect(
            self._save_profile
        )

        self.test_server_button = QPushButton(
            "Test Server"
        )
        self.test_server_button.clicked.connect(
            self._test_server
        )

        self.open_system_button = QPushButton(
            "Open A-SEAT"
        )
        self.open_system_button.clicked.connect(
            self._on_open_system
        )

        profile_buttons.addWidget(
            self.save_profile_button
        )
        profile_buttons.addWidget(
            self.test_server_button
        )
        profile_buttons.addWidget(
            self.open_system_button
        )
        profile_buttons.addStretch()

        profile_layout.addLayout(
            profile_buttons
        )

        self.server_status_label = QLabel(
            "Server status: Not tested"
        )
        self.server_status_label.setObjectName(
            "statusLabel"
        )
        self.server_status_label.setWordWrap(
            True
        )

        profile_layout.addWidget(
            self.server_status_label
        )

        authentication_card = QFrame()
        authentication_card.setObjectName(
            "formCard"
        )

        authentication_layout = QVBoxLayout(
            authentication_card
        )
        authentication_layout.setContentsMargins(
            24,
            22,
            24,
            24,
        )
        authentication_layout.setSpacing(
            15
        )

        authentication_title = QLabel(
            "Authentication"
        )
        authentication_title.setObjectName(
            "cardValue"
        )

        authentication_note = QLabel(
            "Authenticate after saving the profile. "
            "The five-day period starts only after A-SEAT confirms "
            "that the username and password are valid."
        )
        authentication_note.setObjectName(
            "cardDescription"
        )
        authentication_note.setWordWrap(
            True
        )

        authentication_layout.addWidget(
            authentication_title
        )
        authentication_layout.addWidget(
            authentication_note
        )

        authentication_form = QFormLayout()
        authentication_form.setHorizontalSpacing(
            24
        )
        authentication_form.setVerticalSpacing(
            14
        )

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )
        self.password_input.setPlaceholderText(
            "A-SEAT password"
        )

        authentication_form.addRow(
            "Password:",
            self.password_input,
        )

        authentication_layout.addLayout(
            authentication_form
        )

        self.remember_checkbox = QCheckBox(
            "Remember this credential securely for 5 days"
        )
        self.remember_checkbox.setChecked(
            True
        )

        authentication_layout.addWidget(
            self.remember_checkbox
        )

        authentication_buttons = QHBoxLayout()

        self.connect_button = QPushButton(
            "Connect"
        )
        self.connect_button.setObjectName(
            "primaryButton"
        )
        self.connect_button.clicked.connect(
            self._authenticate
        )

        self.disconnect_button = QPushButton(
            "Disconnect"
        )
        self.disconnect_button.clicked.connect(
            self._disconnect
        )

        authentication_buttons.addWidget(
            self.connect_button
        )
        authentication_buttons.addWidget(
            self.disconnect_button
        )
        authentication_buttons.addStretch()

        authentication_layout.addLayout(
            authentication_buttons
        )

        self.authentication_status_label = QLabel(
            "Authentication status: Required"
        )
        self.authentication_status_label.setObjectName(
            "statusLabel"
        )
        self.authentication_status_label.setWordWrap(
            True
        )

        authentication_layout.addWidget(
            self.authentication_status_label
        )

        layout.addWidget(heading)
        layout.addWidget(description)
        layout.addWidget(profile_card)
        layout.addWidget(
            authentication_card
        )
        layout.addStretch()

        scroll_area.setWidget(content)
        root_layout.addWidget(
            scroll_area
        )

    def profile_data(self) -> dict[str, str]:
        """Return the current connection-profile fields."""

        return {
            "profile_id": self._active_profile_id,
            "profile_name": (
                self.profile_name_input
                .text()
                .strip()
            ),
            "system_name": (
                self.system_name_input
                .text()
                .strip()
                or "A-SEAT"
            ),
            "configured_url": (
                self.system_url_input
                .text()
                .strip()
            ),
            "username": (
                self.username_input
                .text()
                .strip()
            ),
        }

    def load_profile(
        self,
        profile: dict[str, Any] | None,
        state: dict[str, Any] | None = None,
    ) -> None:
        """Display the active profile and credential state."""

        profile = profile or {}
        state = state or {}

        self._active_profile_id = str(
            profile.get(
                "profile_id",
                "",
            )
        )

        self.profile_name_input.setText(
            str(
                profile.get(
                    "profile_name",
                    "",
                )
            )
        )

        self.system_name_input.setText(
            str(
                profile.get(
                    "system_name",
                    "A-SEAT",
                )
            )
        )

        self.system_url_input.setText(
            str(
                profile.get(
                    "configured_url",
                    "",
                )
            )
        )

        self.username_input.setText(
            str(
                profile.get(
                    "username",
                    "",
                )
            )
        )

        self.show_authentication_state(
            state
        )

    def _validate_profile(
        self,
    ) -> dict[str, str] | None:
        profile = self.profile_data()

        if not profile["profile_name"]:
            QMessageBox.warning(
                self,
                "Profile Name Required",
                "Enter a connection profile name.",
            )
            self.profile_name_input.setFocus()
            return None

        if not profile["configured_url"]:
            QMessageBox.warning(
                self,
                "System Address Required",
                "Enter the A-SEAT system URL.",
            )
            self.system_url_input.setFocus()
            return None

        return profile

    def _save_profile(self) -> None:
        profile = self._validate_profile()

        if profile is None:
            return

        try:
            saved_profile = (
                self._on_save_profile(
                    profile
                )
            )

            self._active_profile_id = str(
                saved_profile.get(
                    "profile_id",
                    "",
                )
            )

            QMessageBox.information(
                self,
                "Connection Profile Saved",
                "The active connection profile has been saved.",
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Profile Could Not Be Saved",
                str(error),
            )

    def _test_server(self) -> None:
        profile = self._validate_profile()

        if profile is None:
            return

        self.set_server_test_busy(
            True
        )

        self._on_test_server(
            profile
        )

    def _authenticate(self) -> None:
        profile = self._validate_profile()

        if profile is None:
            return

        if not profile["username"]:
            QMessageBox.warning(
                self,
                "Username Required",
                "Enter the A-SEAT username.",
            )
            self.username_input.setFocus()
            return

        password = self.password_input.text()

        if not password:
            QMessageBox.warning(
                self,
                "Password Required",
                "Enter the A-SEAT password.",
            )
            self.password_input.setFocus()
            return

        self.set_authentication_busy(
            True
        )

        self._on_authenticate(
            profile,
            password,
            self.remember_checkbox.isChecked(),
        )

        self.password_input.clear()

    def _disconnect(self) -> None:
        self._on_disconnect()
        self.password_input.clear()

    def set_server_test_busy(
        self,
        busy: bool,
    ) -> None:
        self.test_server_button.setEnabled(
            not busy
        )
        self.test_server_button.setText(
            "Testing..."
            if busy
            else "Test Server"
        )

        if busy:
            self.server_status_label.setText(
                "Server status: Testing..."
            )

    def show_server_success(
        self,
        message: str,
    ) -> None:
        self.set_server_test_busy(
            False
        )

        self.server_status_label.setText(
            f"Server status: Reachable\n{message}"
        )

        self.server_status_label.setStyleSheet(
            "color: #15803d; font-weight: 700;"
        )

    def show_server_failure(
        self,
        message: str,
    ) -> None:
        self.set_server_test_busy(
            False
        )

        self.server_status_label.setText(
            f"Server status: Failed\n{message}"
        )

        self.server_status_label.setStyleSheet(
            "color: #dc2626; font-weight: 700;"
        )

    def set_authentication_busy(
        self,
        busy: bool,
    ) -> None:
        self.connect_button.setEnabled(
            not busy
        )
        self.disconnect_button.setEnabled(
            not busy
        )
        self.connect_button.setText(
            "Connecting..."
            if busy
            else "Connect"
        )

        if busy:
            self.authentication_status_label.setText(
                "Authentication status: Connecting..."
            )

    def show_authentication_success(
        self,
        *,
        remembered: bool,
        expires_at: str = "",
    ) -> None:
        self.set_authentication_busy(
            False
        )

        if remembered:
            text = (
                "Authentication status: Connected\n"
                "Credential stored securely for up to 5 days"
            )

            if expires_at:
                text += (
                    f"\nExpires: {expires_at}"
                )
        else:
            text = (
                "Authentication status: Verified\n"
                "Credential was not saved"
            )

        self.authentication_status_label.setText(
            text
        )

        self.authentication_status_label.setStyleSheet(
            "color: #15803d; font-weight: 700;"
        )

    def show_authentication_failure(
        self,
        message: str,
    ) -> None:
        self.set_authentication_busy(
            False
        )

        self.authentication_status_label.setText(
            "Authentication status: Failed\n"
            f"{message}"
        )

        self.authentication_status_label.setStyleSheet(
            "color: #dc2626; font-weight: 700;"
        )

    def show_authentication_state(
        self,
        state: dict[str, Any],
    ) -> None:
        status = str(
            state.get(
                "status",
                "authentication_required",
            )
        )

        expires_at = str(
            state.get(
                "expires_at",
                "",
            )
        )

        if status == "credential_stored":
            self.show_authentication_success(
                remembered=True,
                expires_at=expires_at,
            )
            return

        if status == "expired":
            self.authentication_status_label.setText(
                "Authentication status: Credential expired"
            )
            return

        self.authentication_status_label.setText(
            "Authentication status: Required"
        )
        self.authentication_status_label.setStyleSheet(
            ""
        )

    def show_disconnected(self) -> None:
        self.set_authentication_busy(
            False
        )
        self.authentication_status_label.setText(
            "Authentication status: Disconnected"
        )
        self.authentication_status_label.setStyleSheet(
            ""
        )
