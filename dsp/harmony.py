"""Fixed-interval harmony: layers 1-2 pitch-shifted copies of the voice at
chosen semitone intervals (e.g. a third and a fifth) under the dry signal.

Unlike PitchCorrector, this doesn't need pitch detection -- shifting "up a
major third" is a fixed ratio (2**(4/12)) regardless of what note is being
sung, so it just reuses the granular shifter directly.
"""

import numpy as np

from .pitch import _GranularPitchShifter


class Harmony:
    def __init__(
        self,
        samplerate: int = 48000,
        voice1_semitones: float = 4.0,
        voice1_mix: float = 0.5,
        voice2_semitones: float = 7.0,
        voice2_mix: float = 0.0,
        dry_mix: float = 1.0,
    ):
        self.samplerate = samplerate
        self.voice1_semitones = voice1_semitones
        self.voice1_mix = voice1_mix
        self.voice2_semitones = voice2_semitones
        self.voice2_mix = voice2_mix
        self.dry_mix = dry_mix
        self.enabled = False

        self._shifter1 = _GranularPitchShifter(samplerate)
        self._shifter2 = _GranularPitchShifter(samplerate)

    def process(self, block: np.ndarray) -> np.ndarray:
        frames, channels = block.shape
        ratio1 = 2.0 ** (self.voice1_semitones / 12.0)
        ratio2 = 2.0 ** (self.voice2_semitones / 12.0)
        dry_mix = self.dry_mix
        mix1 = self.voice1_mix
        mix2 = self.voice2_mix
        shifter1 = self._shifter1
        shifter2 = self._shifter2

        rows = block.tolist()
        out_rows = [None] * frames

        for i, row in enumerate(rows):
            mono = row[0] if channels == 1 else sum(row) / channels
            voice1 = shifter1.process_sample(mono, ratio1)
            voice2 = shifter2.process_sample(mono, ratio2)
            out_val = mono * dry_mix + voice1 * mix1 + voice2 * mix2
            out_rows[i] = [out_val] * channels

        return np.array(out_rows, dtype=block.dtype)
