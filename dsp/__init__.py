from .chain import EffectChain
from .compressor import Compressor
from .eq import ParametricEQ
from .gate import NoiseGate


def default_chain(samplerate: int = 48000) -> EffectChain:
    """The Milestone 2 chain in signal order: gate -> compressor -> EQ."""
    return EffectChain(
        [
            ("gate", NoiseGate(samplerate=samplerate)),
            ("compressor", Compressor(samplerate=samplerate)),
            ("eq", ParametricEQ(samplerate=samplerate)),
        ]
    )
