"""Envelope-follower compressor with attack/release/ratio/threshold/makeup gain."""

import math

import numpy as np

from .utils import MIN_DB, db_to_linear, smoothing_coef


class Compressor:
    def __init__(
        self,
        threshold_db: float = -24.0,
        ratio: float = 4.0,
        attack_ms: float = 10.0,
        release_ms: float = 150.0,
        makeup_db: float = 0.0,
        samplerate: int = 48000,
    ):
        self.threshold_db = threshold_db
        self.ratio = ratio
        self.attack_ms = attack_ms
        self.release_ms = release_ms
        self.makeup_db = makeup_db
        self.samplerate = samplerate
        self.enabled = True

        self._envelope_db = MIN_DB

    def process(self, block: np.ndarray) -> np.ndarray:
        attack_coef = smoothing_coef(self.attack_ms, self.samplerate)
        release_coef = smoothing_coef(self.release_ms, self.samplerate)
        makeup_lin = db_to_linear(self.makeup_db)
        inv_ratio_term = 1.0 - 1.0 / self.ratio
        envelope_db = self._envelope_db

        # Plain-Python loop: numpy's per-scalar call overhead (np.max/np.abs/np.log10
        # on a single row) dominates over a 256-sample block and blows the callback budget.
        rows = block.tolist()
        channels = block.shape[1]
        out_rows = [None] * len(rows)

        for i, row in enumerate(rows):
            peak = abs(row[0]) if channels == 1 else max(abs(v) for v in row)
            peak_db = math.log10(peak) * 20.0 if peak > 0.0 else MIN_DB

            coef = release_coef if peak_db < envelope_db else attack_coef
            envelope_db = coef * envelope_db + (1.0 - coef) * peak_db

            if envelope_db > self.threshold_db:
                reduction_db = (self.threshold_db - envelope_db) * inv_ratio_term
                gain = 10.0 ** (reduction_db / 20.0) * makeup_lin
            else:
                gain = makeup_lin

            out_rows[i] = [v * gain for v in row]

        self._envelope_db = envelope_db
        return np.array(out_rows, dtype=block.dtype)
