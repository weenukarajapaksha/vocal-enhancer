"""GUI panels exposing the Milestone 2 DSP chain's parameters and on/off toggles."""

from PySide6.QtWidgets import QGroupBox, QVBoxLayout

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
