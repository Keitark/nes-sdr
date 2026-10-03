# Hardware integration

NES-SDR targets the released FC ROM Vomitter Rev A-FC hardware unchanged.

## Existing blocks used

- ESP32-S3-WROOM-1-N8
- U13 PRG SRAM: CY62128, 128K x 8
- U14 CHR SRAM: CY62128, 128K x 8
- console-side 74LVC245 bus buffers
- MCU-side 74LVC245 bus buffers
- 74HC595 MCU address generation
- LOAD/RUN ownership logic
- existing SRAM write/readback firmware path

No additional latch or bus transceiver is required by the current design.

## Why shared LOAD_MODE is acceptable

Rev A-FC switches PRG and CHR ownership together.

At first this looks unsuitable for live graphics because asserting LOAD removes PRG from the CPU.

NES-SDR avoids that problem in software: after initialization the 2A03 executes permanently from internal RAM.

Therefore, during a live refresh:

- loss of PRG access is harmless;
- loss of CHR access is temporary and visible;
- ESP32 gets exclusive SRAM ownership exactly as the board was designed to provide.

We keep the original electrical safety model instead of bypassing it.

## CHR memory layout

Only the first 3 KiB changes every frame.

| CHR range | Purpose |
|---|---|
| `$0000-$0BFF` | 192 dynamic graph tiles |
| `$0C00-$0C0F` | blank tile 192 |
| `$0C10...` | 5x7 UI glyph tiles |
| remainder | reserved |

The live writer should therefore refresh only `0x0000..0x0BFF`.

## Proposed firmware transaction

```c
sram_bus_hold_isolated();
write_chr_range(0, frame, 3072);
verify_chr_range(0, frame, 3072);
sram_bus_expose_to_console(mirroring);
```

The reference firmware patch lives under:

```text
integration/fc-rom-vomitter/
```

## RF/self-noise note

ESP-SDR uses the same ESP32-S3 physically mounted in the cartridge.

The following can affect the measured spectrum:

- Famicom clock harmonics;
- PPU activity;
- SRAM/address switching;
- ESP32 digital activity;
- USB cable/common-mode radiation;
- cartridge shell and shielding;
- TV/RF modulator wiring.

That is part of the experiment.

For validation, compare at least:

1. bare cartridge powered from USB;
2. cartridge inserted, console powered;
3. PPU rendering enabled;
4. repeated LOAD/RUN CHR updates;
5. different physical antenna positions.

A visible line that follows console state may be self-noise rather than an external RF source.

## Measurements to capture on first hardware run

Recommended scope/logic-analyzer probes:

- LOAD_MODE
- RUN
- PRG_WE_n
- CHR_WE_n
- CHR_OE_n
- one PPU-side CHR data bit
- optionally one MCU data bit

The key check is that console-facing and MCU-facing drivers are never active against each other during ownership transitions.
