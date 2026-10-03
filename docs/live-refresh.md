# Zero-mod live refresh

## Core idea

After the NES-SDR ROM has initialized the PPU, the 2A03 no longer needs the cartridge PRG ROM.

The ROM copies this three-byte loop into internal CPU RAM at `$0200`:

```asm
$0200: JMP $0200
```

It then jumps to `$0200` permanently.

NMI is disabled and IRQs are masked, so normal execution no longer fetches code or vectors from cartridge PRG.

That changes the live-update problem substantially.

## Refresh sequence

```text
Famicom display is running
2A03 executes forever from internal RAM $0200
PPU continuously reads CHR
        |
        | ESP32 wants a new frame
        v
ROM Vomitter enters existing safe LOAD topology
        |
        +-- console PRG path isolated
        |      (safe: CPU is not reading PRG)
        |
        +-- console CHR path isolated
               (display may glitch briefly)
        |
        v
ESP32 rewrites only dynamic CHR graph bytes
        |
        v
optional graph-region readback/verify
        |
        v
ROM Vomitter returns to RUN topology
        |
        v
PPU immediately sees the new CHR
        |
        v
2A03 never left $0200
```

No extra wire and no CPU/ESP handshake are needed because the CPU is *always* in the safe state after initialization.

## Why interrupts matter

The trick only works if the CPU never unexpectedly fetches an interrupt vector from cartridge PRG while LOAD is active.

The NES-SDR ROM therefore:

- executes `SEI`;
- inhibits the APU frame IRQ;
- leaves PPU NMI disabled;
- uses no mapper IRQ;
- uses no sprites or CPU-side animation after initialization.

The PPU itself keeps rendering while the CPU waits in internal RAM.

## What happens visually during LOAD?

The released ROM Vomitter intentionally disconnects the console side from CHR SRAM while the MCU owns it. Therefore the PPU cannot fetch valid pattern data during the update window.

A brief visual disturbance is expected.

Once RUN is restored, the PPU resumes normal CHR reads without a reset because:

- the nametable remains in the Famicom's CIRAM;
- palette RAM remains inside the PPU;
- scroll/control registers remain configured;
- only CHR pattern data changed.

The target is to make the ownership window short enough that this looks like a brief refresh rather than a reset.

## Update size

The redesigned UI uses:

- 24 graph columns;
- 8 tile rows;
- 192 dynamic graph tiles;
- 16 bytes per tile.

So a live frame needs only:

```text
24 x 8 x 16 = 3072 bytes
```

The remaining CHR tiles contain the fixed UI font and are not rewritten.

This is materially faster than rewriting all 8 KiB of CHR and much faster than reloading PRG.

## First implementation target

Add a ROM Vomitter-side function equivalent to:

```c
enter_load_topology();
write_chr_range(0, graph_chr, 3072);
verify_chr_range(0, graph_chr, 3072);
expose_run_topology();
```

The existing ownership logic should be reused unchanged.

## Safety boundary

This is still a hardware experiment until measured on the actual board.

Before calling it reliable:

1. verify CPU execution remains in internal RAM across repeated LOAD/RUN cycles;
2. scope LOAD_MODE, RUN, CHR OE/WE, and one PPU-side data line;
3. confirm there is no overlap between console and MCU drivers;
4. run thousands of refresh cycles;
5. test with Wi-Fi/RF activity active on the ESP32-S3;
6. verify the PPU always recovers without RESET.

The important distinction is that this scheme does **not** depend on timing luck between the ESP32 and 2A03. The CPU is deliberately parked in a state where cartridge PRG is unnecessary.
