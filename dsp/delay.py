"""Feedback echo/delay effect."""

import numpy as np

MAX_DELAY_MS = 2000.0


class Delay:
    def __init__(
        self,
        delay_ms: float = 300.0,
        feedback: float = 0.3,
        mix: float = 0.3,
        samplerate: int = 48000,
        channels: int = 1,
    ):
        self.delay_ms = delay_ms
        self.feedback = feedback
        self.mix = mix
        self.samplerate = samplerate
        self.enabled = False

        # Allocated up front -- allocating ~96000-sample buffers lazily on the
        # first real-time callback caused a 40ms+ callback spike (budget is ~5ms).
        self._buffer_len = int(MAX_DELAY_MS * 0.001 * samplerate)
        self._buffer = [[0.0] * channels for _ in range(self._buffer_len)]
        self._write_pos = 0

    def process(self, block: np.ndarray) -> np.ndarray:
        frames, channels = block.shape
        if len(self._buffer[0]) != channels:
            self._buffer = [[0.0] * channels for _ in range(self._buffer_len)]
            self._write_pos = 0

        buf = self._buffer
        buf_len = self._buffer_len
        write_pos = self._write_pos
        feedback = self.feedback
        mix = self.mix
        delay_samples = max(1, min(int(self.delay_ms * 0.001 * self.samplerate), buf_len - 1))

        rows = block.tolist()
        out_rows = [None] * frames

        for i, row in enumerate(rows):
            read_pos = (write_pos - delay_samples) % buf_len
            delayed = buf[read_pos]

            out_rows[i] = [row[c] * (1.0 - mix) + delayed[c] * mix for c in range(channels)]
            buf[write_pos] = [row[c] + delayed[c] * feedback for c in range(channels)]

            write_pos = (write_pos + 1) % buf_len

        self._write_pos = write_pos
        return np.array(out_rows, dtype=block.dtype)
