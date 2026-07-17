"""Simple Schroeder/Freeverb-style reverb: parallel comb filters + series allpass filters."""

import numpy as np

_COMB_DELAYS_MS = [29.7, 37.1, 41.1, 43.7]
_ALLPASS_DELAYS_MS = [5.0, 1.7]
_ALLPASS_GAIN = 0.5


class _CombFilter:
    def __init__(self, delay_samples: int):
        self.buffer = [0.0] * delay_samples
        self.pos = 0
        self.feedback = 0.8
        self.damping = 0.5
        self._filter_state = 0.0

    def process_sample(self, x: float) -> float:
        y = self.buffer[self.pos]
        self._filter_state = y * (1.0 - self.damping) + self._filter_state * self.damping
        self.buffer[self.pos] = x + self._filter_state * self.feedback
        self.pos = (self.pos + 1) % len(self.buffer)
        return y


class _AllpassFilter:
    def __init__(self, delay_samples: int, gain: float = _ALLPASS_GAIN):
        self.buffer = [0.0] * delay_samples
        self.pos = 0
        self.gain = gain

    def process_sample(self, x: float) -> float:
        buffered = self.buffer[self.pos]
        y = -self.gain * x + buffered
        self.buffer[self.pos] = x + buffered * self.gain
        self.pos = (self.pos + 1) % len(self.buffer)
        return y


class Reverb:
    def __init__(
        self,
        room_size: float = 0.8,
        damping: float = 0.5,
        mix: float = 0.3,
        samplerate: int = 48000,
        channels: int = 1,
    ):
        self.room_size = room_size
        self.damping = damping
        self.mix = mix
        self.samplerate = samplerate
        self.enabled = False

        # Allocated up front to avoid allocating filter buffers inside the real-time callback.
        self._channel_banks = [self._make_bank() for _ in range(channels)]

    def _make_bank(self):
        combs = [_CombFilter(int(ms * 0.001 * self.samplerate)) for ms in _COMB_DELAYS_MS]
        allpasses = [_AllpassFilter(int(ms * 0.001 * self.samplerate)) for ms in _ALLPASS_DELAYS_MS]
        return combs, allpasses

    def process(self, block: np.ndarray) -> np.ndarray:
        frames, channels = block.shape
        if len(self._channel_banks) != channels:
            self._channel_banks = [self._make_bank() for _ in range(channels)]

        for combs, _ in self._channel_banks:
            for comb in combs:
                comb.feedback = self.room_size
                comb.damping = self.damping

        mix = self.mix
        rows = block.tolist()
        out_rows = [None] * frames

        for i, row in enumerate(rows):
            out_row = [0.0] * channels
            for c in range(channels):
                x = row[c]
                combs, allpasses = self._channel_banks[c]
                wet = sum(comb.process_sample(x) for comb in combs) / len(combs)
                for ap in allpasses:
                    wet = ap.process_sample(wet)
                out_row[c] = x * (1.0 - mix) + wet * mix
            out_rows[i] = out_row

        return np.array(out_rows, dtype=block.dtype)
