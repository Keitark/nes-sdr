# Hardware integration

NES-SDR initially targets the released FC ROM Vomitter Rev A-FC hardware unchanged.

## Relevant existing blocks

- ESP32-S3-WROOM-1-N8
- U13 PRG SRAM: CY62128, 128K x 8
- U14 CHR SRAM: CY62128, 128K x 8
- console-side 74LVC245 bus buffers
- MCU-side 74LVC245 bus buffers
- 74HC595 address generation for MCU SRAM access
- LOAD/RUN ownership logic

Only 32 KiB of PRG and 8 KiB of CHR are needed by the initial NROM target.

## No-mod operating sequence

1. ESP32 keeps the cartridge in LOAD topology.
2. ESP32 captures RF and computes a spectrum.
3. NES-SDR renderer writes a complete 8 KiB CHR image.
4. Existing ROM Vomitter SRAM code writes and verifies PRG + CHR.
5. Existing logic exposes SRAM to the console.
6. User presses the Famicom RESET button.
7. The PPU displays the spectrum.

No electrical change is needed for this sequence.

## Power and RF note

ESP-SDR uses the ESP32-S3 radio while the same module is physically inside the cartridge assembly. The cartridge shell, Famicom chassis, TV/RF wiring, USB cable, and nearby digital buses can all affect the observed spectrum.

For early RF validation, compare:

- bare cartridge PCB;
- cartridge in shell;
- Famicom powered but PPU rendering disabled;
- Famicom actively displaying.

Treat visible self-noise as part of the experiment, not automatically as an SDR bug.

## Live-update boundary

Do not toggle LOAD_MODE while normal PRG code is executing.

The released design intentionally uses LOAD_MODE to protect against bus contention, and switching it removes cartridge PRG from the CPU. NES-SDR will not weaken that safety invariant merely to obtain animation.
