# NES-SDR

[![CI](https://github.com/Keitark/nes-sdr/actions/workflows/ci.yml/badge.svg)](https://github.com/Keitark/nes-sdr/actions/workflows/ci.yml)

**Use a Japanese Famicom as the display for an ESP32-S3 software-defined radio.**

NES-SDR targets the existing [FC ROM Vomitter](https://github.com/Keitark/fc-rom-vomitter) Rev A-FC hardware and is being designed around one rule:

> **No cartridge hardware modification for the main path.**

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
SPC1 spectrum bins
   |
   v
24 display columns
   |
   v
NES CHR tile renderer
   |
   v
existing ROM Vomitter LOAD/RUN bus ownership
   |
   v
Famicom PPU
   |
   v
CRT / TV
```

## Current architecture

[ESP-SDR](https://github.com/ESPARGOS/esp-sdr) already supports ESP32-S3 continuous on-chip FFT operation. NES-SDR therefore does **not** send raw I/Q through the Famicom bus.

Instead, the ESP32 reduces the spectrum to a tiny display frame and rewrites only the dynamic part of CHR SRAM.

```text
256..2048 FFT bins
        |
        v
24 spectrum columns
        |
        v
0..64 pixel bar height
        |
        v
192 dynamic NES tiles
        |
        v
3072 CHR bytes
```

The 6502 never performs an FFT and does not need to understand the SDR data format.

## Zero-mod live refresh trick

The important part is that live updates can plausibly work without modifying the Rev A-FC board.

After the NES-SDR ROM initializes the screen, it copies this loop into the 2A03's internal RAM:

```asm
$0200: JMP $0200
```

and executes there forever.

NMI and IRQ are disabled. From that point on, the CPU no longer needs cartridge PRG.

That means the ESP32 can use ROM Vomitter's existing safe LOAD topology at any time:

```text
PPU displaying spectrum
2A03 looping in internal RAM
        |
        v
ESP asserts LOAD
        |
        +-- PRG disconnected from console (CPU does not care)
        +-- CHR disconnected from PPU (brief visual disturbance)
        |
        v
rewrite + verify CHR[0x0000..0x0BFF]
        |
        v
return to RUN
        |
        v
PPU immediately displays new spectrum
```

No reset and no additional handshake wire are required by the design.

**Hardware validation is still pending.** The mechanism intentionally avoids timing luck between the 2A03 and ESP32, but repeated LOAD/RUN testing and scope measurements are still required before calling it robust.

See [docs/live-refresh.md](docs/live-refresh.md).

## Screen layout

![NES-SDR UI preview](docs/images/ui-preview.png)

The current UI reserves the first 192 CHR tiles for the graph and the remaining tiles for a fixed 5x7 instrument-style font.

```text
            NES-SDR

          RF SPECTRUM

       2.4 GHZ / ESP32-S3


        | |       ||
       || |       ||
     | || ||    | ||
   | | || || || | ||
   ||| ||||||||||||||
    LOW   CENTER   HIGH

       FFT SPAN / RX BW

       ESP-SDR + FAMICOM
```

The graph is:

- 24 columns;
- 64 pixels high;
- 6-pixel bars with a 2-pixel gap;
- 192 dynamic tiles = 3072 bytes.

The UI font lives after tile 192 and is not rewritten during a spectrum update.

## Repository layout

```text
docs/
  architecture.md
  hardware.md
  live-refresh.md
  roadmap.md
  snapshot-workflow.md
  first-hardware-test.md
  esp-idf-component.md

firmware/
  CMakeLists.txt
  include/nes_sdr_frame.h
  include/nes_sdr_spc1.h
  include/nes_sdr_live.h
  src/nes_sdr_frame.c
  src/nes_sdr_spc1.c
  src/nes_sdr_live.c

integration/
  fc-rom-vomitter/
    README.md
    0001-live-chr-refresh.patch
  esp-sdr/
    README.md
    0001-expose-last-spectrum.patch

nes/
  src/main.s
  nes.cfg
  Makefile

tools/
  font5x7.py
  render_mock.py
  render_preview.py

tests/
  test_render_mock.py
  test_renderer_parity.py
  test_spc1.c
  test_live.c

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

The ROM is mapper 0 / NROM and is intended to be loaded through the normal FC ROM Vomitter path.

## Generate the mock screen assets

```sh
python3 tools/render_mock.py \
  --out spectrum.chr \
  --nametable nametable.bin
```

This creates the same 8 KiB CHR image and 960-byte nametable used by the ROM build.

## ESP-SDR frame adapter

The firmware-side adapter understands ESP-SDR's `SPC1` frame layout:

```text
28-byte header
N spectrum bytes (256..2048)
4-byte CRC field
```

ESP-SDR supplies those bytes in natural FFT order (DC at bin 0). NES-SDR applies an FFT shift first so the display runs low frequency -> center/DC -> high frequency, then reduces the result to 24 columns and updates only the graph region of CHR.

The next major integration step is to route the ESP-SDR S3 spectrum producer directly into this adapter on the same ESP32-S3.

The initial live target is **5 Hz (200 ms/frame)**. The working budget is roughly 50 ms for RF capture/FFT and the remainder for CHR render, SRAM write/readback verify, and ownership-transition margin.

## Development path

```text
mock UI + CHR
    ->
NROM display
    ->
2A03 internal-RAM parking
    ->
host-tested SPC1 -> CHR
    ->
CHR-only ROM Vomitter refresh
    ->
real ESP-SDR spectrum producer
    ->
5 Hz live RF display on hardware
```

See [docs/roadmap.md](docs/roadmap.md).

## Credits

NES-SDR builds on:

- [FC ROM Vomitter](https://github.com/Keitark/fc-rom-vomitter)
- [ESP-SDR](https://github.com/ESPARGOS/esp-sdr)

No ESP-SDR source code is vendored here yet. The interface is kept explicit while the Famicom display and bus-ownership path are validated.
