from typing import Final

from PySide6.QtWidgets import QApplication


THEME_PALETTES: Final[dict[str, dict[str, str]]] = {
    "Light": {
        "window_bg": "#f3f4f6",
        "text": "#111827",
        "secondary_text": "#374151",
        "muted_text": "#4b5563",
        "card_bg": "#ffffff",
        "card_border": "#cbd5e1",
        "input_bg": "#ffffff",
        "input_text": "#111827",
        "input_border": "#94a3b8",
        "button_bg": "#e2e8f0",
        "button_text": "#111827",
        "button_hover": "#cbd5e1",
        "primary": "#2563eb",
        "primary_hover": "#1d4ed8",
        "primary_text": "#ffffff",
        "sidebar_bg": "#172033",
        "sidebar_title": "#ffffff",
        "sidebar_text": "#f8fafc",
        "sidebar_secondary": "#e2e8f0",
        "sidebar_muted": "#cbd5e1",
        "sidebar_hover": "#334155",
        "sidebar_selected": "#2563eb",
        "sidebar_selected_text": "#ffffff",
        "focus": "#2563eb",
        "scrollbar": "#94a3b8",
    },
    "Dark": {
        "window_bg": "#161b22",
        "text": "#f0f6fc",
        "secondary_text": "#c9d1d9",
        "muted_text": "#9ba7b4",
        "card_bg": "#21262d",
        "card_border": "#484f58",
        "input_bg": "#0d1117",
        "input_text": "#e6edf3",
        "input_border": "#484f58",
        "button_bg": "#30363d",
        "button_text": "#e6edf3",
        "button_hover": "#3b424b",
        "primary": "#1f6feb",
        "primary_hover": "#388bfd",
        "primary_text": "#ffffff",
        "sidebar_bg": "#0d1117",
        "sidebar_title": "#ffffff",
        "sidebar_text": "#e6edf3",
        "sidebar_secondary": "#b1bac4",
        "sidebar_muted": "#8b949e",
        "sidebar_hover": "#21262d",
        "sidebar_selected": "#1f6feb",
        "sidebar_selected_text": "#ffffff",
        "focus": "#388bfd",
        "scrollbar": "#484f58",
    },
    "Blue": {
        "window_bg": "#eaf2f8",
        "text": "#102a43",
        "secondary_text": "#243f55",
        "muted_text": "#365f73",
        "card_bg": "#ffffff",
        "card_border": "#8fb5cc",
        "input_bg": "#ffffff",
        "input_text": "#102a43",
        "input_border": "#769fb8",
        "button_bg": "#d6e8f3",
        "button_text": "#102a43",
        "button_hover": "#bfdbea",
        "primary": "#0277a8",
        "primary_hover": "#045f86",
        "primary_text": "#ffffff",
        "sidebar_bg": "#083451",
        "sidebar_title": "#ffffff",
        "sidebar_text": "#ffffff",
        "sidebar_secondary": "#dff3ff",
        "sidebar_muted": "#b8def2",
        "sidebar_hover": "#0b557e",
        "sidebar_selected": "#0284c7",
        "sidebar_selected_text": "#ffffff",
        "focus": "#0277a8",
        "scrollbar": "#769fb8",
    },
    "High Contrast": {
        "window_bg": "#000000",
        "text": "#ffffff",
        "secondary_text": "#ffffff",
        "muted_text": "#ffffff",
        "card_bg": "#000000",
        "card_border": "#ffffff",
        "input_bg": "#000000",
        "input_text": "#ffffff",
        "input_border": "#ffffff",
        "button_bg": "#000000",
        "button_text": "#ffffff",
        "button_hover": "#ffff00",
        "primary": "#ffff00",
        "primary_hover": "#ffffff",
        "primary_text": "#000000",
        "sidebar_bg": "#000000",
        "sidebar_title": "#ffff00",
        "sidebar_text": "#ffffff",
        "sidebar_secondary": "#ffffff",
        "sidebar_muted": "#ffffff",
        "sidebar_hover": "#ffff00",
        "sidebar_selected": "#ffff00",
        "sidebar_selected_text": "#000000",
        "focus": "#ffff00",
        "scrollbar": "#ffff00",
    },
}


