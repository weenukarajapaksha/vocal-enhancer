"""Save/load named DSP chain parameter sets as JSON files under presets/."""

import json
import re
from pathlib import Path

PRESETS_DIR = Path(__file__).resolve().parent.parent / "presets"

_VALID_NAME_RE = re.compile(r"^[A-Za-z0-9 _-]{1,60}$")

# Which attributes to save/restore per effect -- deliberately excludes internal
# state (buffers, envelope followers, filter delay lines, etc.).
PARAM_SPECS = {
    "gate": ["enabled", "threshold_db", "attack_ms", "release_ms"],
    "pitch": ["enabled", "strength", "speed_ms", "key", "scale"],
    "harmony": ["enabled", "voice1_semitones", "voice1_mix", "voice2_semitones", "voice2_mix", "dry_mix"],
    "compressor": ["enabled", "threshold_db", "ratio", "attack_ms", "release_ms", "makeup_db"],
    "eq": ["enabled", "low_freq", "low_gain_db", "mid_freq", "mid_gain_db", "mid_q", "high_freq", "high_gain_db"],
    "robot": ["enabled", "carrier_freq", "mix"],
    "delay": ["enabled", "delay_ms", "feedback", "mix"],
    "reverb": ["enabled", "room_size", "damping", "mix"],
}


def _validate_name(name: str) -> str:
    name = name.strip()
    if not _VALID_NAME_RE.match(name):
        raise ValueError("Preset name must be 1-60 characters: letters, numbers, spaces, - or _")
    return name


def chain_to_dict(chain) -> dict:
    return {
        name: {attr: getattr(effect, attr) for attr in PARAM_SPECS.get(name, [])}
        for name, effect in chain.effects
    }


def apply_dict_to_chain(chain, data: dict) -> None:
    for name, params in data.items():
        try:
            effect = chain.get(name)
        except KeyError:
            continue
        for attr, value in params.items():
            setattr(effect, attr, value)
        # EQ (and any future effect with derived filter coefficients) needs a
        # recompute after its raw parameters are restored via setattr.
        if hasattr(effect, "_update_coefficients"):
            effect._update_coefficients()


def list_presets() -> list[str]:
    if not PRESETS_DIR.exists():
        return []
    return sorted(p.stem for p in PRESETS_DIR.glob("*.json"))


def save_preset(chain, name: str) -> str:
    name = _validate_name(name)
    PRESETS_DIR.mkdir(exist_ok=True)
    path = PRESETS_DIR / f"{name}.json"
    with open(path, "w") as f:
        json.dump(chain_to_dict(chain), f, indent=2)
    return name


def load_preset(chain, name: str) -> None:
    path = PRESETS_DIR / f"{name}.json"
    with open(path) as f:
        data = json.load(f)
    apply_dict_to_chain(chain, data)


def delete_preset(name: str) -> None:
    path = PRESETS_DIR / f"{name}.json"
    path.unlink(missing_ok=True)
