from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class ExtractionPage(QWidget):
    """Page used to extract audit progress information."""

    def __init__(
        self,
        on_open_system: Callable[[], None],
        on_start_extraction: Callable[[dict[str, Any]], None],
        system_name: str = "A-SEAT",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setObjectName("contentPage")

        self._on_open_system = on_open_system
        self._on_start_extraction = on_start_extraction

        self.system_name = (
            system_name.strip()
            or "A-SEAT"
        )

        self.output_paths: list[str] = []

        self._build_interface()
        self.set_system_name(
            self.system_name
        )

    def _build_interface(self) -> None:
        """Create the extraction page interface."""

        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(
            32,
            28,
            32,
            28,
        )
        page_layout.setSpacing(18)

        self.heading_label = QLabel(
            "Extract Audit Progress"
        )
        self.heading_label.setObjectName(
            "pageHeading"
        )

        self.description_label = QLabel()
        self.description_label.setObjectName(
            "pageDescription"
        )
        self.description_label.setWordWrap(True)

        extraction_card = QFrame()
        extraction_card.setObjectName(
            "formCard"
        )

        card_layout = QVBoxLayout(
            extraction_card
        )
        card_layout.setContentsMargins(
            30,
            26,
            30,
            26,
        )
        card_layout.setSpacing(18)

        form_layout = QFormLayout()
        form_layout.setSpacing(16)

        self.audit_year_input = QLineEdit()
        self.audit_year_input.setText(
            str(datetime.now().year)
        )
        self.audit_year_input.setPlaceholderText(
            "For example: 2026"
        )

        self.output_format_combo = QComboBox()
        self.output_format_combo.addItems(
            [
                "Excel Workbook",
                "CSV File",
                "Excel and CSV",
            ]
        )

        form_layout.addRow(
            "Audit year:",
            self.audit_year_input,
        )

        form_layout.addRow(
            "Output format:",
            self.output_format_combo,
        )

        self.browser_information_label = QLabel()
        self.browser_information_label.setWordWrap(
            True
        )
        self.browser_information_label.setObjectName(
            "statusLabel"
        )

        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)

        self.open_system_button = QPushButton()
        self.open_system_button.clicked.connect(
            self._on_open_system
        )

        self.start_extraction_button = QPushButton(
            "Start Extraction"
        )
        self.start_extraction_button.setObjectName(
            "primaryButton"
        )
        self.start_extraction_button.clicked.connect(
            self._request_extraction
        )

        self.open_result_button = QPushButton(
            "Open Result"
        )
        self.open_result_button.setEnabled(False)
        self.open_result_button.clicked.connect(
            self._open_result
        )

        button_layout.addWidget(
            self.open_system_button
        )
        button_layout.addWidget(
            self.start_extraction_button
        )
        button_layout.addWidget(
            self.open_result_button
        )
        button_layout.addStretch()

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(
            0,
            100,
        )
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)

        self.status_label = QLabel(
            "Status: Ready"
        )
        self.status_label.setObjectName(
            "statusLabel"
        )
        self.status_label.setWordWrap(True)

        activity_heading = QLabel(
            "Activity"
        )
        activity_heading.setObjectName(
            "sectionHeading"
        )

        self.activity_log = QTextEdit()
        self.activity_log.setReadOnly(True)
        self.activity_log.setMinimumHeight(220)

        card_layout.addLayout(
            form_layout
        )
        card_layout.addWidget(
            self.browser_information_label
        )
        card_layout.addLayout(
            button_layout
        )
        card_layout.addWidget(
            self.progress_bar
        )
        card_layout.addWidget(
            self.status_label
        )
        card_layout.addWidget(
            activity_heading
        )
        card_layout.addWidget(
            self.activity_log
        )

        page_layout.addWidget(
            self.heading_label
        )
        page_layout.addWidget(
            self.description_label
        )
        page_layout.addWidget(
            extraction_card
        )
        page_layout.addStretch()

    def set_system_name(
        self,
        system_name: str,
    ) -> None:
        """Update references to the configured system name."""

        self.system_name = (
            system_name.strip()
            or "A-SEAT"
        )

        self.description_label.setText(
            (
                "Extract the current audit list from "
                f"{self.system_name} and export it to Excel or CSV."
            )
        )

        self.open_system_button.setText(
            f"Open {self.system_name}"
        )

        self.browser_information_label.setText(
            (
                "The extraction will open a temporary Microsoft Edge "
                f"window, log in to {self.system_name}, collect the "
                "audit list and close the browser."
            )
        )

    def _request_extraction(self) -> None:
        """Validate the form and request an extraction."""

        audit_year = (
            self.audit_year_input.text().strip()
        )

        if audit_year and not audit_year.isdigit():
            QMessageBox.warning(
                self,
                "Invalid Audit Year",
                "Enter the audit year using numbers only.",
            )

            self.audit_year_input.setFocus()
            return

        selected_output_format = (
            self.output_format_combo.currentText().strip()
        )

        valid_output_formats = {
            "Excel Workbook",
            "CSV File",
            "Excel and CSV",
        }

        if (
            selected_output_format
            not in valid_output_formats
        ):
            QMessageBox.warning(
                self,
                "Output Format Required",
                "Select a valid output format.",
            )
            return

        request: dict[str, Any] = {
            "audit_year": audit_year,
            "output_format": selected_output_format,
        }

        self._on_start_extraction(
            request
        )

    def reset_progress(self) -> None:
        """Prepare the page for a new extraction."""

        self.output_paths = []

        self.progress_bar.setValue(0)

        self.status_label.setText(
            "Status: Preparing extraction..."
        )

        self.activity_log.clear()

        self.open_result_button.setEnabled(
            False
        )

    def update_progress(
        self,
        progress: int,
        message: str,
    ) -> None:
        """Update progress and add an activity message."""

        safe_progress = max(
            0,
            min(
                100,
                int(progress),
            ),
        )

        self.progress_bar.setValue(
            safe_progress
        )

        cleaned_message = str(
            message
        ).strip()

        if cleaned_message:
            self.status_label.setText(
                f"Status: {cleaned_message}"
            )

            self.activity_log.append(
                cleaned_message
            )

    def set_busy(
        self,
        busy: bool,
    ) -> None:
        """Enable or disable controls during extraction."""

        self.audit_year_input.setEnabled(
            not busy
        )

        self.output_format_combo.setEnabled(
            not busy
        )

        self.open_system_button.setEnabled(
            not busy
        )

        self.start_extraction_button.setEnabled(
            not busy
        )

        if busy:
            self.start_extraction_button.setText(
                "Extracting..."
            )
        else:
            self.start_extraction_button.setText(
                "Start Extraction"
            )

            if self.output_paths:
                self.open_result_button.setEnabled(
                    True
                )

    def show_completed(
        self,
        record_count: int,
        output_paths: list[str],
    ) -> None:
        """Display successful extraction details."""

        self.output_paths = [
            str(path)
            for path in output_paths
            if str(path).strip()
        ]

        self.progress_bar.setValue(100)

        self.status_label.setText(
            (
                "Status: Completed successfully — "
                f"{record_count} records extracted"
            )
        )

        self.activity_log.append(
            (
                "Extraction completed successfully. "
                f"{record_count} records were extracted."
            )
        )

        for output_path in self.output_paths:
            self.activity_log.append(
                f"Created: {output_path}"
            )

        self.open_result_button.setEnabled(
            bool(self.output_paths)
        )

    def show_failed(
        self,
        message: str,
    ) -> None:
        """Display a failed extraction."""

        self.status_label.setText(
            "Status: Extraction failed"
        )

        self.activity_log.append(
            f"Error: {message}"
        )

        self.open_result_button.setEnabled(
            bool(self.output_paths)
        )

    def _preferred_output_path(self) -> str:
        """Return the preferred output file."""

        for output_path in self.output_paths:
            if (
                Path(output_path).suffix.lower()
                in {".xlsx", ".xls"}
            ):
                return output_path

        for output_path in self.output_paths:
            if (
                Path(output_path).suffix.lower()
                == ".csv"
            ):
                return output_path

        if self.output_paths:
            return self.output_paths[0]

        return ""

    def _open_result(self) -> None:
        """Open the latest output file."""

        preferred_output = (
            self._preferred_output_path()
        )

        if not preferred_output:
            QMessageBox.warning(
                self,
                "No Result Available",
                "No extraction result is currently available.",
            )
            return

        output_path = Path(
            preferred_output
        )

        if not output_path.is_file():
            self.open_result_button.setEnabled(
                False
            )

            QMessageBox.warning(
                self,
                "File Not Found",
                (
                    "The output file may have been moved, "
                    "renamed or deleted."
                ),
            )
            return

        opened = QDesktopServices.openUrl(
            QUrl.fromLocalFile(
                str(output_path)
            )
        )

        if not opened:
            QMessageBox.critical(
                self,
                "Unable to Open Result",
                (
                    "The result could not be opened with "
                    "the default application."
                ),
            )