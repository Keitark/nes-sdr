# Roadmap

## Stage 0 — project skeleton

- [x] mapper-0 / NROM display target
- [x] synthetic spectrum generator
- [x] compact 5x7 UI font
- [x] fixed nametable UI
- [x] hardware-independent C CHR renderer
- [x] ESP-SDR SPC1 parser / adapter
- [x] CI for Python, C, and ROM build
- [x] document zero-mod hardware boundary

## Stage 1 — zero-mod display ROM

- [x] reserve 192 CHR tiles for the dynamic graph
- [x] reserve the remaining CHR tiles for fixed UI/font
- [x] generate 24-column, 64-pixel graph assets
- [x] park the 2A03 in internal RAM after initialization
- [x] disable NMI/IRQ dependencies after initialization
- [ ] build and boot the ROM on a real Famicom
- [ ] inspect the screen on CRT / capture hardware
- [ ] tune palette, spacing, and labels

Success criterion: the screen remains stable while the CPU executes only from internal RAM.

## Stage 2 — CHR-only live refresh

- [x] define a 3072-byte dynamic CHR region
- [x] create reference ROM Vomitter firmware patch
- [ ] apply the CHR-only refresh API to an integration branch
- [ ] feed synthetic frames through repeated LOAD/RUN cycles
- [ ] confirm the PPU recovers without RESET
- [ ] run at least 10,000 refresh cycles
- [ ] scope LOAD_MODE, RUN, CHR OE/WE, and a PPU-side data line

Success criterion: repeated CHR refreshes produce no bus contention, CPU crash, or persistent PPU corruption.

## Stage 3 — renderer parity

- [x] Python reference renderer
- [x] C graph renderer
- [x] SPC1 frame parser
- [x] static-UI preservation test
- [ ] add C/Python byte-for-byte fixture parity
- [ ] add recorded ESP-SDR spectrum fixtures
- [ ] add optional smoothing
- [ ] add optional peak hold
- [ ] define magnitude floor/ceiling mapping

Success criterion: a recorded spectrum fixture produces a deterministic graph image across host and ESP32 builds.

## Stage 4 — ESP-SDR integration

- [ ] identify the cleanest ESP32-S3 spectrum-frame hook
- [ ] expose one on-device spectrum frame without USB serialization
- [ ] feed its bins directly to `nes_sdr_spc1_to_chr` or a lower-level bin adapter
- [ ] invoke the ROM Vomitter CHR-only refresh operation
- [ ] add a 1 Hz scheduler
- [ ] keep Wi-Fi / RF capture and SRAM ownership transitions mutually safe

Success criterion: one ESP32-S3 performs RF capture, FFT, graph rendering, and CHR refresh without a PC in the data path.

## Stage 5 — real RF demo

- [ ] 2.4 GHz ISM-band spectrum display
- [ ] center-frequency / bandwidth logging
- [ ] compare displayed peaks against the ESP-SDR browser viewer
- [ ] characterize self-noise from Famicom, PPU, SRAM bus, USB, and cartridge enclosure
- [ ] record a repeatable demo sequence

Success criterion: visible RF activity on the Famicom corresponds to independently observed RF activity.

## Stage 6 — interaction and polish

Candidates that still preserve the no-mod hardware goal:

- web UI for center frequency / bandwidth / gain;
- ESP BOOT button for capture/pause;
- automatic 1 Hz refresh;
- peak-hold trace;
- waterfall-style stepped history;
- Wi-Fi channel markers;
- a more polished instrument face and boot screen.

## Codex handoff point

A Codex checkout becomes especially useful at **Stage 4**, when the work changes from self-contained files to a real multi-repository ESP-IDF integration:

- FC ROM Vomitter firmware;
- ESP-SDR S3 capture/FFT internals;
- NES-SDR renderer;
- build-system and linker constraints;
- hardware-in-the-loop debugging.

Before that point, most work can stay as small, reviewable changes in this repository.
