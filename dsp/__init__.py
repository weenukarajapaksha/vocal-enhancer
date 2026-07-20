from .chain import EffectChain
from .compressor import Compressor
from .delay import Delay
from .eq import ParametricEQ
from .gate import NoiseGate
from .harmony import Harmony
from .pitch import PitchCorrector
from .reverb import Reverb
from .robot import RobotVoice


def default_chain(samplerate: int = 48000, channels: int = 1) -> EffectChain:
    """Signal order: gate -> pitch correction -> harmony -> compressor -> EQ ->
    robot voice -> delay -> reverb.

    The corrective effects (gate/compressor/EQ) are on by default; the creative
    voice effects (pitch/harmony/robot/delay/reverb) start disabled so
    passthrough stays clean until the user opts in.
    """
    return EffectChain(
        [
            ("gate", NoiseGate(samplerate=samplerate)),
            ("pitch", PitchCorrector(samplerate=samplerate)),
            ("harmony", Harmony(samplerate=samplerate)),
            ("compressor", Compressor(samplerate=samplerate)),
            ("eq", ParametricEQ(samplerate=samplerate)),
            ("robot", RobotVoice(samplerate=samplerate)),
            ("delay", Delay(samplerate=samplerate, channels=channels)),
            ("reverb", Reverb(samplerate=samplerate, channels=channels)),
        ]
    )
