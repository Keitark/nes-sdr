#!/usr/bin/env python3
"""Reference NES-SDR CHR renderer and synthetic spectrum generator."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

COLUMNS = 31
ROWS = 8
HEIGHT = 64
CHR_BYTES = 8192
TILE_BYTES = 16
BLANK_TILE = 248


def synthetic_heights() -> list[int]:
    out: list[int] = []
    for x in range(COLUMNS):
        baseline = 8 + int(5 * math.sin(x * 0.55) ** 2)
        peak_a = int(48 * math.exp(-((x - 9) / 2.2) ** 2))
        peak_b = int(35 * math.exp(-((x - 22) / 3.0) ** 2))
        out.append(min(HEIGHT, baseline + peak_a + peak_b))
    return out


def render_chr(heights: list[int]) -> bytes:
    if len(heights) != COLUMNS:
        raise ValueError(f"expected {COLUMNS} heights")

    chr_data = bytearray(CHR_BYTES)

    for tile_row in range(ROWS):
        for x, raw_height in enumerate(heights):
            height = max(0, min(HEIGHT, int(raw_height)))
            tile = tile_row * COLUMNS + x
            base = tile * TILE_BYTES
            fill_from = HEIGHT - height

            for py in range(8):
                global_y = tile_row * 8 + py
                chr_data[base + py] = 0x7E if global_y >= fill_from else 0x00
                chr_data[base + 8 + py] = 0x00

    return bytes(chr_data)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    data = render_chr(synthetic_heights())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(data)
    print(f"wrote {len(data)} bytes to {args.out}")


if __name__ == "__main__":
    main()