def _build_stylesheet(theme: dict[str, str]) -> str:
    """Build a complete Qt stylesheet from a theme colour palette."""

    high_contrast = theme["window_bg"] == "#000000"

    border_width = (
        "2px"
        if high_contrast
        else "1px"
    )

    border_radius = (
        "4px"
        if high_contrast
        else "7px"
    )

    navigation_hover_text = (
        "#000000"
        if high_contrast
        else "#ffffff"
    )

    button_hover_text = (
        "#000000"
        if high_contrast
        else theme["button_text"]
    )

    primary_hover_text = (
        "#000000"
        if high_contrast
        else theme["primary_text"]
    )

    return f"""
/* =========================================================
   APPLICATION
   ========================================================= */

QMainWindow,
QWidget#mainContainer,
QWidget#contentPage,
QStackedWidget {{
    background-color: {theme["window_bg"]};
    color: {theme["text"]};
    font-family: "Segoe UI";
    font-size: 14px;
}}

QWidget#contentPage {{
    background-color: {theme["window_bg"]};
}}


/* =========================================================
   GENERAL TEXT
   ========================================================= */

QLabel {{
    background-color: transparent;
    color: {theme["text"]};
    border: none;
}}

QLabel#pageHeading {{
    color: {theme["text"]};
    font-size: 26px;
    font-weight: 700;
}}

QLabel#pageDescription {{
    color: {theme["secondary_text"]};
    font-size: 14px;
}}

QLabel#cardTitle {{
    color: {theme["secondary_text"]};
    font-size: 13px;
    font-weight: 600;
}}

QLabel#cardValue {{
    color: {theme["text"]};
    font-size: 22px;
    font-weight: 700;
}}

QLabel#cardDescription,
QLabel#statusLabel {{
    color: {theme["muted_text"]};
    font-size: 13px;
}}


/* =========================================================
   SIDEBAR
   ========================================================= */

QWidget#sidebar {{
    background-color: {theme["sidebar_bg"]};
    color: {theme["sidebar_text"]};
    border: none;
}}

QWidget#sidebar QLabel {{
    background-color: transparent;
    border: none;
}}

QLabel#sidebarTitle {{
    color: {theme["sidebar_title"]};
    font-size: 28px;
    font-weight: 700;
}}

QLabel#sidebarSubtitle {{
    color: {theme["sidebar_secondary"]};
    font-size: 15px;
}}

QLabel#sidebarFooter {{
    color: {theme["sidebar_muted"]};
    font-size: 12px;
}}

QPushButton#navigationButton {{
    background-color: transparent;
    color: {theme["sidebar_text"]};
    border: none;
    border-radius: {border_radius};
    padding: 10px 14px;
    text-align: left;
    font-weight: 600;
}}

QPushButton#navigationButton:hover {{
    background-color: {theme["sidebar_hover"]};
    color: {navigation_hover_text};
}}

QPushButton#navigationButton:checked {{
    background-color: {theme["sidebar_selected"]};
    color: {theme["sidebar_selected_text"]};
}}


/* =========================================================
   CARDS
   ========================================================= */

QFrame#summaryCard,
QFrame#formCard {{
    background-color: {theme["card_bg"]};
    color: {theme["text"]};
    border: {border_width} solid {theme["card_border"]};
    border-radius: {border_radius};
}}

QFrame#summaryCard QLabel,
QFrame#formCard QLabel {{
    background-color: transparent;
}}


/* =========================================================
   TEXT INPUTS
   ========================================================= */

QLineEdit {{
    background-color: {theme["input_bg"]};
    color: {theme["input_text"]};
    border: {border_width} solid {theme["input_border"]};
    border-radius: {border_radius};
    min-height: 36px;
    padding: 0 10px;
    selection-background-color: {theme["primary"]};
    selection-color: {theme["primary_text"]};
}}

QLineEdit:focus {{
    border: {border_width} solid {theme["focus"]};
}}

QLineEdit:disabled {{
    color: {theme["muted_text"]};
}}

QLineEdit::placeholder {{
    color: {theme["muted_text"]};
}}


/* =========================================================
   COMBO BOXES

   The drop-down and arrow subcontrols are intentionally not
   customised. Qt's Fusion style therefore draws the native
   arrow correctly on every theme.
   ========================================================= */

QComboBox {{
    background-color: {theme["input_bg"]};
    color: {theme["input_text"]};
    border: {border_width} solid {theme["input_border"]};
    border-radius: {border_radius};
    min-height: 36px;
    padding-left: 10px;
    padding-right: 10px;
    selection-background-color: {theme["primary"]};
    selection-color: {theme["primary_text"]};
}}

QComboBox:hover {{
    border: {border_width} solid {theme["focus"]};
}}

QComboBox:focus {{
    border: {border_width} solid {theme["focus"]};
}}

QComboBox:disabled {{
    color: {theme["muted_text"]};
}}

QComboBox QAbstractItemView {{
    background-color: {theme["input_bg"]};
    color: {theme["input_text"]};
    border: {border_width} solid {theme["input_border"]};
    selection-background-color: {theme["primary"]};
    selection-color: {theme["primary_text"]};
    outline: none;
    padding: 4px;
}}


/* =========================================================
   BUTTONS
   ========================================================= */

QPushButton {{
    background-color: {theme["button_bg"]};
    color: {theme["button_text"]};
    border: {border_width} solid {theme["input_border"]};
    border-radius: {border_radius};
    padding: 8px 14px;
}}

QPushButton:hover {{
    background-color: {theme["button_hover"]};
    color: {button_hover_text};
}}

QPushButton:pressed {{
    padding-top: 9px;
    padding-bottom: 7px;
}}

QPushButton:disabled {{
    color: {theme["muted_text"]};
}}

QPushButton#primaryButton {{
    background-color: {theme["primary"]};
    color: {theme["primary_text"]};
    border: {border_width} solid {theme["primary"]};
    font-weight: 700;
}}

QPushButton#primaryButton:hover {{
    background-color: {theme["primary_hover"]};
    color: {primary_hover_text};
    border-color: {theme["primary_hover"]};
}}


/* =========================================================
   CHECK BOXES
   ========================================================= */

QCheckBox {{
    background-color: transparent;
    color: {theme["text"]};
    spacing: 8px;
}}

QCheckBox:disabled {{
    color: {theme["muted_text"]};
}}

QCheckBox::indicator {{
    width: 17px;
    height: 17px;
}}

QCheckBox::indicator:unchecked {{
    background-color: {theme["input_bg"]};
    border: {border_width} solid {theme["input_border"]};
    border-radius: 3px;
}}

QCheckBox::indicator:checked {{
    background-color: {theme["primary"]};
    border: {border_width} solid {theme["primary"]};
    border-radius: 3px;
}}


/* =========================================================
   TOOL TIPS
   ========================================================= */

QToolTip {{
    background-color: {theme["card_bg"]};
    color: {theme["text"]};
    border: {border_width} solid {theme["card_border"]};
    padding: 5px;
}}


/* =========================================================
   SCROLL BARS
   ========================================================= */

QScrollBar:vertical {{
    background-color: transparent;
    width: 10px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {theme["scrollbar"]};
    border-radius: 5px;
    min-height: 30px;
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    background-color: transparent;
}}

QScrollBar:horizontal {{
    background-color: transparent;
    height: 10px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background-color: {theme["scrollbar"]};
    border-radius: 5px;
    min-width: 30px;
}}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0;
}}

QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {{
    background-color: transparent;
}}
"""


THEMES: Final[dict[str, str]] = {
    theme_name: _build_stylesheet(palette)
    for theme_name, palette in THEME_PALETTES.items()
}


def apply_theme(
    application: QApplication,
    theme_name: str,
) -> None:
    """Apply the selected theme to the entire application."""

    selected_theme_name = (
        theme_name
        if theme_name in THEMES
        else "Light"
    )

    application.setStyle("Fusion")
    application.setStyleSheet("")
    application.setStyleSheet(
        THEMES[selected_theme_name]
    )