"""3-band parametric EQ (low-shelf, mid-peak, high-shelf) using RBJ biquads."""

import numpy as np
from scipy.signal import lfilter


def _low_shelf_coefs(freq, gain_db, samplerate, s=1.0):
    A = 10.0 ** (gain_db / 40.0)
    w0 = 2 * np.pi * freq / samplerate
    cos_w0, sin_w0 = np.cos(w0), np.sin(w0)
    alpha = sin_w0 / 2 * np.sqrt((A + 1 / A) * (1 / s - 1) + 2)
    sqrt_a = np.sqrt(A)

    b0 = A * ((A + 1) - (A - 1) * cos_w0 + 2 * sqrt_a * alpha)
    b1 = 2 * A * ((A - 1) - (A + 1) * cos_w0)
    b2 = A * ((A + 1) - (A - 1) * cos_w0 - 2 * sqrt_a * alpha)
    a0 = (A + 1) + (A - 1) * cos_w0 + 2 * sqrt_a * alpha
    a1 = -2 * ((A - 1) + (A + 1) * cos_w0)
    a2 = (A + 1) + (A - 1) * cos_w0 - 2 * sqrt_a * alpha

    return np.array([b0, b1, b2]) / a0, np.array([a0, a1, a2]) / a0


def _high_shelf_coefs(freq, gain_db, samplerate, s=1.0):
    A = 10.0 ** (gain_db / 40.0)
    w0 = 2 * np.pi * freq / samplerate
    cos_w0, sin_w0 = np.cos(w0), np.sin(w0)
    alpha = sin_w0 / 2 * np.sqrt((A + 1 / A) * (1 / s - 1) + 2)
    sqrt_a = np.sqrt(A)

    b0 = A * ((A + 1) + (A - 1) * cos_w0 + 2 * sqrt_a * alpha)
    b1 = -2 * A * ((A - 1) + (A + 1) * cos_w0)
    b2 = A * ((A + 1) + (A - 1) * cos_w0 - 2 * sqrt_a * alpha)
    a0 = (A + 1) - (A - 1) * cos_w0 + 2 * sqrt_a * alpha
    a1 = 2 * ((A - 1) - (A + 1) * cos_w0)
    a2 = (A + 1) - (A - 1) * cos_w0 - 2 * sqrt_a * alpha

    return np.array([b0, b1, b2]) / a0, np.array([a0, a1, a2]) / a0


def _peaking_coefs(freq, gain_db, q, samplerate):
    A = 10.0 ** (gain_db / 40.0)
    w0 = 2 * np.pi * freq / samplerate
    cos_w0, sin_w0 = np.cos(w0), np.sin(w0)
    alpha = sin_w0 / (2 * q)

    b0 = 1 + alpha * A
    b1 = -2 * cos_w0
    b2 = 1 - alpha * A
    a0 = 1 + alpha / A
    a1 = -2 * cos_w0
    a2 = 1 - alpha / A

    return np.array([b0, b1, b2]) / a0, np.array([a0, a1, a2]) / a0


class Biquad:
    """Single biquad section with filter state (zi) persisted across blocks."""

    def __init__(self):
        self.b = np.array([1.0, 0.0, 0.0])
        self.a = np.array([1.0, 0.0, 0.0])
        self._zi = None

    def set_coefficients(self, b, a):
        self.b, self.a = b, a

    def process(self, block: np.ndarray) -> np.ndarray:
        channels = block.shape[1]
        if self._zi is None or self._zi.shape[1] != channels:
            self._zi = np.zeros((2, channels))

        out = np.empty_like(block)
        for ch in range(channels):
            out[:, ch], self._zi[:, ch] = lfilter(self.b, self.a, block[:, ch], zi=self._zi[:, ch])
        return out


class ParametricEQ:
    """Three fixed bands: low-shelf, mid-peak, high-shelf."""

    def __init__(
        self,
        samplerate: int = 48000,
        low_freq: float = 120.0,
        low_gain_db: float = 0.0,
        mid_freq: float = 1000.0,
        mid_gain_db: float = 0.0,
        mid_q: float = 1.0,
        high_freq: float = 8000.0,
        high_gain_db: float = 0.0,
    ):
        self.samplerate = samplerate
        self.low_freq = low_freq
        self.low_gain_db = low_gain_db
        self.mid_freq = mid_freq
        self.mid_gain_db = mid_gain_db
        self.mid_q = mid_q
        self.high_freq = high_freq
        self.high_gain_db = high_gain_db
        self.enabled = True

        self._low = Biquad()
        self._mid = Biquad()
        self._high = Biquad()
        self._update_coefficients()

    def _update_coefficients(self):
        self._low.set_coefficients(*_low_shelf_coefs(self.low_freq, self.low_gain_db, self.samplerate))
        self._mid.set_coefficients(*_peaking_coefs(self.mid_freq, self.mid_gain_db, self.mid_q, self.samplerate))
        self._high.set_coefficients(*_high_shelf_coefs(self.high_freq, self.high_gain_db, self.samplerate))

    def set_band(self, band: str, **params):
        """Update one band's parameters, e.g. set_band('mid', gain_db=3.0, q=1.4)."""
        for key, value in params.items():
            setattr(self, f"{band}_{key}", value)
        self._update_coefficients()

    def process(self, block: np.ndarray) -> np.ndarray:
        block = self._low.process(block)
        block = self._mid.process(block)
        block = self._high.process(block)
        return block
