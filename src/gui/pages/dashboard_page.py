from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.utils.version import APP_VERSION


class DashboardPage(QWidget):
    """Application dashboard and latest extraction summary."""

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setObjectName("contentPage")

        self.latest_output_file = ""

        self._build_interface()

    def _build_interface(self) -> None:
        """Create the dashboard interface."""

        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(
            32,
            28,
            32,
            28,
        )
        page_layout.setSpacing(20)

        heading = QLabel("Dashboard")
        heading.setObjectName("pageHeading")

        description = QLabel(
            "View the application status and details "
            "of the latest successful extraction."
        )
        description.setObjectName("pageDescription")
        description.setWordWrap(True)

        cards_layout = QGridLayout()
        cards_layout.setHorizontalSpacing(18)
        cards_layout.setVerticalSpacing(18)
        cards_layout.setColumnStretch(0, 1)
        cards_layout.setColumnStretch(1, 1)

        application_card = self._create_card(
            "Application Status"
        )

        self.application_status_label = QLabel(
            "Ready"
        )
        self.application_status_label.setObjectName(
            "dashboardValue"
        )

        application_version_label = QLabel(
            f"Version {APP_VERSION}"
        )
        application_version_label.setObjectName(
            "dashboardDetail"
        )

        application_card.layout().addWidget(
            self.application_status_label
        )
        application_card.layout().addWidget(
            application_version_label
        )
        application_card.layout().addStretch()

        extraction_card = self._create_card(
            "Latest Extraction"
        )

        self.latest_extraction_label = QLabel(
            "No successful extraction recorded"
        )
        self.latest_extraction_label.setObjectName(
            "dashboardValue"
        )
        self.latest_extraction_label.setWordWrap(True)

        self.latest_record_count_label = QLabel(
            "Records extracted: 0"
        )
        self.latest_record_count_label.setObjectName(
            "dashboardDetail"
        )

        extraction_card.layout().addWidget(
            self.latest_extraction_label
        )
        extraction_card.layout().addWidget(
            self.latest_record_count_label
        )
        extraction_card.layout().addStretch()

        output_card = self._create_card(
            "Latest Output File"
        )

        self.latest_output_label = QLabel(
            "No file available"
        )
        self.latest_output_label.setObjectName(
            "dashboardValue"
        )
        self.latest_output_label.setWordWrap(True)
        self.latest_output_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        self.latest_output_path_label = QLabel("")
        self.latest_output_path_label.setObjectName(
            "dashboardDetail"
        )
        self.latest_output_path_label.setWordWrap(True)
        self.latest_output_path_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        self.open_latest_button = QPushButton(
            "Open Latest Result"
        )
        self.open_latest_button.setObjectName(
            "primaryButton"
        )
        self.open_latest_button.setEnabled(False)
        self.open_latest_button.setMaximumWidth(210)
        self.open_latest_button.setMinimumHeight(38)
        self.open_latest_button.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed,
        )
        self.open_latest_button.clicked.connect(
            self._open_latest_result
        )

        output_card.layout().addWidget(
            self.latest_output_label
        )
        output_card.layout().addWidget(
            self.latest_output_path_label
        )
        output_card.layout().addSpacing(8)
        output_card.layout().addWidget(
            self.open_latest_button,
            alignment=Qt.AlignmentFlag.AlignLeft,
        )
        output_card.layout().addStretch()

        cards_layout.addWidget(
            application_card,
            0,
            0,
        )
        cards_layout.addWidget(
            extraction_card,
            0,
            1,
        )
        cards_layout.addWidget(
            output_card,
            1,
            0,
            1,
            2,
        )

        page_layout.addWidget(heading)
        page_layout.addWidget(description)
        page_layout.addLayout(cards_layout)
        page_layout.addStretch()

        self.setStyleSheet(
            """
            QFrame#dashboardCard {
                background-color: palette(base);
                border: 1px solid palette(mid);
                border-radius: 12px;
            }

            QLabel#dashboardCardHeading {
                background-color: transparent;
                border: none;
                font-size: 14px;
                font-weight: 700;
                color: palette(text);
            }

            QLabel#dashboardValue {
                background-color: transparent;
                border: none;
                font-size: 17px;
                font-weight: 600;
                color: palette(text);
            }

            QLabel#dashboardDetail {
                background-color: transparent;
                border: none;
                font-size: 13px;
                color: palette(text);
            }

            QFrame#dashboardCard QPushButton {
                min-height: 38px;
                padding-left: 18px;
                padding-right: 18px;
            }
            """
        )

    def _create_card(
        self,
        title: str,
    ) -> QFrame:
        """Create a styled dashboard card."""

        card = QFrame()
        card.setObjectName("dashboardCard")
        card.setFrameShape(
            QFrame.Shape.NoFrame
        )
        card.setMinimumHeight(155)
        card.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(
            22,
            20,
            22,
            20,
        )
        card_layout.setSpacing(10)

        title_label = QLabel(title)
        title_label.setObjectName(
            "dashboardCardHeading"
        )

        card_layout.addWidget(title_label)
        card_layout.addSpacing(4)

        return card

    def restore_latest_result(
        self,
        output_file: str,
        completed_at: str,
        record_count: int,
    ) -> None:
        """Restore the latest successful extraction."""

        cleaned_path = output_file.strip()

        if not cleaned_path:
            self._show_no_output()
            return

        output_path = Path(cleaned_path)

        self.latest_extraction_label.setText(
            completed_at
            if completed_at
            else "Previous successful extraction"
        )

        self.latest_record_count_label.setText(
            f"Records extracted: {record_count}"
        )

        if output_path.is_file():
            self.latest_output_file = str(
                output_path
            )

            self.latest_output_label.setText(
                output_path.name
            )

            self.latest_output_path_label.setText(
                str(output_path.parent)
            )

            self.open_latest_button.setEnabled(
                True
            )
        else:
            self.latest_output_file = ""

            self.latest_output_label.setText(
                "The previous output file is no longer available"
            )

            self.latest_output_path_label.setText(
                cleaned_path
            )

            self.open_latest_button.setEnabled(
                False
            )

    def set_extraction_started(self) -> None:
        """Show that an extraction is running."""

        self.application_status_label.setText(
            "Extraction in progress"
        )

    def set_extraction_completed(
        self,
        record_count: int,
        completed_at: str,
        output_paths: list[str],
    ) -> None:
        """Show details of a successful extraction."""

        self.application_status_label.setText(
            "Ready"
        )

        preferred_output = (
            self._select_preferred_output(
                output_paths
            )
        )

        self.latest_extraction_label.setText(
            completed_at
        )

        self.latest_record_count_label.setText(
            f"Records extracted: {record_count}"
        )

        if preferred_output:
            output_path = Path(
                preferred_output
            )

            self.latest_output_file = str(
                output_path
            )

            self.latest_output_label.setText(
                output_path.name
            )

            self.latest_output_path_label.setText(
                str(output_path.parent)
            )

            self.open_latest_button.setEnabled(
                output_path.is_file()
            )
        else:
            self._show_no_output()

    def set_extraction_failed(
        self,
        message: str,
    ) -> None:
        """
        Show that the latest attempt failed without removing
        the last successful output.
        """

        self.application_status_label.setText(
            "Latest extraction failed"
        )

    def _show_no_output(self) -> None:
        """Reset the latest-output display."""

        self.latest_output_file = ""

        self.latest_output_label.setText(
            "No file available"
        )

        self.latest_output_path_label.clear()

        self.open_latest_button.setEnabled(
            False
        )

    @staticmethod
    def _select_preferred_output(
        output_paths: list[str],
    ) -> str:
        """Prefer Excel and use CSV when Excel is unavailable."""

        cleaned_paths = [
            str(path).strip()
            for path in output_paths
            if str(path).strip()
        ]

        for path in cleaned_paths:
            if Path(path).suffix.lower() in {
                ".xlsx",
                ".xls",
            }:
                return path

        for path in cleaned_paths:
            if Path(path).suffix.lower() == ".csv":
                return path

        if cleaned_paths:
            return cleaned_paths[0]

        return ""

    def _open_latest_result(self) -> None:
        """Open the latest successful output file."""

        if not self.latest_output_file:
            QMessageBox.warning(
                self,
                "No Output File",
                "No latest output file is available.",
            )
            return

        output_path = Path(
            self.latest_output_file
        )

        if not output_path.is_file():
            self.latest_output_file = ""

            self.latest_output_label.setText(
                "The previous output file is no longer available"
            )

            self.open_latest_button.setEnabled(
                False
            )

            QMessageBox.warning(
                self,
                "File Not Found",
                (
                    "The latest output file may have been "
                    "moved, renamed or deleted."
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
                "Unable to Open File",
                (
                    "The output file could not be opened "
                    "with the default application."
                ),
            )