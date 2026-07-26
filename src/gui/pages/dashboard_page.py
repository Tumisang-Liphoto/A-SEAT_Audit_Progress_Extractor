from pathlib import Path
from typing import Any

import qtawesome as qta
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.utils.version import APP_VERSION


class DashboardPage(QWidget):
    """Application dashboard and latest extraction comparison."""

    STATUS_FILTERS = {
        "All movements": "",
        "Progressed": "progressed",
        "No change": "unchanged",
        "Regressed": "regressed",
        "New audits": "new",
        "No longer listed": "missing",
        "Not comparable": "not_comparable",
    }

    DELIVERY_FILTERS = {
        "All delivery statuses": "",
        "Completed": "completed",
        "Overdue": "overdue",
        "Due soon": "due_soon",
        "Not started late": "not_started_late",
        "In progress": "in_progress",
        "Not yet started": "not_yet_started",
        "Data issues": "__data_issues__",
        "Not currently listed": "not_currently_listed",
    }

    DATA_ISSUE_STATUSES = {
        "missing_progress",
        "invalid_progress",
        "progress_year_mismatch",
        "missing_dates",
        "invalid_dates",
    }

    STATUS_LABELS = {
        "progressed": "Progressed",
        "unchanged": "No change",
        "regressed": "Regressed",
        "new": "New audit",
        "missing": "No longer listed",
        "not_comparable": "Not comparable",
    }

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setObjectName("contentPage")
        self.latest_output_file = ""
        self.comparison_rows: list[dict[str, Any]] = []
        self.details_visible = False

        self._build_interface()

    def _build_interface(self) -> None:
        """Create the dashboard interface."""

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        content_widget = QWidget()
        content_widget.setObjectName("contentPage")

        page_layout = QVBoxLayout(content_widget)
        page_layout.setContentsMargins(32, 28, 32, 28)
        page_layout.setSpacing(20)

        heading = QLabel("Dashboard")
        heading.setObjectName("pageHeading")

        description = QLabel(
            "View the application status, latest extraction "
            "and changes between the two most recent extracts."
        )
        description.setObjectName("pageDescription")
        description.setWordWrap(True)

        page_layout.addWidget(heading)
        page_layout.addWidget(description)

        summary_layout = QGridLayout()
        summary_layout.setHorizontalSpacing(18)
        summary_layout.setVerticalSpacing(18)
        summary_layout.setColumnStretch(0, 1)
        summary_layout.setColumnStretch(1, 1)

        application_card = self._create_standard_card(
            "Application Status"
        )

        self.application_status_label = QLabel("Ready")
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

        extraction_card = self._create_standard_card(
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

        output_card = self._create_standard_card(
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

        summary_layout.addWidget(
            application_card,
            0,
            0,
        )
        summary_layout.addWidget(
            extraction_card,
            0,
            1,
        )
        summary_layout.addWidget(
            output_card,
            1,
            0,
            1,
            2,
        )

        page_layout.addLayout(summary_layout)

        comparison_frame = QFrame()
        comparison_frame.setObjectName(
            "comparisonContainer"
        )

        comparison_layout = QVBoxLayout(
            comparison_frame
        )
        comparison_layout.setContentsMargins(
            22,
            20,
            22,
            20,
        )
        comparison_layout.setSpacing(16)

        comparison_header = QHBoxLayout()
        comparison_header.setSpacing(12)

        comparison_title_layout = QVBoxLayout()
        comparison_title_layout.setSpacing(4)

        comparison_heading = QLabel(
            "Audit Progress Comparison"
        )
        comparison_heading.setObjectName(
            "comparisonHeading"
        )

        self.comparison_date_label = QLabel(
            "No previous extraction is available for comparison."
        )
        self.comparison_date_label.setObjectName(
            "dashboardDetail"
        )
        self.comparison_date_label.setWordWrap(True)

        comparison_title_layout.addWidget(
            comparison_heading
        )
        comparison_title_layout.addWidget(
            self.comparison_date_label
        )

        self.view_details_button = QPushButton(
            "View Details"
        )
        self.view_details_button.setEnabled(False)
        self.view_details_button.setMinimumHeight(36)
        self.view_details_button.clicked.connect(
            self._toggle_details
        )

        comparison_header.addLayout(
            comparison_title_layout,
            1,
        )
        comparison_header.addWidget(
            self.view_details_button,
            alignment=Qt.AlignmentFlag.AlignTop,
        )

        comparison_layout.addLayout(
            comparison_header
        )

        cards_layout = QGridLayout()
        cards_layout.setHorizontalSpacing(12)
        cards_layout.setVerticalSpacing(12)

        for column in range(3):
            cards_layout.setColumnStretch(
                column,
                1,
            )

        (
            audits_card,
            self.audits_compared_value,
            self.audits_compared_detail,
        ) = self._create_metric_card(
            title="Audits compared",
            icon_name="fa5s.th-large",
        )

        (
            progressed_card,
            self.progressed_value,
            self.progressed_detail,
        ) = self._create_metric_card(
            title="Progressed",
            icon_name="fa5s.chart-line",
        )

        (
            unchanged_card,
            self.unchanged_value,
            self.unchanged_detail,
        ) = self._create_metric_card(
            title="No change",
            icon_name="fa5s.arrows-alt-h",
        )

        (
            regressed_card,
            self.regressed_value,
            self.regressed_detail,
        ) = self._create_metric_card(
            title="Regressed",
            icon_name="fa5s.arrow-down",
        )

        (
            new_card,
            self.new_value,
            self.new_detail,
        ) = self._create_metric_card(
            title="New audits",
            icon_name="fa5s.plus-circle",
        )

        (
            missing_card,
            self.missing_value,
            self.missing_detail,
        ) = self._create_metric_card(
            title="Missing audits",
            icon_name="fa5s.exclamation-circle",
        )

        (
            not_comparable_card,
            self.not_comparable_value,
            self.not_comparable_detail,
        ) = self._create_metric_card(
            title="Not comparable",
            icon_name="fa5s.question-circle",
        )

        cards_layout.addWidget(
            audits_card,
            0,
            0,
        )
        cards_layout.addWidget(
            progressed_card,
            0,
            1,
        )
        cards_layout.addWidget(
            unchanged_card,
            0,
            2,
        )
        cards_layout.addWidget(
            regressed_card,
            1,
            0,
        )
        cards_layout.addWidget(
            new_card,
            1,
            1,
        )
        cards_layout.addWidget(
            missing_card,
            1,
            2,
        )
        cards_layout.addWidget(
            not_comparable_card,
            2,
            0,
            1,
            3,
        )

        comparison_layout.addLayout(
            cards_layout
        )

        delivery_heading = QLabel(
            "Current Delivery Status"
        )
        delivery_heading.setObjectName(
            "comparisonDetailsHeading"
        )

        self.delivery_date_label = QLabel(
            "Delivery status will be assessed after a comparison is available."
        )
        self.delivery_date_label.setObjectName(
            "dashboardDetail"
        )
        self.delivery_date_label.setWordWrap(True)

        comparison_layout.addWidget(
            delivery_heading
        )
        comparison_layout.addWidget(
            self.delivery_date_label
        )

        delivery_cards_layout = QGridLayout()
        delivery_cards_layout.setHorizontalSpacing(12)
        delivery_cards_layout.setVerticalSpacing(12)

        for column in range(3):
            delivery_cards_layout.setColumnStretch(
                column,
                1,
            )

        (
            completed_card,
            self.completed_value,
            self.completed_detail,
        ) = self._create_metric_card(
            title="Completed",
            icon_name="fa5s.check-circle",
        )

        (
            overdue_card,
            self.overdue_value,
            self.overdue_detail,
        ) = self._create_metric_card(
            title="Overdue",
            icon_name="fa5s.clock",
        )

        (
            due_soon_card,
            self.due_soon_value,
            self.due_soon_detail,
        ) = self._create_metric_card(
            title="Due soon",
            icon_name="fa5s.hourglass-half",
        )

        (
            not_started_late_card,
            self.not_started_late_value,
            self.not_started_late_detail,
        ) = self._create_metric_card(
            title="Not started late",
            icon_name="fa5s.pause-circle",
        )

        (
            in_progress_card,
            self.in_progress_value,
            self.in_progress_detail,
        ) = self._create_metric_card(
            title="In progress",
            icon_name="fa5s.tasks",
        )

        (
            data_issues_card,
            self.data_issues_value,
            self.data_issues_detail,
        ) = self._create_metric_card(
            title="Data issues",
            icon_name="fa5s.exclamation-triangle",
        )

        delivery_cards_layout.addWidget(
            completed_card,
            0,
            0,
        )
        delivery_cards_layout.addWidget(
            overdue_card,
            0,
            1,
        )
        delivery_cards_layout.addWidget(
            due_soon_card,
            0,
            2,
        )
        delivery_cards_layout.addWidget(
            not_started_late_card,
            1,
            0,
        )
        delivery_cards_layout.addWidget(
            in_progress_card,
            1,
            1,
        )
        delivery_cards_layout.addWidget(
            data_issues_card,
            1,
            2,
        )

        comparison_layout.addLayout(
            delivery_cards_layout
        )

        self.comparison_message_label = QLabel(
            "Complete another successful extraction to view progress changes."
        )
        self.comparison_message_label.setObjectName(
            "comparisonMessage"
        )
        self.comparison_message_label.setWordWrap(True)

        comparison_layout.addWidget(
            self.comparison_message_label
        )

        self.details_container = QWidget()
        self.details_container.setVisible(False)

        details_layout = QVBoxLayout(
            self.details_container
        )
        details_layout.setContentsMargins(
            0,
            4,
            0,
            0,
        )
        details_layout.setSpacing(12)

        filter_layout = QHBoxLayout()

        details_heading = QLabel(
            "Audit-Level Analysis"
        )
        details_heading.setObjectName(
            "comparisonDetailsHeading"
        )

        movement_filter_label = QLabel(
            "Movement:"
        )

        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItems(
            list(
                self.STATUS_FILTERS.keys()
            )
        )
        self.status_filter_combo.setMaximumWidth(
            190
        )
        self.status_filter_combo.currentTextChanged.connect(
            self._apply_comparison_filter
        )

        delivery_filter_label = QLabel(
            "Delivery:"
        )

        self.delivery_filter_combo = QComboBox()
        self.delivery_filter_combo.addItems(
            list(
                self.DELIVERY_FILTERS.keys()
            )
        )
        self.delivery_filter_combo.setMaximumWidth(
            210
        )
        self.delivery_filter_combo.currentTextChanged.connect(
            self._apply_comparison_filter
        )

        filter_layout.addWidget(
            details_heading
        )
        filter_layout.addStretch()
        filter_layout.addWidget(
            movement_filter_label
        )
        filter_layout.addWidget(
            self.status_filter_combo
        )
        filter_layout.addWidget(
            delivery_filter_label
        )
        filter_layout.addWidget(
            self.delivery_filter_combo
        )

        self.comparison_table = QTableWidget()
        self.comparison_table.setColumnCount(9)
        self.comparison_table.setHorizontalHeaderLabels(
            [
                "Auditee",
                "Audit Name",
                "Audit Lead",
                "Planned Completion",
                "Previous",
                "Current",
                "Movement",
                "Delivery Status",
                "Issue",
            ]
        )
        self.comparison_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.comparison_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.comparison_table.setAlternatingRowColors(
            True
        )
        self.comparison_table.setWordWrap(True)
        self.comparison_table.verticalHeader().setVisible(
            False
        )
        self.comparison_table.setMinimumHeight(
            260
        )

        header = self.comparison_table.horizontalHeader()
        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.Stretch,
        )
        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            5,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            6,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            7,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            8,
            QHeaderView.ResizeMode.Stretch,
        )

        details_layout.addLayout(
            filter_layout
        )
        details_layout.addWidget(
            self.comparison_table
        )

        comparison_layout.addWidget(
            self.details_container
        )

        page_layout.addWidget(
            comparison_frame
        )
        page_layout.addStretch()

        scroll_area.setWidget(
            content_widget
        )

        root_layout.addWidget(
            scroll_area
        )

        self.setStyleSheet(
            """
            QFrame#dashboardCard,
            QFrame#comparisonContainer,
            QFrame#comparisonMetricCard {
                background-color: palette(base);
                border: 1px solid palette(mid);
                border-radius: 12px;
            }

            QLabel#dashboardCardHeading,
            QLabel#comparisonHeading,
            QLabel#comparisonDetailsHeading {
                background-color: transparent;
                border: none;
                font-size: 14px;
                font-weight: 700;
                color: palette(text);
            }

            QLabel#comparisonHeading {
                font-size: 16px;
            }

            QLabel#dashboardValue {
                background-color: transparent;
                border: none;
                font-size: 17px;
                font-weight: 600;
                color: palette(text);
            }

            QLabel#dashboardDetail,
            QLabel#metricDetail {
                background-color: transparent;
                border: none;
                font-size: 13px;
                color: palette(text);
            }

            QLabel#metricTitle {
                background-color: transparent;
                border: none;
                font-size: 13px;
                font-weight: 600;
                color: palette(text);
            }

            QLabel#metricValue {
                background-color: transparent;
                border: none;
                font-size: 25px;
                font-weight: 700;
                color: palette(text);
            }

            QLabel#metricIcon {
                background-color: palette(alternate-base);
                border: 1px solid palette(mid);
                border-radius: 10px;
                padding: 8px;
            }

            QLabel#comparisonMessage {
                background-color: palette(alternate-base);
                border: 1px solid palette(mid);
                border-radius: 9px;
                padding: 12px;
                color: palette(text);
            }

            QFrame#dashboardCard QPushButton {
                min-height: 38px;
                padding-left: 18px;
                padding-right: 18px;
            }

            QTableWidget {
                border: 1px solid palette(mid);
                border-radius: 8px;
                gridline-color: palette(mid);
                background-color: palette(base);
                alternate-background-color: palette(alternate-base);
            }

            QHeaderView::section {
                background-color: palette(alternate-base);
                color: palette(text);
                border: none;
                border-right: 1px solid palette(mid);
                border-bottom: 1px solid palette(mid);
                padding: 8px;
                font-weight: 700;
            }
            """
        )

    def _create_standard_card(
        self,
        title: str,
    ) -> QFrame:
        """Create one of the existing dashboard cards."""

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

        card_layout.addWidget(
            title_label
        )
        card_layout.addSpacing(4)

        return card

    def _create_metric_card(
        self,
        *,
        title: str,
        icon_name: str,
    ) -> tuple[QFrame, QLabel, QLabel]:
        """Create a comparison summary card."""

        card = QFrame()
        card.setObjectName(
            "comparisonMetricCard"
        )
        card.setMinimumHeight(120)
        card.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        card_layout = QHBoxLayout(
            card
        )
        card_layout.setContentsMargins(
            16,
            15,
            16,
            15,
        )
        card_layout.setSpacing(12)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setObjectName(
            "metricTitle"
        )
        title_label.setWordWrap(True)

        value_label = QLabel("0")
        value_label.setObjectName(
            "metricValue"
        )

        detail_label = QLabel(
            "No comparison available"
        )
        detail_label.setObjectName(
            "metricDetail"
        )
        detail_label.setWordWrap(True)

        text_layout.addWidget(
            title_label
        )
        text_layout.addWidget(
            value_label
        )
        text_layout.addWidget(
            detail_label
        )
        text_layout.addStretch()

        icon_label = QLabel()
        icon_label.setObjectName(
            "metricIcon"
        )
        icon_label.setFixedSize(
            46,
            46,
        )
        icon_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        try:
            icon_label.setPixmap(
                qta.icon(
                    icon_name,
                    color="#4f7cff",
                ).pixmap(
                    23,
                    23,
                )
            )
        except Exception:
            icon_label.setText("•")

        card_layout.addLayout(
            text_layout,
            1,
        )
        card_layout.addWidget(
            icon_label,
            alignment=Qt.AlignmentFlag.AlignTop,
        )

        return (
            card,
            value_label,
            detail_label,
        )

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

    def show_comparison(
        self,
        comparison: dict[str, Any],
    ) -> None:
        """Display comparison results from the latest two snapshots."""

        if not bool(
            comparison.get(
                "has_comparison",
                False,
            )
        ):
            self.comparison_rows = []
            self._set_comparison_values(
                audits_compared=0,
                progressed=0,
                unchanged=0,
                regressed=0,
                new=0,
                missing=0,
                not_comparable=0,
            )
            self._set_delivery_values(
                completed=0,
                overdue=0,
                due_soon=0,
                not_started_late=0,
                in_progress=0,
                data_issues=0,
            )

            self.comparison_date_label.setText(
                "No previous extraction is available for comparison."
            )
            self.comparison_message_label.setText(
                "Complete another successful extraction to view "
                "progress changes."
            )
            self.view_details_button.setEnabled(
                False
            )
            self._hide_details()
            return

        summary = comparison.get(
            "summary",
            {},
        )

        audits_compared = self._safe_int(
            summary.get(
                "audits_compared",
                0,
            )
        )
        progressed = self._safe_int(
            summary.get(
                "progressed",
                0,
            )
        )
        unchanged = self._safe_int(
            summary.get(
                "unchanged",
                0,
            )
        )
        regressed = self._safe_int(
            summary.get(
                "regressed",
                0,
            )
        )
        new = self._safe_int(
            summary.get(
                "new",
                0,
            )
        )
        missing = self._safe_int(
            summary.get(
                "missing",
                0,
            )
        )
        not_comparable = self._safe_int(
            summary.get(
                "not_comparable",
                0,
            )
        )

        self._set_comparison_values(
            audits_compared=audits_compared,
            progressed=progressed,
            unchanged=unchanged,
            regressed=regressed,
            new=new,
            missing=missing,
            not_comparable=not_comparable,
        )

        delivery_summary = comparison.get(
            "delivery_summary",
            {},
        )

        completed = self._safe_int(
            delivery_summary.get(
                "completed",
                0,
            )
        )
        overdue = self._safe_int(
            delivery_summary.get(
                "overdue",
                0,
            )
        )
        due_soon = self._safe_int(
            delivery_summary.get(
                "due_soon",
                0,
            )
        )
        not_started_late = self._safe_int(
            delivery_summary.get(
                "not_started_late",
                0,
            )
        )
        in_progress = self._safe_int(
            delivery_summary.get(
                "in_progress",
                0,
            )
        )
        data_issues = sum(
            self._safe_int(
                delivery_summary.get(
                    key,
                    0,
                )
            )
            for key in self.DATA_ISSUE_STATUSES
        )

        self._set_delivery_values(
            completed=completed,
            overdue=overdue,
            due_soon=due_soon,
            not_started_late=not_started_late,
            in_progress=in_progress,
            data_issues=data_issues,
        )

        assessment_date = str(
            comparison.get(
                "assessment_display_date",
                "",
            )
        ).strip()

        self.delivery_date_label.setText(
            (
                "Status assessed as at "
                f"{assessment_date}."
                if assessment_date
                else "Status assessed using the latest extraction date."
            )
        )

        previous_date = str(
            comparison.get(
                "previous_display_date",
                "",
            )
        ).strip()

        current_date = str(
            comparison.get(
                "current_display_date",
                "",
            )
        ).strip()

        self.comparison_date_label.setText(
            f"{previous_date or 'Previous extraction'} compared with "
            f"{current_date or 'latest extraction'}"
        )

        try:
            average_value = float(
                comparison.get(
                    "average_movement",
                    0,
                )
            )
        except (TypeError, ValueError):
            average_value = 0.0

        movement_prefix = (
            "+"
            if average_value > 0
            else ""
        )

        self.comparison_message_label.setText(
            "Average movement across comparable audits: "
            f"{movement_prefix}{average_value:g} percentage points."
        )

        rows = comparison.get(
            "rows",
            [],
        )

        self.comparison_rows = [
            dict(row)
            for row in rows
            if isinstance(
                row,
                dict,
            )
        ]

        self.view_details_button.setEnabled(
            bool(
                self.comparison_rows
            )
        )

        self._populate_comparison_table(
            self.comparison_rows
        )

    def show_comparison_error(
        self,
        message: str,
    ) -> None:
        """Show a non-fatal comparison processing error."""

        self.comparison_rows = []
        self._set_comparison_values(
            audits_compared=0,
            progressed=0,
            unchanged=0,
            regressed=0,
            new=0,
            missing=0,
            not_comparable=0,
        )
        self._set_delivery_values(
            completed=0,
            overdue=0,
            due_soon=0,
            not_started_late=0,
            in_progress=0,
            data_issues=0,
        )

        self.comparison_date_label.setText(
            "The latest comparison could not be loaded."
        )
        self.comparison_message_label.setText(
            message
            or "An unknown comparison error occurred."
        )
        self.view_details_button.setEnabled(
            False
        )
        self._hide_details()

    def _set_comparison_values(
        self,
        *,
        audits_compared: int,
        progressed: int,
        unchanged: int,
        regressed: int,
        new: int,
        missing: int,
        not_comparable: int,
    ) -> None:
        """Update the movement comparison cards."""

        self.audits_compared_value.setText(
            str(audits_compared)
        )
        self.progressed_value.setText(
            str(progressed)
        )
        self.unchanged_value.setText(
            str(unchanged)
        )
        self.regressed_value.setText(
            str(regressed)
        )
        self.new_value.setText(
            str(new)
        )
        self.missing_value.setText(
            str(missing)
        )
        self.not_comparable_value.setText(
            str(not_comparable)
        )

        comparable_total = (
            progressed
            + unchanged
            + regressed
        )

        self.audits_compared_detail.setText(
            "Present in both extracts"
        )
        self.progressed_detail.setText(
            self._percentage_detail(
                progressed,
                comparable_total,
            )
        )
        self.unchanged_detail.setText(
            self._percentage_detail(
                unchanged,
                comparable_total,
            )
        )
        self.regressed_detail.setText(
            (
                "Needs review"
                if regressed
                else "No regression detected"
            )
        )
        self.new_detail.setText(
            (
                "First seen in latest extract"
                if new
                else "No new audits"
            )
        )
        self.missing_detail.setText(
            (
                "Not found in latest extract"
                if missing
                else "No audits removed"
            )
        )
        self.not_comparable_detail.setText(
            (
                "Progress requires review"
                if not_comparable
                else "All progress is comparable"
            )
        )

    def _set_delivery_values(
        self,
        *,
        completed: int,
        overdue: int,
        due_soon: int,
        not_started_late: int,
        in_progress: int,
        data_issues: int,
    ) -> None:
        """Update current delivery-status cards."""

        self.completed_value.setText(
            str(completed)
        )
        self.overdue_value.setText(
            str(overdue)
        )
        self.due_soon_value.setText(
            str(due_soon)
        )
        self.not_started_late_value.setText(
            str(not_started_late)
        )
        self.in_progress_value.setText(
            str(in_progress)
        )
        self.data_issues_value.setText(
            str(data_issues)
        )

        self.completed_detail.setText(
            "Progress recorded at 100%"
        )
        self.overdue_detail.setText(
            (
                "Requires management attention"
                if overdue
                else "No overdue audits"
            )
        )
        self.due_soon_detail.setText(
            (
                "Due within 30 days"
                if due_soon
                else "No audits due soon"
            )
        )
        self.not_started_late_detail.setText(
            (
                "Start date passed at 0%"
                if not_started_late
                else "No late starts"
            )
        )
        self.in_progress_detail.setText(
            "Started and not yet completed"
        )
        self.data_issues_detail.setText(
            (
                "Progress or date data needs review"
                if data_issues
                else "No data issues detected"
            )
        )

    @staticmethod
    def _percentage_detail(
        value: int,
        total: int,
    ) -> str:
        if total <= 0:
            return "0% of comparable audits"

        percentage = round(
            value / total * 100
        )

        return (
            f"{percentage}% of comparable audits"
        )

    def _toggle_details(self) -> None:
        """Show or hide the detailed comparison table."""

        if not self.comparison_rows:
            return

        self.details_visible = (
            not self.details_visible
        )

        self.details_container.setVisible(
            self.details_visible
        )

        self.view_details_button.setText(
            "Hide Details"
            if self.details_visible
            else "View Details"
        )

        if self.details_visible:
            self._apply_comparison_filter()

    def _hide_details(self) -> None:
        self.details_visible = False
        self.details_container.setVisible(
            False
        )
        self.view_details_button.setText(
            "View Details"
        )

    def _apply_comparison_filter(
        self,
        *_: Any,
    ) -> None:
        """Filter by movement and delivery status."""

        selected_status = (
            self.STATUS_FILTERS.get(
                self.status_filter_combo.currentText(),
                "",
            )
        )

        selected_delivery = (
            self.DELIVERY_FILTERS.get(
                self.delivery_filter_combo.currentText(),
                "",
            )
        )

        filtered_rows: list[dict[str, Any]] = []

        for row in self.comparison_rows:
            row_status = str(
                row.get(
                    "status",
                    "",
                )
            )
            delivery_status = str(
                row.get(
                    "delivery_status",
                    "",
                )
            )

            if (
                selected_status
                and row_status != selected_status
            ):
                continue

            if selected_delivery == "__data_issues__":
                if (
                    delivery_status
                    not in self.DATA_ISSUE_STATUSES
                ):
                    continue
            elif (
                selected_delivery
                and delivery_status != selected_delivery
            ):
                continue

            filtered_rows.append(
                row
            )

        self._populate_comparison_table(
            filtered_rows
        )

    def _populate_comparison_table(
        self,
        rows: list[dict[str, Any]],
    ) -> None:
        """Populate the audit-level comparison table."""

        self.comparison_table.setRowCount(
            len(rows)
        )

        for row_index, row in enumerate(rows):
            values = [
                row.get(
                    "Auditee Name",
                    "",
                ),
                row.get(
                    "Audit Name",
                    "",
                ),
                row.get(
                    "Audit Lead",
                    "",
                ),
                row.get(
                    "Planned Completion Date",
                    "",
                ),
                row.get(
                    "previous_progress",
                    "",
                ),
                row.get(
                    "current_progress",
                    "",
                ),
                row.get(
                    "movement_text",
                    "",
                ),
                row.get(
                    "delivery_status_label",
                    "",
                ),
                row.get(
                    "delivery_issue",
                    "",
                ),
            ]

            for column_index, value in enumerate(
                values
            ):
                item = QTableWidgetItem(
                    str(value)
                )

                if column_index in {
                    3,
                    4,
                    5,
                    6,
                    7,
                }:
                    item.setTextAlignment(
                        int(
                            Qt.AlignmentFlag.AlignCenter
                            | Qt.AlignmentFlag.AlignVCenter
                        )
                    )

                self.comparison_table.setItem(
                    row_index,
                    column_index,
                    item,
                )

        self.comparison_table.resizeRowsToContents()

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
        """Show a failed extraction without removing prior results."""

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

    @staticmethod
    def _safe_int(
        value: Any,
    ) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0