from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.services.branding_service import BrandingService
from src.utils.version import APP_NAME, APP_VERSION


class AboutPage(QWidget):
    """Application information, branding and acknowledgements."""

    def __init__(
        self,
        branding_service: BrandingService,
        organisation_name: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setObjectName("contentPage")

        self.branding_service = branding_service
        self.organisation_name = (
            organisation_name.strip()
            or "Organisation"
        )

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
        content_widget.setObjectName(
            "contentPage"
        )

        page_layout = QVBoxLayout(
            content_widget
        )
        page_layout.setContentsMargins(
            32,
            28,
            32,
            28,
        )
        page_layout.setSpacing(20)

        heading = QLabel("About")
        heading.setObjectName(
            "pageHeading"
        )

        description = QLabel(
            "Application information, organisation branding "
            "and AFROSAI-E acknowledgement."
        )
        description.setObjectName(
            "pageDescription"
        )
        description.setWordWrap(True)

        page_layout.addWidget(heading)
        page_layout.addWidget(description)

        hero_card = QFrame()
        hero_card.setObjectName(
            "aboutHeroCard"
        )

        hero_layout = QHBoxLayout(
            hero_card
        )
        hero_layout.setContentsMargins(
            26,
            24,
            26,
            24,
        )
        hero_layout.setSpacing(24)

        self.organisation_logo_label = QLabel()
        self.organisation_logo_label.setObjectName(
            "organisationLogo"
        )
        self.organisation_logo_label.setFixedSize(
            180,
            120,
        )
        self.organisation_logo_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.organisation_logo_label.setScaledContents(
            False
        )

        hero_text_layout = QVBoxLayout()
        hero_text_layout.setSpacing(8)

        app_name_label = QLabel(
            APP_NAME
        )
        app_name_label.setObjectName(
            "aboutAppName"
        )
        app_name_label.setWordWrap(True)

        version_label = QLabel(
            f"Version {APP_VERSION}"
        )
        version_label.setObjectName(
            "aboutVersion"
        )

        purpose_label = QLabel(
            (
                "A desktop application for extracting, exporting "
                "and comparing audit progress information from "
                "the AFROSAI-E A-SEAT audit management system."
            )
        )
        purpose_label.setObjectName(
            "aboutBodyText"
        )
        purpose_label.setWordWrap(True)

        self.organisation_label = QLabel(
            f"Configured for: {self.organisation_name}"
        )
        self.organisation_label.setObjectName(
            "aboutOrganisation"
        )
        self.organisation_label.setWordWrap(True)

        hero_text_layout.addWidget(
            app_name_label
        )
        hero_text_layout.addWidget(
            version_label
        )
        hero_text_layout.addSpacing(4)
        hero_text_layout.addWidget(
            purpose_label
        )
        hero_text_layout.addSpacing(6)
        hero_text_layout.addWidget(
            self.organisation_label
        )
        hero_text_layout.addStretch()

        hero_layout.addWidget(
            self.organisation_logo_label
        )
        hero_layout.addLayout(
            hero_text_layout,
            1,
        )

        page_layout.addWidget(
            hero_card
        )

        information_grid = QGridLayout()
        information_grid.setHorizontalSpacing(
            18
        )
        information_grid.setVerticalSpacing(
            18
        )
        information_grid.setColumnStretch(
            0,
            1,
        )
        information_grid.setColumnStretch(
            1,
            1,
        )

        purpose_card = self._create_information_card(
            "Purpose",
            (
                "The application supports audit teams by extracting "
                "audit progress information, producing structured "
                "Excel and CSV outputs, and comparing recent "
                "extractions to identify movement, regression, "
                "new audits and missing audits."
            ),
        )

        privacy_card = self._create_information_card(
            "Local Data Handling",
            (
                "Application settings, extraction snapshots and "
                "branding files are stored locally on the user's "
                "computer. Passwords are not saved by the application."
            ),
        )

        update_card = self._create_information_card(
            "Updates",
            (
                "The application can check GitHub for published "
                "releases and install approved updates using the "
                "built-in updater."
            ),
        )

        support_card = self._create_information_card(
            "Support",
            (
                "Support and organisation-specific contact details "
                "will be added once they have been confirmed."
            ),
        )

        information_grid.addWidget(
            purpose_card,
            0,
            0,
        )
        information_grid.addWidget(
            privacy_card,
            0,
            1,
        )
        information_grid.addWidget(
            update_card,
            1,
            0,
        )
        information_grid.addWidget(
            support_card,
            1,
            1,
        )

        page_layout.addLayout(
            information_grid
        )

        acknowledgement_card = QFrame()
        acknowledgement_card.setObjectName(
            "acknowledgementCard"
        )

        acknowledgement_layout = QHBoxLayout(
            acknowledgement_card
        )
        acknowledgement_layout.setContentsMargins(
            24,
            22,
            24,
            22,
        )
        acknowledgement_layout.setSpacing(22)

        self.afroasi_logo_label = QLabel()
        self.afroasi_logo_label.setObjectName(
            "afroasiLogo"
        )
        self.afroasi_logo_label.setFixedSize(
            210,
            120,
        )
        self.afroasi_logo_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        acknowledgement_text_layout = QVBoxLayout()
        acknowledgement_text_layout.setSpacing(
            8
        )

        acknowledgement_heading = QLabel(
            "AFROSAI-E Acknowledgement"
        )
        acknowledgement_heading.setObjectName(
            "aboutSectionHeading"
        )

        acknowledgement_text = QLabel(
            (
                "This application is designed for use with the "
                "AFROSAI-E A-SEAT audit management system. "
                "The AFROSAI-E logo remains displayed as a permanent "
                "acknowledgement even when an organisation uploads "
                "its own branding."
            )
        )
        acknowledgement_text.setObjectName(
            "aboutBodyText"
        )
        acknowledgement_text.setWordWrap(
            True
        )

        acknowledgement_text_layout.addWidget(
            acknowledgement_heading
        )
        acknowledgement_text_layout.addWidget(
            acknowledgement_text
        )
        acknowledgement_text_layout.addStretch()

        acknowledgement_layout.addWidget(
            self.afroasi_logo_label
        )
        acknowledgement_layout.addLayout(
            acknowledgement_text_layout,
            1,
        )

        page_layout.addWidget(
            acknowledgement_card
        )

        footer_label = QLabel(
            (
                f"{APP_NAME} • Version {APP_VERSION}"
            )
        )
        footer_label.setObjectName(
            "aboutFooter"
        )
        footer_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        page_layout.addWidget(
            footer_label
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
            QFrame#aboutHeroCard,
            QFrame#aboutInfoCard,
            QFrame#acknowledgementCard {
                background-color: palette(base);
                border: 1px solid palette(mid);
                border-radius: 12px;
            }

            QLabel#organisationLogo,
            QLabel#afroasiLogo {
                background-color: palette(alternate-base);
                border: 1px solid palette(mid);
                border-radius: 12px;
            }

            QLabel#aboutAppName {
                background-color: transparent;
                border: none;
                font-size: 22px;
                font-weight: 700;
                color: palette(text);
            }

            QLabel#aboutVersion,
            QLabel#aboutOrganisation,
            QLabel#aboutFooter {
                background-color: transparent;
                border: none;
                font-size: 13px;
                color: palette(text);
            }

            QLabel#aboutOrganisation {
                font-weight: 600;
            }

            QLabel#aboutSectionHeading {
                background-color: transparent;
                border: none;
                font-size: 15px;
                font-weight: 700;
                color: palette(text);
            }

            QLabel#aboutBodyText {
                background-color: transparent;
                border: none;
                font-size: 13px;
                color: palette(text);
            }
            """
        )

        self.refresh_branding()

    def _create_information_card(
        self,
        heading: str,
        body: str,
    ) -> QFrame:
        """Create a compact information card."""

        card = QFrame()
        card.setObjectName(
            "aboutInfoCard"
        )
        card.setMinimumHeight(
            155
        )
        card.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        layout = QVBoxLayout(
            card
        )
        layout.setContentsMargins(
            20,
            18,
            20,
            18,
        )
        layout.setSpacing(
            9
        )

        heading_label = QLabel(
            heading
        )
        heading_label.setObjectName(
            "aboutSectionHeading"
        )

        body_label = QLabel(
            body
        )
        body_label.setObjectName(
            "aboutBodyText"
        )
        body_label.setWordWrap(
            True
        )

        layout.addWidget(
            heading_label
        )
        layout.addWidget(
            body_label
        )
        layout.addStretch()

        return card

    def refresh_branding(
        self,
        use_custom_logo: bool = False,
        organisation_name: str | None = None,
    ) -> None:
        """Refresh organisation and AFROSAI-E logos."""

        if organisation_name is not None:
            self.organisation_name = (
                organisation_name.strip()
                or "Organisation"
            )

        self.organisation_label.setText(
            f"Configured for: {self.organisation_name}"
        )

        organisation_logo = (
            self.branding_service.get_active_logo_path(
                use_custom_logo=use_custom_logo
            )
        )

        default_logo = (
            self.branding_service.get_default_logo_path()
        )

        self._set_logo(
            self.organisation_logo_label,
            organisation_logo,
            160,
            100,
        )

        self._set_logo(
            self.afroasi_logo_label,
            default_logo,
            190,
            100,
        )

    @staticmethod
    def _set_logo(
        label: QLabel,
        image_path: Path,
        width: int,
        height: int,
    ) -> None:
        """Load and scale one logo while preserving aspect ratio."""

        pixmap = QPixmap(
            str(image_path)
        )

        if pixmap.isNull():
            label.setText(
                "Logo unavailable"
            )
            return

        scaled_pixmap = pixmap.scaled(
            width,
            height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        label.setText("")
        label.setPixmap(
            scaled_pixmap
        )