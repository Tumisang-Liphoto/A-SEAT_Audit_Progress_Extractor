from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class Sidebar(QWidget):
    """Left navigation sidebar."""

    def __init__(
        self,
        on_page_selected: Callable[[int], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._on_page_selected = on_page_selected
        self._buttons: list[QPushButton] = []

        self.setObjectName("sidebar")
        self.setFixedWidth(300)

        # Ensures Qt paints the stylesheet background on this custom widget.
        self.setAttribute(
            Qt.WidgetAttribute.WA_StyledBackground,
            True,
        )

        self._build_interface()

    def _build_interface(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 34, 26, 28)
        layout.setSpacing(10)

        title = QLabel("A-SEAT")
        title.setObjectName("sidebarTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)

        subtitle = QLabel("Audit Progress\nExtractor")
        subtitle.setObjectName("sidebarSubtitle")
        subtitle.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(48)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        navigation_items = [
            ("Dashboard", 0),
            ("Extract Progress", 1),
            ("Settings", 2),
        ]

        for label, page_index in navigation_items:
            button = QPushButton(label)
            button.setObjectName("navigationButton")
            button.setCheckable(True)
            button.setMinimumHeight(54)

            button.clicked.connect(
                lambda checked=False, index=page_index: (
                    self._select_page(index)
                )
            )

            self.button_group.addButton(button)
            self._buttons.append(button)
            layout.addWidget(button)

        self._buttons[0].setChecked(True)

        layout.addStretch()

        footer = QLabel("Office Audit Utility")
        footer.setObjectName("sidebarFooter")

        layout.addWidget(footer)

    def _select_page(self, page_index: int) -> None:
        self._on_page_selected(page_index)

    def set_selected_page(self, page_index: int) -> None:
        if 0 <= page_index < len(self._buttons):
            self._buttons[page_index].setChecked(True)