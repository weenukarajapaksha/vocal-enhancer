"""Load & Process tab: load an audio file, run it through the same effect
settings configured in the Real-Time tab, and play back the processed result.
"""

import os
import threading

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from audio.devices import best_default_devices, device_choices
from audio.file_io import SUPPORTED_EXTENSIONS, load_audio_file
from audio.file_player import FilePlayer
from dsp import default_chain
from dsp.presets import apply_dict_to_chain, chain_to_dict
from gui.level_meter import METER_FLOOR_DB, LevelMeter

POLL_MS = 100


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


class FileProcessingTab(QWidget):
    def __init__(self, live_chain, parent=None):
        super().__init__(parent)
        self.live_chain = live_chain  # read-only here: current effect settings are copied, not mutated
        self.player: FilePlayer | None = None
        self._file_data = None
        self._file_samplerate = None
        self._process_result = {}

        self.file_label = QLabel("No file loaded")
        self.choose_button = QPushButton("Choose File...")
        self.choose_button.clicked.connect(self._on_choose_file)

        file_row = QHBoxLayout()
        file_row.addWidget(self.file_label, 1)
        file_row.addWidget(self.choose_button)

        self.output_combo = QComboBox()
        for label, index in device_choices("output"):
            self.output_combo.addItem(label, index)
        _, default_out = best_default_devices()
        pos = self.output_combo.findData(default_out)
        if pos >= 0:
            self.output_combo.setCurrentIndex(pos)

        form = QFormLayout()
        form.addRow("Output", self.output_combo)

        self.play_button = QPushButton("Process && Play")
        self.play_button.setObjectName("StartButton")
        self.play_button.setMinimumHeight(36)
        self.play_button.setEnabled(False)
        self.play_button.clicked.connect(self._on_play)

        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self._on_stop)

        button_row = QHBoxLayout()
        button_row.addWidget(self.play_button, 1)
        button_row.addWidget(self.stop_button)

        self.status_label = QLabel("Idle")
        self.status_label.setObjectName("StatusLabel")

        control_card = _card(file_row, form, button_row, self.status_label)

        self.level_meter = LevelMeter()
        meter_row = QHBoxLayout()
        meter_label = QLabel("Output")
        meter_label.setFixedWidth(50)
        meter_row.addWidget(meter_label)
        meter_row.addWidget(self.level_meter)
        meter_card = _card(meter_row)

        note = QLabel(
            "Uses the same effect settings configured in the Real-Time tab. "
            "Supported formats: WAV, FLAC, OGG, AIFF."
        )
        note.setObjectName("HeaderSubtitle")
        note.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.addWidget(note)
        layout.addWidget(control_card)
        layout.addWidget(meter_card)
        layout.addStretch(1)

        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(POLL_MS)
        self.poll_timer.timeout.connect(self._poll)
        self.poll_timer.start()

    def _on_choose_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose audio file", "", SUPPORTED_EXTENSIONS)
        if not path:
            return
        try:
            data, samplerate = load_audio_file(path)
        except Exception as e:
            QMessageBox.critical(self, "Failed to load file", str(e))
            return

        self._file_data = data
        self._file_samplerate = samplerate
        duration = len(data) / samplerate
        self.file_label.setText(f"{os.path.basename(path)} ({duration:.1f}s)")
        self.play_button.setEnabled(True)
        self.status_label.setText("Loaded")

    def _on_play(self):
        if self._file_data is None:
            return
        if self.player is not None and self.player.is_playing:
            self.player.stop()

        self.status_label.setText("Processing...")
        self.play_button.setEnabled(False)
        self.choose_button.setEnabled(False)

        file_chain = default_chain(samplerate=self._file_samplerate, channels=self._file_data.shape[1])
        apply_dict_to_chain(file_chain, chain_to_dict(self.live_chain))

        self._process_result = {}
        data = self._file_data

        def worker():
            self._process_result["data"] = file_chain(data)

        threading.Thread(target=worker, daemon=True).start()

    def _poll(self):
        if "data" in self._process_result:
            processed = self._process_result.pop("data")
            self.player = FilePlayer(
                samplerate=self._file_samplerate,
                channels=processed.shape[1],
                output_device=self.output_combo.currentData(),
            )
            self.player.load(processed)
            self.player.start()
            self.play_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            self.choose_button.setEnabled(True)

        if self.player is not None and self.player.is_playing:
            self.level_meter.set_db(self.player.output_level_db)
            elapsed, total = self.player.progress_seconds
            self.status_label.setText(f"Playing -- {elapsed:.1f}s / {total:.1f}s")
        elif self.player is not None:
            self.level_meter.set_db(METER_FLOOR_DB)
            if self.status_label.text().startswith("Playing"):
                self.status_label.setText("Finished")
            self.stop_button.setEnabled(False)

    def _on_stop(self):
        if self.player is not None:
            self.player.stop()
        self.status_label.setText("Stopped")
        self.stop_button.setEnabled(False)
        self.level_meter.set_db(METER_FLOOR_DB)

    def shutdown(self):
        if self.player is not None and self.player.is_playing:
            self.player.stop()
