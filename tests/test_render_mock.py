import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from render_mock import BLANK_TILE, CHR_BYTES, COLUMNS, HEIGHT, render_chr


class RenderMockTests(unittest.TestCase):
    def test_size(self):
        self.assertEqual(len(render_chr([0] * COLUMNS)), CHR_BYTES)

    def test_blank_graph(self):
        data = render_chr([0] * COLUMNS)
        self.assertEqual(data, bytes(CHR_BYTES))

    def test_full_height_bar(self):
        heights = [0] * COLUMNS
        heights[0] = HEIGHT
        data = render_chr(heights)

        for tile_row in range(8):
            base = (tile_row * COLUMNS) * 16
            self.assertEqual(data[base:base + 8], bytes([0x7E] * 8))
            self.assertEqual(data[base + 8:base + 16], bytes(8))

    def test_reserved_blank_tile(self):
        data = render_chr([HEIGHT] * COLUMNS)
        base = BLANK_TILE * 16
        self.assertEqual(data[base:base + 16], bytes(16))


if __name__ == "__main__":
    unittest.main()
