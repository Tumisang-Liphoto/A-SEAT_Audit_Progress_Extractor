from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)


class LoginDialog(QDialog):
    """Collect the user's system login credentials."""

    def __init__(
        self,
        system_name: str = "A-SEAT",
        saved_username: str = "",
        remember_username: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.system_name = (
            system_name.strip()
            or "A-SEAT"
        )

        self.setWindowTitle(
            f"{self.system_name} Login"
        )
        self.setModal(True)
        self.setMinimumWidth(420)

        self._build_interface(
            saved_username=saved_username,
            remember_username=remember_username,
        )

    def _build_interface(
        self,
        saved_username: str,
        remember_username: bool,
    ) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            24,
            22,
            24,
            22,
        )
        layout.setSpacing(14)

        heading = QLabel(
            f"Enter your {self.system_name} credentials"
        )
        heading.setObjectName(
            "dialogHeading"
        )

        description = QLabel(
            "Your credentials will be used only for the "
            "current extraction."
        )
        description.setWordWrap(True)

        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText(
            f"Enter your {self.system_name} username"
        )
        self.username_input.setClearButtonEnabled(True)
        self.username_input.setText(
            saved_username.strip()
        )

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText(
            f"Enter your {self.system_name} password"
        )
        self.password_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        self.password_input.returnPressed.connect(
            self._validate_and_accept
        )

        form_layout.addRow(
            "Username:",
            self.username_input,
        )
        form_layout.addRow(
            "Password:",
            self.password_input,
        )

        self.remember_username_checkbox = QCheckBox(
            "Remember username on this device"
        )
        self.remember_username_checkbox.setChecked(
            remember_username
        )

        security_note = QLabel(
            "Your password will never be saved."
        )
        security_note.setObjectName(
            "statusLabel"
        )
        security_note.setWordWrap(True)
        security_note.setStyleSheet(
            """
            QLabel {
                background-color: transparent;
                font-size: 11px;
            }
            """
        )

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Ok
        )

        continue_button = self.button_box.button(
            QDialogButtonBox.StandardButton.Ok
        )

        if continue_button is not None:
            continue_button.setText(
                "Continue"
            )
            continue_button.setObjectName(
                "primaryButton"
            )

        self.button_box.accepted.connect(
            self._validate_and_accept
        )
        self.button_box.rejected.connect(
            self.reject
        )

        layout.addWidget(heading)
        layout.addWidget(description)
        layout.addLayout(form_layout)
        layout.addWidget(
            self.remember_username_checkbox
        )
        layout.addWidget(security_note)
        layout.addSpacing(4)
        layout.addWidget(self.button_box)

        if saved_username.strip():
            self.password_input.setFocus(
                Qt.FocusReason.OtherFocusReason
            )
        else:
            self.username_input.setFocus(
                Qt.FocusReason.OtherFocusReason
            )

    def _validate_and_accept(self) -> None:
        username = (
            self.username_input.text().strip()
        )
        password = (
            self.password_input.text()
        )

        if not username:
            QMessageBox.warning(
                self,
                "Username Required",
                (
                    f"Enter your {self.system_name} "
                    "username."
                ),
            )

            self.username_input.setFocus()
            return

        if not password:
            QMessageBox.warning(
                self,
                "Password Required",
                (
                    f"Enter your {self.system_name} "
                    "password."
                ),
            )

            self.password_input.setFocus()
            return

        self.accept()

    def credentials(
        self,
    ) -> tuple[str, str, bool]:
        """Return username, password and remember preference."""

        return (
            self.username_input.text().strip(),
            self.password_input.text(),
            self.remember_username_checkbox.isChecked(),
        )

    def clear_password(self) -> None:
        """Remove the password from the dialog field."""

        self.password_input.clear()