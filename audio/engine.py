"""Real-time audio engine: duplex stream with a pluggable processing hook.

Milestone 1 wires this up as pure passthrough (mic -> speakers, unmodified).
Milestone 2 will pass in a real `processor` callable (the DSP chain) instead
of the default identity function -- no other changes to this file should be
needed.
"""

import time

import numpy as np
import sounddevice as sd


def passthrough(indata: np.ndarray) -> np.ndarray:
    """Identity processor: output equals input, unmodified."""
    return indata


def _peak_dbfs(block: np.ndarray) -> float:
    """Peak level of a float32 buffer in dBFS (0 dBFS = full scale)."""
    peak = float(np.max(np.abs(block))) if block.size else 0.0
    if peak <= 0.0:
        return -100.0
    return max(20.0 * np.log10(peak), -100.0)


class AudioEngine:
    def __init__(
        self,
        samplerate: int = 48000,
        blocksize: int = 256,
        channels: int = 1,
        input_device=None,
        output_device=None,
        processor=passthrough,
        latency_hint="low",
    ):
        self.samplerate = samplerate
        self.blocksize = blocksize
        self.channels = channels
        self.input_device = input_device
        self.output_device = output_device
        self.processor = processor
        self.latency_hint = latency_hint

        self._stream: sd.Stream | None = None
        self._callback_durations: list[float] = []
        self._xruns = 0

        # Read from any thread for live level meters; each callback overwrites
        # these with a single float, which is an atomic operation under the GIL.
        self.input_level_db = -100.0
        self.output_level_db = -100.0

    @property
    def is_running(self) -> bool:
        return self._stream is not None and self._stream.active

    @property
    def latency(self) -> tuple[float, float]:
        """(input_latency, output_latency) in seconds, valid once started."""
        return self._stream.latency

    def _callback(self, indata, outdata, frames, time_info, status):
        start = time.perf_counter()

        if status:
            # input/output underflow or overflow reported by PortAudio
            self._xruns += 1
            print(f"[audio] stream status: {status}", flush=True)

        outdata[:] = self.processor(indata)

        self.input_level_db = _peak_dbfs(indata)
        self.output_level_db = _peak_dbfs(outdata)

        self._callback_durations.append(time.perf_counter() - start)

    def _open_stream(self, latency):
        return sd.Stream(
            samplerate=self.samplerate,
            blocksize=self.blocksize,
            channels=self.channels,
            dtype="float32",
            device=(self.input_device, self.output_device),
            latency=latency,
            callback=self._callback,
        )

    def start(self):
        try:
            self._stream = self._open_stream(self.latency_hint)
        except sd.PortAudioError:
            # Some host API / device combinations reject a low-latency request outright;
            # fall back to the driver's default buffering rather than failing to start.
            self._stream = self._open_stream(None)
        self._stream.start()

        in_latency, out_latency = self._stream.latency
        print("[audio] stream started", flush=True)
        print(f"[audio] samplerate: {self._stream.samplerate:.0f} Hz", flush=True)
        print(f"[audio] blocksize: {self.blocksize} frames", flush=True)
        print(
            f"[audio] measured latency: input={in_latency * 1000:.1f} ms, "
            f"output={out_latency * 1000:.1f} ms, "
            f"round-trip={(in_latency + out_latency) * 1000:.1f} ms",
            flush=True,
        )

    def stop(self):
        if self._stream is None:
            return
        self._stream.stop()
        self._stream.close()

        if self._callback_durations:
            budget_ms = self.blocksize / self.samplerate * 1000
            durations_ms = [d * 1000 for d in self._callback_durations]
            print("[audio] stream stopped", flush=True)
            print(
                f"[audio] callback time (ms) -- avg: {sum(durations_ms) / len(durations_ms):.3f}, "
                f"max: {max(durations_ms):.3f}, budget: {budget_ms:.3f}",
                flush=True,
            )
            print(f"[audio] status flags reported: {self._xruns}", flush=True)

    def run_forever(self):
        """Block until interrupted (Ctrl+C), then stop cleanly."""
        self.start()
        try:
            print("[audio] running -- press Ctrl+C to stop", flush=True)
            while True:
                sd.sleep(200)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
