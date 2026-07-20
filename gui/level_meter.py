"""A simple dBFS level meter built on QProgressBar."""

from PySide6.QtWidgets import QProgressBar

METER_FLOOR_DB = -60.0


class LevelMeter(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRange(0, 100)
        self.setTextVisible(False)
        self.setFixedHeight(16)
        self.set_db(METER_FLOOR_DB)

    def set_db(self, db: float):
        pct = max(0.0, min(1.0, (db - METER_FLOOR_DB) / -METER_FLOOR_DB)) * 100
        self.setValue(round(pct))

        if db > -3:
            color = "#e05555"  # near clipping
        elif db > -12:
            color = "#e0c455"
        else:
            color = "#55b06a"
        self.setStyleSheet(
            "QProgressBar { border: 1px solid #3a3c4a; border-radius: 4px; background: #2d2f3a; }"
            f"QProgressBar::chunk {{ background-color: {color}; border-radius: 3px; }}"
        )
