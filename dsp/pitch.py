"""Real-time pitch correction: YIN pitch detection + granular pitch shifting.

This is a prototype-stage implementation: the granular shifter trades some
"warble" character (vs. commercial PSOLA-based Auto-Tune) for something that
is simple enough to run safely in the real-time audio callback.
"""

import math

import numpy as np

from .utils import smoothing_coef


def _yin_frequency(frame: np.ndarray, samplerate: int, fmin: float, fmax: float, threshold: float = 0.15):
    """YIN pitch estimate for one analysis frame. Returns (freq_hz, confidence),
    or (None, 0.0) if the frame looks unvoiced/silent.
    """
    n = len(frame)
    tau_max = min(n // 2, int(samplerate / fmin))
    tau_min = max(2, int(samplerate / fmax))
    if tau_max <= tau_min:
        return None, 0.0

    # Difference function d(tau), computed via FFT autocorrelation (de Cheveigne
    # & Kawahara's fast method) instead of an O(n * tau_max) direct loop.
    size = 1
    while size < n + tau_max:
        size *= 2
    spectrum = np.fft.rfft(frame, n=size)
    acf = np.fft.irfft(spectrum * np.conj(spectrum), n=size)[:tau_max]

    energy = np.concatenate(([0.0], np.cumsum(frame.astype(np.float64) ** 2)))
    taus = np.arange(tau_max)
    e0 = energy[n - taus]
    e1 = energy[n] - energy[taus]
    diff = e0 + e1 - 2 * acf

    cumsum = np.cumsum(diff[1:])
    cmnd = np.ones(tau_max)
    with np.errstate(divide="ignore", invalid="ignore"):
        cmnd[1:] = diff[1:] * taus[1:] / cumsum
    cmnd[1:] = np.where(cumsum > 0, cmnd[1:], 1.0)

    tau_estimate = None
    for tau in range(tau_min, tau_max - 1):
        if cmnd[tau] < threshold:
            while tau + 1 < tau_max and cmnd[tau + 1] < cmnd[tau]:
                tau += 1
            tau_estimate = tau
            break

    if tau_estimate is None:
        return None, 0.0

    if 0 < tau_estimate < tau_max - 1:
        s0, s1, s2 = cmnd[tau_estimate - 1], cmnd[tau_estimate], cmnd[tau_estimate + 1]
        denom = 2 * s1 - s2 - s0
        shift = 0.5 * (s2 - s0) / denom if denom != 0 else 0.0
    else:
        shift = 0.0

    refined_tau = tau_estimate + shift
    if refined_tau <= 0:
        return None, 0.0

    freq = samplerate / refined_tau
    confidence = 1.0 - cmnd[tau_estimate]
    return freq, max(0.0, min(1.0, confidence))


NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

SCALES = {
    "Chromatic": list(range(12)),
    "Major": [0, 2, 4, 5, 7, 9, 11],
    "Minor": [0, 2, 3, 5, 7, 8, 10],
}


def _freq_to_midi(freq: float) -> float:
    return 69.0 + 12.0 * math.log2(freq / 440.0)


def _midi_to_freq(midi: float) -> float:
    return 440.0 * (2.0 ** ((midi - 69.0) / 12.0))


def nearest_scale_frequency(freq: float, key: str = "C", scale: str = "Chromatic") -> float:
    """Snap a frequency to the nearest note (12-TET) in the given key/scale."""
    root_pc = NOTE_NAMES.index(key)
    intervals = SCALES.get(scale, SCALES["Chromatic"])
    allowed_pcs = {(root_pc + iv) % 12 for iv in intervals}

    midi = _freq_to_midi(freq)
    base = round(midi)
    best_candidate, best_dist = None, None
    for offset in range(-6, 7):
        candidate = base + offset
        if candidate % 12 in allowed_pcs:
            dist = abs(candidate - midi)
            if best_dist is None or dist < best_dist:
                best_dist, best_candidate = dist, candidate

    return _midi_to_freq(best_candidate)


class _GranularPitchShifter:
    """Two-tap overlap-add granular pitch shifter: reads a continuously-written
    circular buffer at `ratio` times playback speed via two Hann-windowed,
    half-grain-offset taps, crossfading between them to hide the periodic
    read-position resets.
    """

    def __init__(self, samplerate: int, grain_ms: float = 40.0):
        self.grain_samples = max(64, int(grain_ms * 0.001 * samplerate))
        self._buffer_len = self.grain_samples * 4
        self._buffer = [0.0] * self._buffer_len
        self._write_pos = 0

        self._phase = [0.0, self.grain_samples / 2.0]
        self._read = [0.0, self.grain_samples / 2.0]
        self._window = [
            0.5 * (1 - math.cos(2 * math.pi * i / self.grain_samples)) for i in range(self.grain_samples)
        ]

    def _read_interpolated(self, pos: float) -> float:
        buf = self._buffer
        buf_len = self._buffer_len
        i0 = int(pos) % buf_len
        i1 = (i0 + 1) % buf_len
        frac = pos - int(pos)
        return buf[i0] * (1.0 - frac) + buf[i1] * frac

    def process_sample(self, x: float, ratio: float) -> float:
        buf = self._buffer
        buf_len = self._buffer_len
        grain = self.grain_samples
        window = self._window

        buf[self._write_pos] = x

        w0 = window[int(self._phase[0]) % grain]
        w1 = window[int(self._phase[1]) % grain]
        total_w = w0 + w1
        if total_w > 1e-6:
            out = (self._read_interpolated(self._read[0]) * w0 + self._read_interpolated(self._read[1]) * w1) / total_w
        else:
            out = 0.0

        for tap in (0, 1):
            self._read[tap] = (self._read[tap] + ratio) % buf_len
            self._phase[tap] += 1.0
            if self._phase[tap] >= grain:
                self._phase[tap] -= grain
                # Only resync if this tap's read position has drifted close to
                # colliding with the write pointer -- an unconditional resync
                # every grain would erase the drift that small (typical
                # pitch-correction-sized) ratios rely on to accumulate a shift.
                # Small ratios then resync rarely (near glitch-free); larger
                # ratios resync more often (audible as granular artifacts).
                delay = (self._write_pos - self._read[tap]) % buf_len
                if delay < grain or delay > buf_len - grain:
                    self._read[tap] = (self._write_pos - buf_len // 2) % buf_len

        self._write_pos = (self._write_pos + 1) % buf_len
        return out


class PitchCorrector:
    def __init__(
        self,
        samplerate: int = 48000,
        strength: float = 1.0,
        speed_ms: float = 15.0,
        key: str = "C",
        scale: str = "Chromatic",
        fmin: float = 70.0,
        fmax: float = 1000.0,
        analysis_ms: float = 42.0,
        hop_ms: float = 10.0,
    ):
        self.samplerate = samplerate
        self.strength = strength
        self.speed_ms = speed_ms
        self.key = key
        self.scale = scale
        self.fmin = fmin
        self.fmax = fmax
        self.enabled = False

        self._analysis_len = int(analysis_ms * 0.001 * samplerate)
        self._hop_len = max(1, int(hop_ms * 0.001 * samplerate))
        self._circ_buffer = [0.0] * self._analysis_len
        self._circ_write_pos = 0
        self._samples_since_hop = 0

        self._target_ratio = 1.0
        self._smoothed_ratio = 1.0
        self.detected_freq = None
        self._shifter = _GranularPitchShifter(samplerate)

    def _run_detection(self):
        circ = self._circ_buffer
        pos = self._circ_write_pos
        window = np.array(circ[pos:] + circ[:pos] if pos else circ, dtype=np.float32)

        freq, confidence = _yin_frequency(window, self.samplerate, self.fmin, self.fmax)
        self.detected_freq = freq if confidence > 0.5 else None

        if self.detected_freq is not None:
            target = nearest_scale_frequency(self.detected_freq, self.key, self.scale)
            ratio = target / self.detected_freq
            self._target_ratio = 1.0 + (ratio - 1.0) * self.strength
        else:
            self._target_ratio = 1.0

    def process(self, block: np.ndarray) -> np.ndarray:
        frames, channels = block.shape
        rows = block.tolist()
        out_rows = [None] * frames

        circ = self._circ_buffer
        circ_len = self._analysis_len
        circ_pos = self._circ_write_pos
        samples_since_hop = self._samples_since_hop
        smoothed_ratio = self._smoothed_ratio
        smooth_coef = smoothing_coef(self.speed_ms, self.samplerate)
        shifter = self._shifter

        for i, row in enumerate(rows):
            mono = row[0] if channels == 1 else sum(row) / channels

            circ[circ_pos] = mono
            circ_pos = (circ_pos + 1) % circ_len
            samples_since_hop += 1
            if samples_since_hop >= self._hop_len:
                samples_since_hop = 0
                self._circ_write_pos = circ_pos
                self._run_detection()

            smoothed_ratio = smooth_coef * smoothed_ratio + (1.0 - smooth_coef) * self._target_ratio
            shifted = shifter.process_sample(mono, smoothed_ratio)
            out_rows[i] = [shifted] * channels

        self._circ_write_pos = circ_pos
        self._samples_since_hop = samples_since_hop
        self._smoothed_ratio = smoothed_ratio
        return np.array(out_rows, dtype=block.dtype)
