from collections.abc import Callable
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
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


class UserProfilePage(QWidget):
    """Edit user information separately from system settings."""

    def __init__(
        self,
        on_save: Callable[[dict[str, Any]], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._on_save = on_save

        self.setObjectName("contentPage")

        self._build_interface()

    def _build_interface(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(
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

        heading = QLabel("User Profile")
        heading.setObjectName("pageHeading")

        description = QLabel(
            "Maintain your personal and organisational information "
            "separately from A-SEAT connection and application settings."
        )
        description.setObjectName(
            "pageDescription"
        )
        description.setWordWrap(True)

        layout.addWidget(heading)
        layout.addWidget(description)

        identity_card = QFrame()
        identity_card.setObjectName(
            "formCard"
        )

        identity_layout = QVBoxLayout(
            identity_card
        )
        identity_layout.setContentsMargins(
            24,
            22,
            24,
            24,
        )
        identity_layout.setSpacing(15)

        identity_title = QLabel(
            "Personal Information"
        )
        identity_title.setObjectName(
            "cardValue"
        )

        identity_note = QLabel(
            "This information is stored only for the current Windows "
            "user and is not sent to A-SEAT automatically."
        )
        identity_note.setObjectName(
            "cardDescription"
        )
        identity_note.setWordWrap(True)

        identity_layout.addWidget(
            identity_title
        )
        identity_layout.addWidget(
            identity_note
        )

        identity_form = QFormLayout()
        identity_form.setHorizontalSpacing(
            24
        )
        identity_form.setVerticalSpacing(
            14
        )
        identity_form.setLabelAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.preferred_name_input = (
            QLineEdit()
        )
        self.preferred_name_input.setPlaceholderText(
            "Name shown in the application"
        )

        self.full_name_input = QLineEdit()
        self.full_name_input.setPlaceholderText(
            "Full name"
        )

        self.job_title_input = QLineEdit()
        self.job_title_input.setPlaceholderText(
            "Job title or role"
        )

        identity_form.addRow(
            "Preferred name:",
            self.preferred_name_input,
        )
        identity_form.addRow(
            "Full name:",
            self.full_name_input,
        )
        identity_form.addRow(
            "Job title:",
            self.job_title_input,
        )

        identity_layout.addLayout(
            identity_form
        )

        organisation_card = QFrame()
        organisation_card.setObjectName(
            "formCard"
        )

        organisation_layout = QVBoxLayout(
            organisation_card
        )
        organisation_layout.setContentsMargins(
            24,
            22,
            24,
            24,
        )
        organisation_layout.setSpacing(
            15
        )

        organisation_title = QLabel(
            "Organisation"
        )
        organisation_title.setObjectName(
            "cardValue"
        )

        organisation_note = QLabel(
            "These details can later be used in report headings, "
            "activity records and utility outputs."
        )
        organisation_note.setObjectName(
            "cardDescription"
        )
        organisation_note.setWordWrap(
            True
        )

        organisation_layout.addWidget(
            organisation_title
        )
        organisation_layout.addWidget(
            organisation_note
        )

        organisation_form = QFormLayout()
        organisation_form.setHorizontalSpacing(
            24
        )
        organisation_form.setVerticalSpacing(
            14
        )

        self.organisation_input = (
            QLineEdit()
        )
        self.organisation_input.setPlaceholderText(
            "Organisation or SAI"
        )

        self.directorate_input = QLineEdit()
        self.directorate_input.setPlaceholderText(
            "Directorate, department or unit"
        )

        organisation_form.addRow(
            "Organisation:",
            self.organisation_input,
        )
        organisation_form.addRow(
            "Directorate:",
            self.directorate_input,
        )

        organisation_layout.addLayout(
            organisation_form
        )

        contact_card = QFrame()
        contact_card.setObjectName(
            "formCard"
        )

        contact_layout = QVBoxLayout(
            contact_card
        )
        contact_layout.setContentsMargins(
            24,
            22,
            24,
            24,
        )
        contact_layout.setSpacing(15)

        contact_title = QLabel(
            "Contact Information"
        )
        contact_title.setObjectName(
            "cardValue"
        )

        contact_note = QLabel(
            "Contact details are optional and remain stored locally."
        )
        contact_note.setObjectName(
            "cardDescription"
        )
        contact_note.setWordWrap(True)

        contact_layout.addWidget(
            contact_title
        )
        contact_layout.addWidget(
            contact_note
        )

        contact_form = QFormLayout()
        contact_form.setHorizontalSpacing(
            24
        )
        contact_form.setVerticalSpacing(
            14
        )

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText(
            "name@example.org"
        )

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText(
            "Phone number"
        )

        contact_form.addRow(
            "Email address:",
            self.email_input,
        )
        contact_form.addRow(
            "Phone number:",
            self.phone_input,
        )

        contact_layout.addLayout(
            contact_form
        )

        button_row = QHBoxLayout()
        button_row.addStretch()

        self.clear_button = QPushButton(
            "Clear Form"
        )
        self.clear_button.clicked.connect(
            self.clear_form
        )

        self.save_button = QPushButton(
            "Save Profile"
        )
        self.save_button.setObjectName(
            "primaryButton"
        )
        self.save_button.clicked.connect(
            self._save_profile
        )

        button_row.addWidget(
            self.clear_button
        )
        button_row.addWidget(
            self.save_button
        )

        self.status_label = QLabel(
            "Profile status: Not saved"
        )
        self.status_label.setObjectName(
            "statusLabel"
        )
        self.status_label.setWordWrap(
            True
        )

        layout.addWidget(identity_card)
        layout.addWidget(
            organisation_card
        )
        layout.addWidget(contact_card)
        layout.addLayout(button_row)
        layout.addWidget(
            self.status_label
        )
        layout.addStretch()

        scroll_area.setWidget(content)
        outer_layout.addWidget(
            scroll_area
        )

    def load_profile(
        self,
        profile: dict[str, Any],
    ) -> None:
        """Populate the form from stored profile information."""

        self.preferred_name_input.setText(
            str(
                profile.get(
                    "preferred_name",
                    "",
                )
            )
        )

        self.full_name_input.setText(
            str(
                profile.get(
                    "full_name",
                    "",
                )
            )
        )

        self.job_title_input.setText(
            str(
                profile.get(
                    "job_title",
                    "",
                )
            )
        )

        self.organisation_input.setText(
            str(
                profile.get(
                    "organisation",
                    "",
                )
            )
        )

        self.directorate_input.setText(
            str(
                profile.get(
                    "directorate",
                    "",
                )
            )
        )

        self.email_input.setText(
            str(
                profile.get(
                    "email_address",
                    "",
                )
            )
        )

        self.phone_input.setText(
            str(
                profile.get(
                    "phone_number",
                    "",
                )
            )
        )

        has_profile = any(
            str(
                profile.get(
                    key,
                    "",
                )
            ).strip()
            for key in (
                "preferred_name",
                "full_name",
                "job_title",
                "organisation",
                "directorate",
                "email_address",
                "phone_number",
            )
        )

        self.status_label.setText(
            (
                "Profile status: Saved locally"
                if has_profile
                else "Profile status: Not completed"
            )
        )

    def profile_data(self) -> dict[str, str]:
        """Return the current form values."""

        return {
            "preferred_name": (
                self.preferred_name_input
                .text()
                .strip()
            ),
            "full_name": (
                self.full_name_input
                .text()
                .strip()
            ),
            "job_title": (
                self.job_title_input
                .text()
                .strip()
            ),
            "organisation": (
                self.organisation_input
                .text()
                .strip()
            ),
            "directorate": (
                self.directorate_input
                .text()
                .strip()
            ),
            "email_address": (
                self.email_input
                .text()
                .strip()
            ),
            "phone_number": (
                self.phone_input
                .text()
                .strip()
            ),
        }

    def _save_profile(self) -> None:
        """Validate and request profile saving."""

        profile = self.profile_data()

        email_address = profile[
            "email_address"
        ]

        if (
            email_address
            and (
                "@" not in email_address
                or "." not in email_address.rsplit(
                    "@",
                    1,
                )[-1]
            )
        ):
            QMessageBox.warning(
                self,
                "Email Address",
                "Enter a valid email address or leave the field blank.",
            )
            self.email_input.setFocus()
            return

        try:
            self._on_save(profile)
        except Exception as error:
            QMessageBox.critical(
                self,
                "Profile Could Not Be Saved",
                str(error),
            )
            return

        self.status_label.setText(
            "Profile status: Saved locally"
        )

        QMessageBox.information(
            self,
            "Profile Saved",
            "Your user profile has been saved successfully.",
        )

    def clear_form(self) -> None:
        """Clear visible fields without deleting saved data."""

        for field in (
            self.preferred_name_input,
            self.full_name_input,
            self.job_title_input,
            self.organisation_input,
            self.directorate_input,
            self.email_input,
            self.phone_input,
        ):
            field.clear()

        self.status_label.setText(
            "Profile status: Form cleared but not saved"
        )
