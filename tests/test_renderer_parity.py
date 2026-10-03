import ctypes
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

from render_mock import (  # noqa: E402
    CHR_BYTES,
    COLUMNS,
    GRAPH_BYTES,
    HEIGHT,
    reduce_bins_u8,
    render_graph,
)


class RendererParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        lib_path = Path(cls.tmp.name) / "libnes_sdr_frame.so"
        subprocess.run(
            [
                "cc",
                "-std=c11",
                "-shared",
                "-fPIC",
                f"-I{ROOT / 'firmware' / 'include'}",
                str(ROOT / "firmware" / "src" / "nes_sdr_frame.c"),
                "-o",
                str(lib_path),
            ],
            check=True,
        )
        cls.lib = ctypes.CDLL(str(lib_path))
        cls.lib.nes_sdr_reduce_bins_u8.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_uint8),
        ]
        cls.lib.nes_sdr_render_graph.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.POINTER(ctypes.c_uint8),
        ]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def c_reduce(self, bins: bytes) -> list[int]:
        src = (ctypes.c_uint8 * len(bins))(*bins)
        dst = (ctypes.c_uint8 * COLUMNS)()
        self.lib.nes_sdr_reduce_bins_u8(src, len(bins), dst)
        return list(dst)

    def c_render(self, heights: list[int], fill: int = 0x5A) -> bytes:
        h = (ctypes.c_uint8 * COLUMNS)(*heights)
        chr_data = (ctypes.c_uint8 * CHR_BYTES)(*([fill] * CHR_BYTES))
        self.lib.nes_sdr_render_graph(h, chr_data)
        return bytes(chr_data)

    def test_reduce_matches_python_reference(self):
        fixtures = [
            bytes(range(256)),
            bytes(reversed(range(256))),
            bytes((i * 37 + 19) & 0xFF for i in range(512)),
            bytes((255 if 100 <= i < 150 else 12) for i in range(1024)),
            bytes((i ^ (i >> 3)) & 0xFF for i in range(2048)),
        ]
        for bins in fixtures:
            with self.subTest(n=len(bins)):
                self.assertEqual(self.c_reduce(bins), reduce_bins_u8(bins))

    def test_graph_matches_python_reference(self):
        fixtures = [
            [0] * COLUMNS,
            [HEIGHT] * COLUMNS,
            list(range(COLUMNS)),
            [min(HEIGHT, i * 3) for i in range(COLUMNS)],
            [((i * 17) ^ 23) % (HEIGHT + 1) for i in range(COLUMNS)],
        ]
        for heights in fixtures:
            with self.subTest(heights=heights):
                expected = bytearray([0x5A] * CHR_BYTES)
                render_graph(expected, heights)
                actual = self.c_render(heights)
                self.assertEqual(actual[:GRAPH_BYTES], bytes(expected[:GRAPH_BYTES]))
                self.assertEqual(actual[GRAPH_BYTES:], bytes([0x5A] * (CHR_BYTES - GRAPH_BYTES)))


if __name__ == "__main__":
    unittest.main()
