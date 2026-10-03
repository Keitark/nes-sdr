# NES-SDR

Turn a Japanese Famicom into a live RF spectrum display using the ESP32-S3 already present on the [FC ROM Vomitter](https://github.com/Keitark/fc-rom-vomitter).

The project combines three ideas:

1. **ESP-SDR-style RF capture on the ESP32-S3** — on-chip FFTs reduce the RF stream to compact spectrum data.
2. **CHR SRAM as a display framebuffer** — spectrum bars are converted directly into NES/Famicom pattern-table tiles.
3. **A tiny NROM program on the Famicom** — the 2A03 and PPU only handle display setup and UI; they do not process raw I/Q.

The first target is deliberately modest: **a 1 Hz spectrum display**. That is enough to prove the end-to-end path before attempting faster refresh or demodulation.

> Status: early PoC. The software layout and CHR renderer are being built first. Live CHR SRAM ownership while the console is running still needs a safe bus-arbitration solution.

## Why this architecture?

The ESP32-S3 is already supported by ESP-SDR's continuous on-chip spectrum mode, so the NES does not need to ingest raw I/Q.

```text
2.4 GHz RF
   |
   v
ESP32-S3 RF receiver
   |
   v
on-chip FFT
   |
   v
256+ FFT bins
   |
   v
collapse / smooth / scale
   |
   v
31 display columns, 0..64 pixels
   |
   v
CHR tile encoder
   |
   v
FC ROM Vomitter CHR SRAM
   |
   v
Famicom PPU -> TV
```

The Famicom sees ordinary CHR graphics. The spectrum can therefore be redrawn without asking the 6502 to perform FFTs, move large sample buffers, or even understand the RF data format.

## Display format

The initial ROM reserves an 8-tile-high by 31-tile-wide region:

- 31 spectrum columns
- 64 vertical pixels per column
- 248 unique CHR tiles
- tile 248 is reserved as a blank background tile
- tiles 249-255 are reserved for future UI glyphs

A complete graph image occupies **248 x 16 = 3968 bytes** of CHR pattern data.

The ESP32 renderer accepts 31 normalized bar heights and produces those 3968 bytes directly.

## Repository layout

```text
docs/
  architecture.md       end-to-end design
  hardware.md           FC ROM Vomitter integration and live-update constraints
  roadmap.md            staged implementation plan

firmware/
  include/nes_sdr_frame.h
  src/nes_sdr_frame.c   FFT-bin collapse and CHR tile renderer
  README.md             ESP-SDR integration notes

nes/
  src/main.s            minimal NROM display program
  nes.cfg               ca65/ld65 memory map
  Makefile

tools/
  render_mock.py        host-side preview/reference implementation

tests/
  test_render_mock.py   renderer behavior tests
```

## Build the Famicom ROM

Install [cc65](https://cc65.github.io/cc65/) and run:

```sh
make -C nes
```

The result is:

```text
nes/build/nes-sdr.nes
```

It is a mapper-0 / NROM image intended to be loaded by FC ROM Vomitter.

## Render a mock spectrum

```sh
python tools/render_mock.py --out /tmp/nes-sdr.chr
```

This writes an 8 KiB CHR image containing a synthetic spectrum in the same layout used by the firmware-side renderer.

## Hardware strategy

The existing FC ROM Vomitter already has:

- ESP32-S3-WROOM-1-N8
- PRG SRAM
- CHR SRAM
- separate console-side and MCU-side bus buffers
- LOAD/RUN ownership logic

That is almost exactly what NES-SDR needs.

The remaining issue is **live CHR updates**. In the current Rev A-FC design, LOAD/RUN ownership switches PRG and CHR together. During RUN the MCU-side CHR address buffers are disabled; during LOAD the Famicom loses PRG as well as CHR.

The PoC therefore separates two milestones:

### Snapshot mode

No board changes are required. Generate a CHR frame, load PRG+CHR SRAM through the existing ROM Vomitter path, then run the console. This validates the RF-to-NES graphics pipeline.

### Live mode

Keep PRG continuously available to the Famicom while allowing the ESP32 to temporarily own only the CHR SRAM. The exact implementation is documented in [docs/hardware.md](docs/hardware.md).

The target refresh rate is initially only 1 Hz, so the design favors simple, safe arbitration over maximum bandwidth.

## ESP-SDR relationship

NES-SDR is designed to consume the same kind of on-device spectrum information produced by [ESPARGOS/esp-sdr](https://github.com/ESPARGOS/esp-sdr).

ESP-SDR currently supports ESP32-S3 continuous on-chip FFT operation with selectable FFT sizes and 16/40/80 MS/s sample-rate modes. NES-SDR does not need to stream those FFT bins over USB: the intended integration is to feed them directly into the CHR renderer on the same ESP32-S3.

No ESP-SDR source is vendored here yet. That keeps the first commits focused on the Famicom display pipeline and makes the integration boundary explicit.

## Short-term goal

A useful first demo is:

```text
Power on Famicom
      |
      v
NES-SDR ROM starts
      |
      v
ESP32-S3 measures 2.4 GHz spectrum
      |
      v
new graph generated once per second
      |
      v
CHR SRAM updated
      |
      v
spectrum moves on a CRT
```

That is the whole joke — and also a surprisingly sensible split of work between a 1983 console and a modern Wi-Fi SoC.
