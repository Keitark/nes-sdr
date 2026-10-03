#!/usr/bin/env python3
"""Reference NES-SDR CHR renderer and synthetic spectrum generator."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from font5x7 import BLANK_TILE, install_font

COLUMNS = 24
ROWS = 8
HEIGHT = 64
CHR_BYTES = 8192
TILE_BYTES = 16
GRAPH_TILES = COLUMNS * ROWS
GRAPH_BYTES = GRAPH_TILES * TILE_BYTES


def synthetic_heights() -> list[int]:
    out: list[int] = []
    for x in range(COLUMNS):
        baseline = 7 + int(4 * math.sin(x * 0.58) ** 2)
        peak_a = int(50 * math.exp(-((x - 7) / 1.8) ** 2))
        peak_b = int(37 * math.exp(-((x - 17) / 2.5) ** 2))
        out.append(min(HEIGHT, baseline + peak_a + peak_b))
    return out


def render_graph(chr_data: bytearray, heights: list[int]) -> None:
    if len(heights) != COLUMNS:
        raise ValueError(f"expected {COLUMNS} heights")

    for tile_row in range(ROWS):
        for x, raw_height in enumerate(heights):
            height = max(0, min(HEIGHT, int(raw_height)))
            tile = tile_row * COLUMNS + x
            base = tile * TILE_BYTES
            fill_from = HEIGHT - height

            for py in range(8):
                global_y = tile_row * 8 + py
                # Six-pixel-wide bar centered in each 8-pixel column.
                chr_data[base + py] = 0x7E if global_y >= fill_from else 0x00
                chr_data[base + 8 + py] = 0x00


def render_chr(heights: list[int]) -> bytes:
    chr_data = bytearray(CHR_BYTES)
    render_graph(chr_data, heights)
    install_font(chr_data)
    return bytes(chr_data)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    data = render_chr(synthetic_heights())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(data)
    print(
        f"wrote {len(data)} bytes to {args.out} "
        f"({GRAPH_BYTES} dynamic graph bytes, UI starts at tile {BLANK_TILE})"
    )


if __name__ == "__main__":
    main()
