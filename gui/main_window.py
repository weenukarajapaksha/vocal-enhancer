"""Milestone 3: GUI dashboard -- device selection, start/stop, live level
meters, and effect controls for the Milestone 2 DSP chain.
"""

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from audio.devices import best_default_devices, device_choices
from audio.engine import AudioEngine
from dsp import default_chain
from dsp.presets import delete_preset, list_presets, load_preset, save_preset
from gui.effects_panel import (
    build_compressor_panel,
    build_delay_panel,
    build_eq_panel,
    build_gate_panel,
    build_harmony_panel,
    build_pitch_panel,
    build_reverb_panel,
    build_robot_panel,
)
from gui.level_meter import METER_FLOOR_DB, LevelMeter

METER_POLL_MS = 50
SAMPLERATE = 48000


def _card(*widgets_or_layouts) -> QFrame:
    frame = QFrame()
    frame.setObjectName("Card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(16, 14, 16, 14)
    layout.setSpacing(10)
    for item in widgets_or_layouts:
        if isinstance(item, QWidget):
            layout.addWidget(item)
        else:
            layout.addLayout(item)
    return frame


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vocal Enhancer")
        self.engine: AudioEngine | None = None
        self.chain = default_chain(samplerate=SAMPLERATE)

        header = QLabel("Vocal Enhancer")
        header.setObjectName("HeaderTitle")
        subheader = QLabel("Real-time voice processing")
        subheader.setObjectName("HeaderSubtitle")

        self.input_combo = QComboBox()
        self.output_combo = QComboBox()
        self._populate_devices()

        self.start_button = QPushButton("Start")
        self.start_button.setObjectName("StartButton")
        self.start_button.setProperty("running", False)
        self.start_button.setMinimumHeight(36)
        self.start_button.clicked.connect(self._on_start_stop)

        self.status_label = QLabel("Stopped")
        self.status_label.setObjectName("StatusLabel")

        form = QFormLayout()
        form.setSpacing(8)
        form.addRow("Input", self.input_combo)
        form.addRow("Output", self.output_combo)

        control_card = _card(form, self.start_button, self.status_label)

        self.preset_combo = QComboBox()
        self._refresh_preset_list()
        self.load_preset_button = QPushButton("Load")
        self.load_preset_button.clicked.connect(self._on_load_preset)
        self.delete_preset_button = QPushButton("Delete")
        self.delete_preset_button.clicked.connect(self._on_delete_preset)

        preset_load_row = QHBoxLayout()
        preset_load_row.addWidget(self.preset_combo, 1)
        preset_load_row.addWidget(self.load_preset_button)
        preset_load_row.addWidget(self.delete_preset_button)

        self.preset_name_edit = QLineEdit()
        self.preset_name_edit.setPlaceholderText("New preset name")
        self.save_preset_button = QPushButton("Save")
        self.save_preset_button.clicked.connect(self._on_save_preset)

        preset_save_row = QHBoxLayout()
        preset_save_row.addWidget(self.preset_name_edit, 1)
        preset_save_row.addWidget(self.save_preset_button)

        presets_card = _card(preset_load_row, preset_save_row)

        self.input_meter = LevelMeter()
        self.output_meter = LevelMeter()

        meters = QVBoxLayout()
        meters.setSpacing(6)
        input_row = QHBoxLayout()
        input_label = QLabel("Input")
        input_label.setFixedWidth(50)
        input_row.addWidget(input_label)
        input_row.addWidget(self.input_meter)
        meters.addLayout(input_row)

        output_row = QHBoxLayout()
        output_label = QLabel("Output")
        output_label.setFixedWidth(50)
        output_row.addWidget(output_label)
        output_row.addWidget(self.output_meter)
        meters.addLayout(output_row)

        meters_card = _card(meters)

        self.tabs = self._build_effect_tabs()

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.addWidget(header)
        layout.addWidget(subheader)
        layout.addWidget(control_card)
        layout.addWidget(presets_card)
        layout.addWidget(meters_card)
        layout.addWidget(self.tabs)
        self.main_layout = layout

        container = QWidget()
        container.setLayout(layout)

        scroll = QScrollArea()
        scroll.setWidget(container)
        scroll.setWidgetResizable(True)
        self.setCentralWidget(scroll)
        self.resize(440, 720)

        self.meter_timer = QTimer(self)
        self.meter_timer.setInterval(METER_POLL_MS)
        self.meter_timer.timeout.connect(self._update_meters)
        self.meter_timer.start()

    def _build_effect_tabs(self) -> QTabWidget:
        vocal_chain_tab = QWidget()
        vocal_chain_layout = QVBoxLayout(vocal_chain_tab)
        vocal_chain_layout.addWidget(build_gate_panel(self.chain.get("gate")))
        vocal_chain_layout.addWidget(build_pitch_panel(self.chain.get("pitch")))
        vocal_chain_layout.addWidget(build_harmony_panel(self.chain.get("harmony")))
        vocal_chain_layout.addWidget(build_compressor_panel(self.chain.get("compressor")))
        vocal_chain_layout.addWidget(build_eq_panel(self.chain.get("eq")))
        vocal_chain_layout.addStretch(1)

        voice_fx_tab = QWidget()
        voice_fx_layout = QVBoxLayout(voice_fx_tab)
        voice_fx_layout.addWidget(build_robot_panel(self.chain.get("robot")))
        voice_fx_layout.addWidget(build_delay_panel(self.chain.get("delay")))
        voice_fx_layout.addWidget(build_reverb_panel(self.chain.get("reverb")))
        voice_fx_layout.addStretch(1)

        tabs = QTabWidget()
        tabs.addTab(vocal_chain_tab, "Vocal Chain")
        tabs.addTab(voice_fx_tab, "Voice FX")
        return tabs

    def _rebuild_effect_tabs(self):
        """Recreate the effect panels so their sliders reflect a freshly loaded preset."""
        index = self.main_layout.indexOf(self.tabs)
        old_tabs = self.tabs
        self.tabs = self._build_effect_tabs()
        self.main_layout.removeWidget(old_tabs)
        self.main_layout.insertWidget(index, self.tabs)
        old_tabs.deleteLater()

    def _refresh_preset_list(self):
        self.preset_combo.clear()
        self.preset_combo.addItems(list_presets())

    def _on_save_preset(self):
        name = self.preset_name_edit.text()
        try:
            saved_name = save_preset(self.chain, name)
        except ValueError as e:
            QMessageBox.warning(self, "Invalid preset name", str(e))
            return
        self.preset_name_edit.clear()
        self._refresh_preset_list()
        pos = self.preset_combo.findText(saved_name)
        if pos >= 0:
            self.preset_combo.setCurrentIndex(pos)

    def _on_load_preset(self):
        name = self.preset_combo.currentText()
        if not name:
            return
        load_preset(self.chain, name)
        self._rebuild_effect_tabs()

    def _on_delete_preset(self):
        name = self.preset_combo.currentText()
        if not name:
            return
        confirm = QMessageBox.question(self, "Delete preset", f"Delete preset '{name}'?")
        if confirm != QMessageBox.StandardButton.Yes:
            return
        delete_preset(name)
        self._refresh_preset_list()

    def _populate_devices(self):
        default_in, default_out = best_default_devices()

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

    def _restyle_start_button(self, running: bool):
        self.start_button.setProperty("running", running)
        self.start_button.style().unpolish(self.start_button)
        self.start_button.style().polish(self.start_button)

    def _start(self):
        input_device = self.input_combo.currentData()
        output_device = self.output_combo.currentData()

        self.engine = AudioEngine(
            samplerate=SAMPLERATE,
            input_device=input_device,
            output_device=output_device,
            processor=self.chain,
        )
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
        self._restyle_start_button(True)
        self.input_combo.setEnabled(False)
        self.output_combo.setEnabled(False)

    def _stop(self):
        self.engine.stop()
        self.engine = None
        self.status_label.setText("Stopped")
        self.start_button.setText("Start")
        self._restyle_start_button(False)
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
