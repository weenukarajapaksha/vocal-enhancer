"""Output-only playback of a pre-processed audio buffer, with live level metering."""

import numpy as np
import sounddevice as sd

from .engine import _peak_dbfs


class FilePlayer:
    def __init__(self, samplerate: int, channels: int, output_device=None):
        self.samplerate = samplerate
        self.channels = channels
        self.output_device = output_device

        self._stream: sd.OutputStream | None = None
        self._data: np.ndarray | None = None
        self._pos = 0
        self.output_level_db = -100.0

    def load(self, data: np.ndarray):
        self._data = data
        self._pos = 0

    @property
    def is_playing(self) -> bool:
        return self._stream is not None and self._stream.active

    @property
    def progress_seconds(self) -> tuple[float, float]:
        total = len(self._data) / self.samplerate if self._data is not None else 0.0
        elapsed = min(self._pos, len(self._data)) / self.samplerate if self._data is not None else 0.0
        return elapsed, total

    def _callback(self, outdata, frames, time_info, status):
        remaining = len(self._data) - self._pos
        if remaining <= 0:
            outdata[:] = 0
            raise sd.CallbackStop()

        n = min(frames, remaining)
        chunk = self._data[self._pos : self._pos + n]
        outdata[:n] = chunk
        if n < frames:
            outdata[n:] = 0

        self._pos += n
        self.output_level_db = _peak_dbfs(chunk)

    def start(self):
        self._pos = 0
        self._stream = sd.OutputStream(
            samplerate=self.samplerate,
            channels=self.channels,
            dtype="float32",
            device=self.output_device,
            callback=self._callback,
        )
        self._stream.start()

    def stop(self):
        if self._stream is None:
            return
        self._stream.stop()
        self._stream.close()
        self._stream = None
        self.output_level_db = -100.0
