#!/usr/bin/env python3
"""Fail a combined build that silently keeps the weak RF backend."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


def find_nm() -> str:
    names = ("xtensa-esp32s3-elf-nm", "xtensa-esp32s3-elf-nm.exe")
    package_bin = (
        Path.home() / ".platformio" / "packages" / "toolchain-xtensa-esp-elf" / "bin"
    )
    for name in names:
        tool = package_bin / name
        if tool.is_file():
            return str(tool)
        found = shutil.which(name)
        if found:
            return found
    raise RuntimeError("ESP32-S3 nm tool was not found")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("elf", type=Path)
    args = parser.parse_args()
    output = subprocess.check_output([find_nm(), str(args.elf)], text=True)
    symbols: dict[str, str] = {}
    for line in output.splitlines():
        parts = line.split()
        if len(parts) == 3:
            symbols[parts[2]] = parts[1]
    expected = (
        "nes_sdr_rf_backend_available",
        "nes_sdr_rf_backend_capture",
        "esp_sdr_s3_local_spec",
    )
    wrong = {name: symbols.get(name) for name in expected if symbols.get(name) != "T"}
    if wrong:
        raise SystemExit(f"strong RF backend missing from final ELF: {wrong}")
    print("strong NES-SDR/ESP-SDR RF backend linked")


if __name__ == "__main__":
    main()
