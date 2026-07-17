"""A labeled slider bound to a float range, for DSP effect parameters."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSlider, QWidget


class ParamSlider(QWidget):
    valueChanged = Signal(float)

    def __init__(self, label: str, min_value: float, max_value: float, initial: float, step: float = 0.1, suffix: str = "", parent=None):
        super().__init__(parent)
        self._min = min_value
        self._step = step
        self._suffix = suffix

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, round((max_value - min_value) / step))
        self.slider.setValue(round((initial - min_value) / step))
        self.slider.valueChanged.connect(self._on_slider_changed)

        self.value_label = QLabel(self._format(initial))
        self.value_label.setFixedWidth(60)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel(label), 2)
        layout.addWidget(self.slider, 3)
        layout.addWidget(self.value_label, 1)

    def _format(self, value: float) -> str:
        return f"{value:.1f}{self._suffix}"

    def _on_slider_changed(self, raw: int):
        value = self._min + raw * self._step
        self.value_label.setText(self._format(value))
        self.valueChanged.emit(value)

    def value(self) -> float:
        return self._min + self.slider.value() * self._step
