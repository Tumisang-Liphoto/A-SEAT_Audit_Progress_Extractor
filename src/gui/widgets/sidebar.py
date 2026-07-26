from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QButtonGroup,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.services.branding_service import BrandingService
from src.utils.version import APP_VERSION


class Sidebar(QWidget):
    """Left navigation sidebar with organisation branding."""

    def __init__(
        self,
        on_page_selected: Callable[[int], None],
        branding_service: BrandingService,
        use_custom_logo: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._on_page_selected = on_page_selected
        self.branding_service = branding_service
        self.use_custom_logo = use_custom_logo

        self._buttons: list[QPushButton] = []

        self.setObjectName("sidebar")
        self.setFixedWidth(300)

        self.setAttribute(
            Qt.WidgetAttribute.WA_StyledBackground,
            True,
        )

        self._build_interface()
        self.refresh_branding(
            use_custom_logo=self.use_custom_logo
        )

    def _build_interface(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            24,
            24,
            24,
            22,
        )
        layout.setSpacing(10)

        self.organisation_logo_label = QLabel()
        self.organisation_logo_label.setObjectName(
            "sidebarOrganisationLogo"
        )
        self.organisation_logo_label.setFixedSize(
            180,
            100,
        )
        self.organisation_logo_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        title = QLabel("A-SEAT")
        title.setObjectName("sidebarTitle")
        title.setAlignment(
            Qt.AlignmentFlag.AlignLeft
        )

        subtitle = QLabel(
            "Audit Progress\nExtractor"
        )
        subtitle.setObjectName(
            "sidebarSubtitle"
        )
        subtitle.setWordWrap(True)

        layout.addWidget(
            self.organisation_logo_label,
            alignment=Qt.AlignmentFlag.AlignHCenter,
        )
        layout.addSpacing(8)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(28)

        self.button_group = QButtonGroup(
            self
        )
        self.button_group.setExclusive(
            True
        )

        navigation_items = [
            ("Dashboard", 0),
            ("Extract Progress", 1),
            ("Settings", 2),
            ("About", 3),
        ]

        for label, page_index in navigation_items:
            button = QPushButton(label)
            button.setObjectName(
                "navigationButton"
            )
            button.setCheckable(True)
            button.setMinimumHeight(54)

            button.clicked.connect(
                lambda checked=False, index=page_index: (
                    self._select_page(index)
                )
            )

            self.button_group.addButton(
                button
            )
            self._buttons.append(
                button
            )
            layout.addWidget(button)

        self._buttons[0].setChecked(
            True
        )

        layout.addStretch()

        attribution_label = QLabel(
            "Powered by"
        )
        attribution_label.setObjectName(
            "sidebarAttribution"
        )
        attribution_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.afroasi_logo_label = QLabel()
        self.afroasi_logo_label.setObjectName(
            "sidebarAfroasiLogo"
        )
        self.afroasi_logo_label.setFixedSize(
            180,
            82,
        )
        self.afroasi_logo_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        version_label = QLabel(
            f"Version {APP_VERSION}"
        )
        version_label.setObjectName(
            "sidebarFooter"
        )
        version_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout.addWidget(
            attribution_label
        )
        layout.addWidget(
            self.afroasi_logo_label,
            alignment=Qt.AlignmentFlag.AlignHCenter,
        )
        layout.addSpacing(4)
        layout.addWidget(
            version_label
        )

        self.setStyleSheet(
            """
            QLabel#sidebarOrganisationLogo,
            QLabel#sidebarAfroasiLogo {
                background-color: transparent;
                border: none;
            }

            QLabel#sidebarAttribution {
                background-color: transparent;
                border: none;
                font-size: 11px;
                font-weight: 600;
            }
            """
        )

    def refresh_branding(
        self,
        use_custom_logo: bool = False,
    ) -> None:
        """Refresh the organisation and AFROSAI-E logos."""

        self.use_custom_logo = (
            use_custom_logo
        )

        active_logo = (
            self.branding_service.get_active_logo_path(
                use_custom_logo=(
                    self.use_custom_logo
                )
            )
        )

        default_logo = (
            self.branding_service.get_default_logo_path()
        )

        self._set_logo(
            label=self.organisation_logo_label,
            image_path=active_logo,
            width=160,
            height=88,
        )

        self._set_logo(
            label=self.afroasi_logo_label,
            image_path=default_logo,
            width=155,
            height=70,
        )

    @staticmethod
    def _set_logo(
        *,
        label: QLabel,
        image_path: Path,
        width: int,
        height: int,
    ) -> None:
        """Load and scale a logo while preserving aspect ratio."""

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

    def _select_page(
        self,
        page_index: int,
    ) -> None:
        self._on_page_selected(
            page_index
        )

    def set_selected_page(
        self,
        page_index: int,
    ) -> None:
        if (
            0
            <= page_index
            < len(self._buttons)
        ):
            self._buttons[
                page_index
            ].setChecked(
                True
            )