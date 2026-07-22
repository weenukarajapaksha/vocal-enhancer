"""Milestone 3: GUI entry point."""

import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from gui.main_window import MainWindow
from gui.theme import STYLESHEET

ICON_PATH = Path(__file__).resolve().parent / "assets" / "icon.ico"


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    if ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(ICON_PATH)))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
