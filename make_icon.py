#!/usr/bin/env python3
"""Draw icon.png, the home-screen icon.

Written by hand with zlib so the project needs no image library. iOS rounds
the corners itself, so this only has to be a flat 180x180 square: a deep
lake-blue gradient with two pale waves across the lower half.

    python make_icon.py
"""

import math
import pathlib
import struct
import zlib

SIZE = 180
OUTPUT = pathlib.Path(__file__).parent / "icon.png"

TOP = (13, 63, 94)      # sky-ish deep blue
BOTTOM = (7, 36, 56)    # darker water
WAVE = (226, 240, 248)  # pale foam


def chunk(tag, payload):
    body = tag + payload
    return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body))


def pixel(x, y):
    t = y / (SIZE - 1)
    base = tuple(round(TOP[i] + (BOTTOM[i] - TOP[i]) * t) for i in range(3))

    # Two waves, the lower one heavier and slightly out of phase.
    for centre, amplitude, phase, thickness in ((114, 7, 0.0, 5), (140, 9, 1.9, 7)):
        crest = centre + amplitude * math.sin(x / SIZE * 2 * math.pi * 1.6 + phase)
        edge = abs(y - crest)
        if edge < thickness:
            # Soften the last pixel of each edge so the curve is not jagged.
            alpha = min(1.0, thickness - edge)
            base = tuple(round(base[i] + (WAVE[i] - base[i]) * alpha) for i in range(3))
    return base


def main():
    raw = bytearray()
    for y in range(SIZE):
        raw.append(0)  # PNG filter type 0 for this scanline
        for x in range(SIZE):
            raw.extend(pixel(x, y))

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", SIZE, SIZE, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    OUTPUT.write_bytes(png)
    print(f"Wrote {OUTPUT.name} ({SIZE}x{SIZE}, {len(png)} bytes)")


if __name__ == "__main__":
    main()
