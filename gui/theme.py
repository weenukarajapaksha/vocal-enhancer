"""Dark theme stylesheet for the dashboard."""

ACCENT = "#7c5cff"
ACCENT_HOVER = "#9277ff"
BG = "#1b1c22"
PANEL = "#25262f"
PANEL_ALT = "#2d2f3a"
BORDER = "#3a3c4a"
TEXT = "#e8e8ec"
TEXT_DIM = "#9a9ba8"

STYLESHEET = f"""
QWidget {{
    background-color: {BG};
    color: {TEXT};
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
}}

QScrollArea, QTabWidget::pane {{
    border: none;
    background-color: {BG};
}}

QLabel#HeaderTitle {{
    font-size: 20px;
    font-weight: 600;
    color: {TEXT};
}}

QLabel#HeaderSubtitle {{
    color: {TEXT_DIM};
    font-size: 12px;
}}

QLabel#StatusLabel {{
    color: {TEXT_DIM};
    font-size: 12px;
    padding: 2px 0px;
}}

QFrame#Card {{
    background-color: {PANEL};
    border: 1px solid {BORDER};
    border-radius: 10px;
}}

QGroupBox {{
    background-color: {PANEL};
    border: 1px solid {BORDER};
    border-radius: 10px;
    margin-top: 14px;
    padding: 12px 10px 10px 10px;
    font-weight: 600;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    top: 2px;
    padding: 0px 4px;
    color: {TEXT};
}}

QGroupBox::indicator {{
    width: 15px;
    height: 15px;
    border-radius: 4px;
    border: 1px solid {BORDER};
    background-color: {PANEL_ALT};
}}

QGroupBox::indicator:checked {{
    background-color: {ACCENT};
    border: 1px solid {ACCENT};
}}

QPushButton {{
    background-color: {PANEL_ALT};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
}}

QPushButton:hover {{
    border: 1px solid {ACCENT};
}}

QPushButton#StartButton {{
    background-color: {ACCENT};
    border: none;
    color: white;
}}

QPushButton#StartButton:hover {{
    background-color: {ACCENT_HOVER};
}}

QPushButton#StartButton[running="true"] {{
    background-color: #e05555;
}}

QPushButton#StartButton[running="true"]:hover {{
    background-color: #eb6f6f;
}}

QComboBox {{
    background-color: {PANEL_ALT};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 5px 8px;
}}

QComboBox:hover {{
    border: 1px solid {ACCENT};
}}

QComboBox QAbstractItemView {{
    background-color: {PANEL_ALT};
    border: 1px solid {BORDER};
    selection-background-color: {ACCENT};
    outline: none;
}}

QSlider::groove:horizontal {{
    height: 4px;
    background: {BORDER};
    border-radius: 2px;
}}

QSlider::sub-page:horizontal {{
    background: {ACCENT};
    border-radius: 2px;
}}

QSlider::handle:horizontal {{
    background: {TEXT};
    width: 14px;
    height: 14px;
    margin: -6px 0;
    border-radius: 7px;
}}

QSlider::handle:horizontal:hover {{
    background: {ACCENT};
}}

QProgressBar {{
    border: 1px solid {BORDER};
    border-radius: 4px;
    background: {PANEL_ALT};
}}

QTabWidget::pane {{
    border-top: 1px solid {BORDER};
    margin-top: -1px;
}}

QTabBar::tab {{
    background: transparent;
    color: {TEXT_DIM};
    padding: 8px 18px;
    border-bottom: 2px solid transparent;
    font-weight: 600;
}}

QTabBar::tab:selected {{
    color: {TEXT};
    border-bottom: 2px solid {ACCENT};
}}

QTabBar::tab:hover {{
    color: {TEXT};
}}

QScrollBar:vertical {{
    background: {BG};
    width: 10px;
}}

QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 5px;
    min-height: 24px;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
"""
