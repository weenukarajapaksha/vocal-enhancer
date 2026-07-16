"""Shared dB/linear conversions for DSP modules."""

import numpy as np

MIN_DB = -100.0


def db_to_linear(db: float) -> float:
    return 10.0 ** (db / 20.0)


def linear_to_db(value: float) -> float:
    if value <= 0.0:
        return MIN_DB
    return max(20.0 * np.log10(value), MIN_DB)


def smoothing_coef(time_ms: float, samplerate: int) -> float:
    """One-pole smoothing coefficient for a given attack/release time constant."""
    time_ms = max(time_ms, 0.001)
    return float(np.exp(-1.0 / (time_ms * 0.001 * samplerate)))
