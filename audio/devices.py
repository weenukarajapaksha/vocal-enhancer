"""Device discovery helpers built on top of sounddevice/PortAudio."""

import sounddevice as sd


def list_devices() -> None:
    """Print all available audio devices with their indices."""
    print(sd.query_devices())


def default_devices() -> tuple[int, int]:
    """Return (input_index, output_index) for the system default devices."""
    return sd.default.device


_PREFERRED_HOST_APIS = ("Windows WASAPI", "Windows DirectSound")


def best_default_devices() -> tuple[int, int]:
    """Like `default_devices()`, but prefers a lower-latency host API (WASAPI, then
    DirectSound) for the same physical device -- the OS default is often the legacy
    MME API, which can add 150+ ms of extra buffering.
    """
    devices = sd.query_devices()
    hostapis = sd.query_hostapis()

    def find_best(default_index, kind):
        if default_index is None or default_index < 0:
            return default_index
        default_name = devices[default_index]["name"].strip()

        for preferred_api in _PREFERRED_HOST_APIS:
            for i, d in enumerate(devices):
                if d[f"max_{kind}_channels"] <= 0:
                    continue
                if hostapis[d["hostapi"]]["name"] != preferred_api:
                    continue
                name = d["name"].strip()
                # MME device names are truncated to 31 chars, so match by prefix.
                if name.startswith(default_name) or default_name.startswith(name):
                    return i
        return default_index

    default_in, default_out = sd.default.device
    return find_best(default_in, "input"), find_best(default_out, "output")


def device_choices(kind: str) -> list[tuple[str, int]]:
    """Return [(display_name, index), ...] for devices usable as `kind` ('input' or 'output')."""
    return [
        (f"{i}: {d['name']}", i)
        for i, d in enumerate(sd.query_devices())
        if d[f"max_{kind}_channels"] > 0
    ]


def resolve_device(device: int | str | None, kind: str):
    """Resolve a user-supplied device argument (index, name substring, or None).

    `kind` is 'input' or 'output', used only for a clearer error message.
    """
    if device is None:
        return None
    try:
        return int(device)
    except ValueError:
        pass

    matches = [
        i
        for i, d in enumerate(sd.query_devices())
        if device.lower() in d["name"].lower() and d[f"max_{kind}_channels"] > 0
    ]
    if not matches:
        raise ValueError(f"No {kind} device matching '{device}' found.")
    if len(matches) > 1:
        names = ", ".join(f"{i}:{sd.query_devices(i)['name']}" for i in matches)
        raise ValueError(f"Ambiguous {kind} device '{device}', matches: {names}")
    return matches[0]
