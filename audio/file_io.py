"""Load an audio file from disk for offline processing."""

import numpy as np
import soundfile as sf

SUPPORTED_EXTENSIONS = "Audio Files (*.wav *.flac *.ogg *.aiff *.aif)"


def load_audio_file(path: str) -> tuple[np.ndarray, int]:
    """Returns (data, samplerate). data has shape (frames, channels), float32."""
    data, samplerate = sf.read(path, dtype="float32", always_2d=True)
    return data, samplerate
