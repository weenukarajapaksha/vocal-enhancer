"""Ring-modulation "robot voice" effect."""

import math

import numpy as np


class RobotVoice:
    def __init__(self, carrier_freq: float = 60.0, mix: float = 1.0, samplerate: int = 48000):
        self.carrier_freq = carrier_freq
        self.mix = mix
        self.samplerate = samplerate
        self.enabled = False

        self._phase = 0.0

    def process(self, block: np.ndarray) -> np.ndarray:
        frames, channels = block.shape
        phase = self._phase
        phase_inc = 2.0 * math.pi * self.carrier_freq / self.samplerate
        mix = self.mix

        rows = block.tolist()
        out_rows = [None] * frames

        for i, row in enumerate(rows):
            carrier = math.sin(phase)
            out_rows[i] = [v * (1.0 - mix) + (v * carrier) * mix for v in row]
            phase += phase_inc
            if phase > 2.0 * math.pi:
                phase -= 2.0 * math.pi

        self._phase = phase
        return np.array(out_rows, dtype=block.dtype)
