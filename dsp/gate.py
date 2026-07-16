"""Threshold-based noise gate with attack/release smoothing."""

import numpy as np

from .utils import db_to_linear, smoothing_coef


class NoiseGate:
    def __init__(
        self,
        threshold_db: float = -50.0,
        attack_ms: float = 2.0,
        release_ms: float = 150.0,
        samplerate: int = 48000,
    ):
        self.threshold_db = threshold_db
        self.attack_ms = attack_ms
        self.release_ms = release_ms
        self.samplerate = samplerate
        self.enabled = True

        self._envelope = 0.0  # linear peak envelope of the input
        self._gain = 1.0  # smoothed gate gain currently applied

    def process(self, block: np.ndarray) -> np.ndarray:
        attack_coef = smoothing_coef(self.attack_ms, self.samplerate)
        release_coef = smoothing_coef(self.release_ms, self.samplerate)
        threshold_lin = db_to_linear(self.threshold_db)
        envelope = self._envelope
        gain = self._gain

        # Plain-Python loop: numpy's per-scalar call overhead (np.max/np.abs on a
        # single row) dominates over a 256-sample block and blows the callback budget.
        rows = block.tolist()
        channels = block.shape[1]
        out_rows = [None] * len(rows)

        for i, row in enumerate(rows):
            peak = abs(row[0]) if channels == 1 else max(abs(v) for v in row)
            coef = release_coef if peak < envelope else attack_coef
            envelope = coef * envelope + (1.0 - coef) * peak

            target_gain = 1.0 if envelope >= threshold_lin else 0.0
            gain_coef = release_coef if target_gain < gain else attack_coef
            gain = gain_coef * gain + (1.0 - gain_coef) * target_gain

            out_rows[i] = [v * gain for v in row]

        self._envelope = envelope
        self._gain = gain
        return np.array(out_rows, dtype=block.dtype)
