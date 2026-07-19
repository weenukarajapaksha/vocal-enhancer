"""GUI panels exposing the Milestone 2 DSP chain's parameters and on/off toggles."""

from PySide6.QtWidgets import QComboBox, QGroupBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from dsp.pitch import NOTE_NAMES, SCALES
from gui.param_slider import ParamSlider


def _group(title, enabled, on_toggle, sliders):
    box = QGroupBox(title)
    box.setCheckable(True)
    box.setChecked(enabled)
    box.toggled.connect(on_toggle)

    layout = QVBoxLayout()
    for slider in sliders:
        layout.addWidget(slider)
    box.setLayout(layout)
    return box


def build_gate_panel(gate):
    threshold = ParamSlider("Threshold", -80, 0, gate.threshold_db, step=1, suffix=" dB")
    threshold.valueChanged.connect(lambda v: setattr(gate, "threshold_db", v))

    return _group("Noise Gate", gate.enabled, lambda on: setattr(gate, "enabled", on), [threshold])


def build_compressor_panel(comp):
    threshold = ParamSlider("Threshold", -60, 0, comp.threshold_db, step=1, suffix=" dB")
    threshold.valueChanged.connect(lambda v: setattr(comp, "threshold_db", v))

    ratio = ParamSlider("Ratio", 1, 20, comp.ratio, step=0.5, suffix=":1")
    ratio.valueChanged.connect(lambda v: setattr(comp, "ratio", v))

    makeup = ParamSlider("Makeup Gain", 0, 24, comp.makeup_db, step=0.5, suffix=" dB")
    makeup.valueChanged.connect(lambda v: setattr(comp, "makeup_db", v))

    return _group(
        "Compressor", comp.enabled, lambda on: setattr(comp, "enabled", on), [threshold, ratio, makeup]
    )


def build_eq_panel(eq):
    low_gain = ParamSlider("Low Shelf Gain", -12, 12, eq.low_gain_db, step=0.5, suffix=" dB")
    low_gain.valueChanged.connect(lambda v: eq.set_band("low", gain_db=v))

    mid_freq = ParamSlider("Mid Freq", 200, 8000, eq.mid_freq, step=10, suffix=" Hz")
    mid_freq.valueChanged.connect(lambda v: eq.set_band("mid", freq=v))

    mid_gain = ParamSlider("Mid Gain", -12, 12, eq.mid_gain_db, step=0.5, suffix=" dB")
    mid_gain.valueChanged.connect(lambda v: eq.set_band("mid", gain_db=v))

    high_gain = ParamSlider("High Shelf Gain", -12, 12, eq.high_gain_db, step=0.5, suffix=" dB")
    high_gain.valueChanged.connect(lambda v: eq.set_band("high", gain_db=v))

    return _group(
        "Parametric EQ",
        eq.enabled,
        lambda on: setattr(eq, "enabled", on),
        [low_gain, mid_freq, mid_gain, high_gain],
    )


def build_pitch_panel(pitch):
    key_combo = QComboBox()
    key_combo.addItems(NOTE_NAMES)
    key_combo.setCurrentText(pitch.key)
    key_combo.currentTextChanged.connect(lambda v: setattr(pitch, "key", v))

    scale_combo = QComboBox()
    scale_combo.addItems(list(SCALES.keys()))
    scale_combo.setCurrentText(pitch.scale)
    scale_combo.currentTextChanged.connect(lambda v: setattr(pitch, "scale", v))

    key_row_layout = QHBoxLayout()
    key_row_layout.setContentsMargins(0, 0, 0, 0)
    key_row_layout.addWidget(QLabel("Key"))
    key_row_layout.addWidget(key_combo)
    key_row_layout.addWidget(QLabel("Scale"))
    key_row_layout.addWidget(scale_combo)
    key_row = QWidget()
    key_row.setLayout(key_row_layout)

    strength = ParamSlider("Strength", 0, 1, pitch.strength, step=0.05, suffix="")
    strength.valueChanged.connect(lambda v: setattr(pitch, "strength", v))

    speed = ParamSlider("Retune Speed", 5, 200, pitch.speed_ms, step=5, suffix=" ms")
    speed.valueChanged.connect(lambda v: setattr(pitch, "speed_ms", v))

    return _group(
        "Pitch Correction",
        pitch.enabled,
        lambda on: setattr(pitch, "enabled", on),
        [key_row, strength, speed],
    )


def build_robot_panel(robot):
    carrier = ParamSlider("Carrier Freq", 20, 300, robot.carrier_freq, step=5, suffix=" Hz")
    carrier.valueChanged.connect(lambda v: setattr(robot, "carrier_freq", v))

    mix = ParamSlider("Mix", 0, 1, robot.mix, step=0.05, suffix="")
    mix.valueChanged.connect(lambda v: setattr(robot, "mix", v))

    return _group("Robot Voice", robot.enabled, lambda on: setattr(robot, "enabled", on), [carrier, mix])


def build_delay_panel(delay):
    delay_time = ParamSlider("Delay Time", 10, 1000, delay.delay_ms, step=10, suffix=" ms")
    delay_time.valueChanged.connect(lambda v: setattr(delay, "delay_ms", v))

    feedback = ParamSlider("Feedback", 0, 0.9, delay.feedback, step=0.05, suffix="")
    feedback.valueChanged.connect(lambda v: setattr(delay, "feedback", v))

    mix = ParamSlider("Mix", 0, 1, delay.mix, step=0.05, suffix="")
    mix.valueChanged.connect(lambda v: setattr(delay, "mix", v))

    return _group(
        "Delay / Echo", delay.enabled, lambda on: setattr(delay, "enabled", on), [delay_time, feedback, mix]
    )


def build_reverb_panel(reverb):
    room_size = ParamSlider("Room Size", 0.5, 0.98, reverb.room_size, step=0.02, suffix="")
    room_size.valueChanged.connect(lambda v: setattr(reverb, "room_size", v))

    damping = ParamSlider("Damping", 0, 1, reverb.damping, step=0.05, suffix="")
    damping.valueChanged.connect(lambda v: setattr(reverb, "damping", v))

    mix = ParamSlider("Mix", 0, 1, reverb.mix, step=0.05, suffix="")
    mix.valueChanged.connect(lambda v: setattr(reverb, "mix", v))

    return _group(
        "Reverb", reverb.enabled, lambda on: setattr(reverb, "enabled", on), [room_size, damping, mix]
    )
