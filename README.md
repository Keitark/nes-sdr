# NES-SDR

**Use a Japanese Famicom as the display for an ESP32-S3 software-defined radio.**

NES-SDR targets the existing [FC ROM Vomitter](https://github.com/Keitark/fc-rom-vomitter) Rev A-FC hardware and, for the first working version, requires **no cartridge hardware modification**.

The ESP32-S3 does the RF work. The Famicom does the gloriously inappropriate 1983 graphics work.

```text
2.4 GHz RF
   |
   v
ESP32-S3 RF capture
   |
   v
on-chip FFT
   |
   v
bin reduction
   |
   v
NES CHR tile renderer
   |
   v
existing ROM Vomitter SRAM LOAD path
   |
   v
Famicom PPU
   |
   v
CRT / TV
```

## First target: snapshot spectrum analyzer

The initial target is intentionally simple and safe:

1. capture RF on the ESP32-S3;
2. compute a spectrum;
3. convert it into NES CHR tiles;
4. load the NROM PRG + generated CHR through ROM Vomitter's existing SRAM loader;
5. expose the SRAM to the Famicom;
6. press RESET;
7. display the spectrum.

No lifted pins, bodge wires, extra latches, or rewired SRAM signals.

This gives us a complete RF-to-Famicom pipeline before trying any clever runtime tricks.

## Why the ESP32-S3 is enough

[ESP-SDR](https://github.com/ESPARGOS/esp-sdr) supports the ESP32-S3 with continuous on-chip FFT operation. NES-SDR does **not** need to push raw I/Q through the Famicom bus.

Instead:

```text
256..2048 FFT bins
        |
        v
31 display columns
        |
        v
0..64 pixel bar height
        |
        v
248 unique NES tiles
```

A complete graph occupies only 3968 bytes of CHR pattern data.

The 6502 never performs an FFT and does not need to understand the SDR data format.

## Current display format

The NROM program reserves an 8-tile-high × 31-tile-wide graph:

- 31 spectrum columns;
- 64 vertical pixels;
- 6-pixel-wide bars with a 2-pixel gap;
- tiles 0-247: graph;
- tile 248: blank;
- tiles 249-255: reserved.

The nametable is static. Changing the spectrum means generating different CHR bytes.

## Repository layout

```text
docs/
  architecture.md       zero-mod architecture and live-update boundary
  hardware.md           ROM Vomitter hardware integration
  roadmap.md            staged implementation plan

firmware/
  include/nes_sdr_frame.h
  src/nes_sdr_frame.c   FFT-bin reduction + CHR renderer
  README.md

nes/
  src/main.s            minimal mapper-0 spectrum display
  nes.cfg
  Makefile

tools/
  render_mock.py        reference/synthetic CHR generator

tests/
  test_render_mock.py

.github/workflows/
  ci.yml
```

## Build the Famicom ROM

Install cc65, then:

```sh
make -C nes
```

Output:

```text
nes/build/nes-sdr.nes
```

The ROM is 32 KiB PRG + 8 KiB CHR, mapper 0 / NROM, ready for the normal FC ROM Vomitter upload path.

## Generate a mock spectrum

```sh
python3 tools/render_mock.py --out spectrum.chr
```

This creates an 8 KiB CHR image using exactly the same tile layout expected by the Famicom ROM.

## About live 1 Hz updates

**Zero-mod live refresh is a research item, not something this project pretends already works.**

On the released ROM Vomitter board, LOAD/RUN ownership switches PRG and CHR together. While the ESP32 owns SRAM, the Famicom temporarily loses PRG. There is also no stock-board runtime handshake from the 2A03 back to the ESP32.

So the project will first make snapshot mode solid.

Software-only ideas such as executing a rendezvous loop from the 2A03's internal RAM are documented in [docs/architecture.md](docs/architecture.md), but blind bus takeover is deliberately not used.

If a safe zero-mod live scheme can be demonstrated, it becomes the next mode. If not, snapshot mode remains the baseline instead of quietly requiring a hardware bodge.

## Development stages

See [docs/roadmap.md](docs/roadmap.md), but the short version is:

```text
mock CHR
   -> NROM display
   -> host-tested C renderer
   -> ESP-SDR FFT adapter
   -> real RF snapshot
   -> ROM Vomitter integration
   -> investigate zero-mod live refresh
```

## Credits

NES-SDR builds on the ideas and hardware of:

- [FC ROM Vomitter](https://github.com/Keitark/fc-rom-vomitter)
- [ESP-SDR](https://github.com/ESPARGOS/esp-sdr)

No ESP-SDR source code is vendored in the repository at this stage. The integration boundary is intentionally kept small while the Famicom display path is developed.
