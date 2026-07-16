"""Ordered, individually toggleable sequence of DSP effects."""

import numpy as np


class EffectChain:
    """Each effect must expose `process(block) -> block` and an `enabled` flag."""

    def __init__(self, effects: list[tuple[str, object]]):
        self.effects = effects

    def __call__(self, block: np.ndarray) -> np.ndarray:
        for _, effect in self.effects:
            if effect.enabled:
                block = effect.process(block)
        return block

    def get(self, name: str):
        for effect_name, effect in self.effects:
            if effect_name == name:
                return effect
        raise KeyError(name)
