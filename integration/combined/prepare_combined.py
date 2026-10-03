#!/usr/bin/env python3
"""Prepare a temporary FC ROM Vomitter + NES-SDR + ESP-SDR combined build.

This script is intended for CI workspaces only. It copies transformed GPL
ESP-SDR sources into a temporary FC ROM Vomitter checkout; it does not vendor
those sources into either project's release tree.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


SDKCONFIG_APPEND = r"""
# ---- NES-SDR / ESP-SDR combined-build profile ----
CONFIG_ESP_PHY_ENABLE_CERT_TEST=y
CONFIG_ESP_PHY_DEBUG=y
CONFIG_FREERTOS_HZ=1000
CONFIG_COMPILER_OPTIMIZATION_PERF=y
CONFIG_ESP_DEFAULT_CPU_FREQ_MHZ_240=y
# CONFIG_PM_ENABLE is not set
# CONFIG_ESP_WIFI_IRAM_OPT is not set
# CONFIG_ESP_WIFI_EXTRA_IRAM_OPT is not set
# CONFIG_ESP_WIFI_RX_IRAM_OPT is not set
# CONFIG_ESP_WIFI_SLP_IRAM_OPT is not set
# CONFIG_ESP_PHY_IRAM_OPT is not set
# CONFIG_ESP_WIFI_AMPDU_TX_ENABLED is not set
# CONFIG_ESP_WIFI_AMPDU_RX_ENABLED is not set
CONFIG_FREERTOS_UNICORE=y
# CONFIG_ESP_INT_WDT is not set
# CONFIG_ESP_TASK_WDT_EN is not set
CONFIG_ESP_WIFI_STATIC_RX_BUFFER_NUM=4
CONFIG_ESP_SDR_UART_BAUD=2000000
"""


def copytree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, symlinks=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--nes-sdr", type=Path, required=True)
    parser.add_argument("--fc-rom-vomitter", type=Path, required=True)
    parser.add_argument("--esp-sdr", type=Path, required=True)
    args = parser.parse_args()

    nes = args.nes_sdr.resolve()
    fc = args.fc_rom_vomitter.resolve()
    esp = args.esp_sdr.resolve()

    firmware = fc / "firmware"
    components = firmware / "components"
    components.mkdir(parents=True, exist_ok=True)

    # Transformed ESP-SDR main component.
    copytree(esp / "main", components / "esp_sdr_rf")

    # ESP-SDR's pinned ESP-DSP dependency.
    esp_dsp = esp / "components" / "esp-dsp"
    if not esp_dsp.exists():
        raise RuntimeError(
            "ESP-SDR esp-dsp component missing; clone ESP-SDR with submodules"
        )
    copytree(esp_dsp, components / "esp-dsp")

    # Small strong-symbol adapter from NES-SDR -> embedded ESP-SDR.
    copytree(
        nes / "integration" / "esp-sdr" / "backend",
        components / "nes_sdr_esp_sdr_backend",
    )

    # Make the copied ESP-SDR component omit its standalone app_main().
    project_cmake = firmware / "CMakeLists.txt"
    cmake_text = project_cmake.read_text()
    needle = "include($ENV{IDF_PATH}/tools/cmake/project.cmake)\n"
    if cmake_text.count(needle) != 1:
        raise RuntimeError("unexpected FC ROM Vomitter firmware/CMakeLists.txt")
    cmake_text = cmake_text.replace(
        needle,
        "set(ESP_SDR_EMBEDDED ON CACHE BOOL "
        "\"Embed ESP-SDR into ROM Vomitter\" FORCE)\n" + needle,
        1,
    )
    project_cmake.write_text(cmake_text)

    defaults = firmware / "sdkconfig.defaults"
    text = defaults.read_text()
    if "NES-SDR / ESP-SDR combined-build profile" in text:
        raise RuntimeError("combined sdkconfig profile already present")
    defaults.write_text(text.rstrip() + "\n" + SDKCONFIG_APPEND.lstrip())

    print("prepared combined FC ROM Vomitter + NES-SDR + ESP-SDR build")


if __name__ == "__main__":
    main()
