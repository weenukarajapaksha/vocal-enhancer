"""Milestone 1: audio passthrough skeleton.

Mic in -> (no processing) -> speaker out, with startup diagnostics.
"""

import argparse
import sys

from audio.devices import list_devices, resolve_device
from audio.engine import AudioEngine


def parse_args():
    parser = argparse.ArgumentParser(description="Real-time vocal enhancer (passthrough)")
    parser.add_argument("--list-devices", action="store_true", help="list audio devices and exit")
    parser.add_argument("--input-device", default=None, help="input device index or name substring")
    parser.add_argument("--output-device", default=None, help="output device index or name substring")
    parser.add_argument("--samplerate", type=int, default=48000)
    parser.add_argument("--blocksize", type=int, default=256)
    parser.add_argument("--channels", type=int, default=1)
    return parser.parse_args()


def main():
    args = parse_args()

    if args.list_devices:
        list_devices()
        return

    try:
        input_device = resolve_device(args.input_device, "input")
        output_device = resolve_device(args.output_device, "output")
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    engine = AudioEngine(
        samplerate=args.samplerate,
        blocksize=args.blocksize,
        channels=args.channels,
        input_device=input_device,
        output_device=output_device,
    )
    engine.run_forever()


if __name__ == "__main__":
    main()
