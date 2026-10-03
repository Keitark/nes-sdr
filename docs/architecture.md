# Architecture

## Design rule: Rev A-FC stays unmodified

NES-SDR targets a stock FC ROM Vomitter Rev A-FC board.

No lifted pins, bodge wires, extra latches, or rewired SRAM signals are required for the primary path.

```text
ESP32-S3                          Famicom
---------                         -------
RF capture                        PPU renders UI
FFT                               2A03 parks in RAM
bin reduction
CHR tile generation
    |
    | existing LOAD/RUN ownership
    v
PRG SRAM + CHR SRAM  ---------->  cartridge buses
```

The ESP32 does RF/DSP work. The Famicom supplies the PPU, video timing, palette, nametable RAM, and the display hardware.

## Existing ROM Vomitter behavior we reuse

Rev A-FC already supports:

1. isolating the console from PRG/CHR SRAM;
2. giving the ESP32 address/data ownership;
3. writing SRAM;
4. readback verification;
5. returning ownership to the console.

The electrical ownership mechanism does not need to be redesigned.

## Boot phase

At boot, the normal NROM image runs from PRG SRAM.

It initializes:

- palette RAM;
- the fixed nametable UI;
- background rendering;
- the initial CHR image.

It then disables all expected interrupt sources and copies a tiny loop into internal 2A03 RAM at `$0200`.

```asm
$0200: JMP $0200
```

Execution jumps there permanently.

## Steady-state phase

Once parked in internal RAM, the 2A03 makes no cartridge PRG reads.

This removes the synchronization problem that a conventional game would have: the CPU is always safe for cartridge PRG to disappear.

The PPU keeps rendering independently.

## Live frame refresh

The ESP32 can now perform:

```text
RUN
 |
 | 2A03 already parked in internal RAM
 v
assert LOAD
 |
 +--> console PRG buffers disabled
 |      CPU unaffected
 |
 +--> console CHR buffers disabled
        PPU may show a brief transient
 |
 v
write dynamic CHR region
 |
 v
verify dynamic CHR region
 |
 v
return to RUN
 |
 v
PPU reads the new pattern data
```

No CPU-to-ESP handshake is required.

## Dynamic versus static CHR

The screen is deliberately partitioned.

```text
CHR $0000-$0BFF   3072 bytes   dynamic spectrum graph
CHR $0C00-$0FFF   UI/font area in pattern table 0
CHR $1000-$1FFF   reserved for future use
```

The graph uses:

- 24 columns;
- 8 tile rows;
- 192 tiles;
- 16 bytes per tile.

Only the first 3072 bytes need to change each frame.

The static font and UI graphics remain untouched.

## Interrupt invariants

The RAM-parking technique depends on the CPU not fetching vectors from cartridge PRG while LOAD is active.

The ROM therefore:

- executes `SEI`;
- disables PPU NMI;
- inhibits the APU frame IRQ;
- does not use mapper IRQs;
- performs no CPU-side animation after setup.

A user-initiated console RESET during the short LOAD interval is outside the intended operating sequence because reset vector fetches need PRG to be visible.

## Expected visual artifact

The PPU cannot access CHR SRAM while the ESP32 owns it.

So the image may briefly glitch during each refresh.

That is a display-quality issue, not a bus-contention mechanism. Once RUN returns, the existing nametable, palette, scroll, and PPU state remain valid and normal pattern fetching resumes.

Reducing the ownership window is therefore useful.

## Performance target

The initial target is 1 Hz.

With the current ROM Vomitter bit-banged SRAM address path, updating and verifying 3072 bytes is expected to be visibly non-instantaneous but still practical for a proof of concept.

Future optimizations can include:

- faster address shifting;
- writing only changed tiles;
- optional verify policies after the basic mechanism is proven;
- lower refresh rates when the spectrum is unchanged.

None of these are required to establish the architecture.

## Validation gate

The live mechanism remains experimental until measured on hardware.

Required evidence:

1. stable internal-RAM CPU execution;
2. no console/MCU driver overlap;
3. scope capture of LOAD_MODE / RUN / CHR OE / CHR WE;
4. repeated refresh cycling;
5. PPU recovery after every cycle;
6. operation while ESP-SDR and Wi-Fi/RF activity are active.

The important property is that the scheme does not depend on phase alignment or timing luck between the ESP32 and 2A03.
