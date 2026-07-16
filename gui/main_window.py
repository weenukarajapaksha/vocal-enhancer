"""Milestone 3: GUI shell -- device selection, start/stop, live level meters.

No effect controls yet; those get added once the Milestone 2 DSP chain exists,
at which point they get their own panel here and get passed to AudioEngine's
`processor` argument.
"""

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from audio.devices import default_devices, device_choices
from audio.engine import AudioEngine
from gui.level_meter import METER_FLOOR_DB, LevelMeter

METER_POLL_MS = 50


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vocal Enhancer")
        self.engine: AudioEngine | None = None

        self.input_combo = QComboBox()
        self.output_combo = QComboBox()
        self._populate_devices()

        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self._on_start_stop)

        self.status_label = QLabel("Stopped")

        self.input_meter = LevelMeter()
        self.output_meter = LevelMeter()

        form = QFormLayout()
        form.addRow("Input device", self.input_combo)
        form.addRow("Output device", self.output_combo)

        meters = QVBoxLayout()
        input_row = QHBoxLayout()
        input_row.addWidget(QLabel("Input"))
        input_row.addWidget(self.input_meter)
        meters.addLayout(input_row)

        output_row = QHBoxLayout()
        output_row.addWidget(QLabel("Output"))
        output_row.addWidget(self.output_meter)
        meters.addLayout(output_row)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(self.start_button)
        layout.addWidget(self.status_label)
        layout.addLayout(meters)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.meter_timer = QTimer(self)
        self.meter_timer.setInterval(METER_POLL_MS)
        self.meter_timer.timeout.connect(self._update_meters)
        self.meter_timer.start()

    def _populate_devices(self):
        default_in, default_out = default_devices()

        for label, index in device_choices("input"):
            self.input_combo.addItem(label, index)
        for label, index in device_choices("output"):
            self.output_combo.addItem(label, index)

        self._select_device(self.input_combo, default_in)
        self._select_device(self.output_combo, default_out)

    @staticmethod
    def _select_device(combo: QComboBox, device_index: int):
        pos = combo.findData(device_index)
        if pos >= 0:
            combo.setCurrentIndex(pos)

    def _on_start_stop(self):
        if self.engine is not None and self.engine.is_running:
            self._stop()
        else:
            self._start()

    def _start(self):
        input_device = self.input_combo.currentData()
        output_device = self.output_combo.currentData()

        self.engine = AudioEngine(input_device=input_device, output_device=output_device)
        try:
            self.engine.start()
        except Exception as e:
            QMessageBox.critical(self, "Failed to start audio", str(e))
            self.engine = None
            return

        in_lat, out_lat = self.engine.latency
        self.status_label.setText(
            f"Running -- {self.engine.samplerate:.0f} Hz, {self.engine.blocksize} frames, "
            f"round-trip latency {(in_lat + out_lat) * 1000:.0f} ms"
        )
        self.start_button.setText("Stop")
        self.input_combo.setEnabled(False)
        self.output_combo.setEnabled(False)

    def _stop(self):
        self.engine.stop()
        self.engine = None
        self.status_label.setText("Stopped")
        self.start_button.setText("Start")
        self.input_combo.setEnabled(True)
        self.output_combo.setEnabled(True)
        self.input_meter.set_db(METER_FLOOR_DB)
        self.output_meter.set_db(METER_FLOOR_DB)

    def _update_meters(self):
        if self.engine is not None and self.engine.is_running:
            self.input_meter.set_db(self.engine.input_level_db)
            self.output_meter.set_db(self.engine.output_level_db)

    def closeEvent(self, event):
        if self.engine is not None and self.engine.is_running:
            self.engine.stop()
        event.accept()
