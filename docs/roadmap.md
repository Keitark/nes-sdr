# Roadmap

## Stage 0 — repository skeleton

- [x] NROM/mapper-0 target
- [x] host-side synthetic spectrum generator
- [x] hardware-independent C CHR renderer
- [x] CI for renderer and ROM build
- [x] document zero-mod hardware boundary

## Stage 1 — display validation

- [ ] build `nes/build/nes-sdr.nes` in CI
- [ ] load it through FC ROM Vomitter
- [ ] confirm the graph geometry on real Famicom hardware
- [ ] capture CRT / HDMI-upscaler screenshots
- [ ] tune palette, margins, and bar geometry

Success criterion: a synthetic spectrum generated on the host appears correctly on the Famicom without hardware changes.

## Stage 2 — renderer parity

- [ ] add native C unit tests
- [ ] verify Python and C renderers produce identical CHR bytes
- [ ] add recorded FFT fixtures
- [ ] add max-hold and optional temporal smoothing
- [ ] define an explicit magnitude mapping contract

Success criterion: the same FFT fixture always produces a bit-identical CHR image on host and ESP32.

## Stage 3 — ESP-SDR adapter

- [ ] build against an ESP32-S3 ESP-SDR-compatible spectrum source
- [ ] consume 256+ FFT bins on-device
- [ ] reduce to 31 display columns
- [ ] render CHR entirely on the ESP32-S3
- [ ] expose capture frequency / bandwidth in logs

Success criterion: real RF activity produces a valid 8 KiB CHR snapshot without using a PC for DSP.

## Stage 4 — ROM Vomitter snapshot integration

- [ ] combine fixed NES-SDR PRG with generated CHR
- [ ] reuse the existing SRAM write/verify path
- [ ] preserve ROM Vomitter bus-safety invariants
- [ ] provide a one-command or one-button snapshot workflow
- [ ] measure capture-to-ready latency

Success criterion: power/upload/capture/RESET produces a real RF spectrum on the Famicom with an unmodified Rev A-FC board.

## Stage 5 — zero-mod live-refresh research

No live-refresh method is accepted merely because it "usually works."

Candidates:

1. **2A03 internal-RAM rendezvous**
   - execute a tiny loop entirely from $0000-$07FF;
   - make cartridge PRG unnecessary during the update window;
   - solve ESP32/Famicom synchronization without adding a wire.

2. **Deterministic timed takeover**
   - investigate only if a repeatable synchronization source exists;
   - reject if drift can cause PRG removal during cartridge execution.

3. **PPU-assisted CHR write experiments**
   - investigate whether existing signals can safely update CHR without full ownership transfer;
   - reject if it relies on marginal bus contention or undocumented timing luck.

Success criterion: repeated long-run testing shows no bus contention, crashes, or corrupted SRAM and the mechanism has a clear timing argument.

Until then, live refresh is experimental and snapshot mode is the supported zero-mod design.

## Later ideas

- waterfall snapshots;
- peak-hold trace;
- Wi-Fi channel markers;
- controller-selected center frequency;
- AM/FM-style demodulation experiments where the ESP32 produces a compact visualization or audio representation;
- alternate retro front ends while keeping the same renderer contract.
