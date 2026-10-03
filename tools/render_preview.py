#!/usr/bin/env python3
"""Render NES-SDR CHR + nametable assets to a dependency-free PNG preview."""

from __future__ import annotations

import argparse
import struct
import zlib
from pathlib import Path

WIDTH = 256
HEIGHT = 240

# Review palette only. The real Famicom uses the palette bytes in main.s.
RGB = (
    (12, 14, 18),       # background
    (232, 242, 232),    # plane 0
    (190, 48, 40),      # plane 1 / Famicom-red axis / future peak trace
    (255, 255, 255),    # overlap
)


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    body = kind + payload
    return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)


def write_png(path: Path, width: int, height: int, rgb: bytes) -> None:
    if len(rgb) != width * height * 3:
        raise ValueError("RGB byte count does not match image dimensions")

    scanlines = bytearray()
    stride = width * 3
    for y in range(height):
        scanlines.append(0)  # PNG filter: None
        start = y * stride
        scanlines.extend(rgb[start:start + stride])

    data = bytearray(b"\x89PNG\r\n\x1a\n")
    data.extend(png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)))
    data.extend(png_chunk(b"IDAT", zlib.compress(bytes(scanlines), 9)))
    data.extend(png_chunk(b"IEND", b""))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def decode_pixel(chr_data: bytes, tile: int, px: int, py: int) -> int:
    base = tile * 16
    lo = chr_data[base + py]
    hi = chr_data[base + 8 + py]
    bit = 7 - px
    return ((lo >> bit) & 1) | (((hi >> bit) & 1) << 1)


def render(chr_data: bytes, nametable: bytes) -> bytes:
    if len(chr_data) != 8192:
        raise ValueError("CHR must be exactly 8192 bytes")
    if len(nametable) != 960:
        raise ValueError("nametable must be exactly 960 bytes")

    out = bytearray(WIDTH * HEIGHT * 3)
    for ty in range(30):
        for tx in range(32):
            tile = nametable[ty * 32 + tx]
            for py in range(8):
                y = ty * 8 + py
                for px in range(8):
                    x = tx * 8 + px
                    color = RGB[decode_pixel(chr_data, tile, px, py)]
                    at = (y * WIDTH + x) * 3
                    out[at:at + 3] = bytes(color)
    return bytes(out)


def scale_nearest(rgb: bytes, scale: int) -> tuple[int, int, bytes]:
    if scale <= 1:
        return WIDTH, HEIGHT, rgb

    sw = WIDTH * scale
    sh = HEIGHT * scale
    out = bytearray(sw * sh * 3)
    for y in range(HEIGHT):
        row = rgb[y * WIDTH * 3:(y + 1) * WIDTH * 3]
        expanded = bytearray()
        for x in range(WIDTH):
            pixel = row[x * 3:x * 3 + 3]
            expanded.extend(pixel * scale)
        for sy in range(scale):
            start = ((y * scale + sy) * sw) * 3
            out[start:start + sw * 3] = expanded
    return sw, sh, bytes(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chr", type=Path, required=True)
    parser.add_argument("--nametable", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--scale", type=int, default=2)
    args = parser.parse_args()

    rgb = render(args.chr.read_bytes(), args.nametable.read_bytes())
    width, height, rgb = scale_nearest(rgb, max(1, args.scale))
    write_png(args.out, width, height, rgb)
    print(f"wrote {width}x{height} preview to {args.out}")


if __name__ == "__main__":
    main()
