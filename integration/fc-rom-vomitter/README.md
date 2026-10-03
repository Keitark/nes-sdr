# FC ROM Vomitter integration

NES-SDR is intentionally developed in its own repository first.

The target hardware is the existing `Keitark/fc-rom-vomitter` Rev A-FC board with **no hardware rework**.

## Minimal firmware change required

The ROM Vomitter firmware already has all of the electrical ownership machinery needed for live NES-SDR updates. What it lacks is a public operation that refreshes only part of CHR SRAM while leaving PRG contents untouched.

NES-SDR's dynamic graph occupies exactly:

```text
24 columns x 8 tile rows x 16 bytes = 3072 bytes
```

and starts at CHR address 0.

The fixed UI/font begins at CHR address `0x0C00` and is preserved across live updates.

The desired transaction is:

```text
controller lock
    |
    v
sram_bus_hold_isolated()
    |
    v
write CHR[0x0000..0x0BFF]
    |
    v
readback / verify same range
    |
    v
sram_bus_expose_to_console()
    |
    v
controller unlock
```

PRG SRAM is never rewritten during a live frame.

## Why the CPU survives

The NES-SDR ROM finishes initialization by copying `JMP $0200` into internal 2A03 RAM and executing there forever.

Therefore the CPU does not need cartridge PRG while the ESP32 owns the SRAM buses.

See [../../docs/live-refresh.md](../../docs/live-refresh.md).

## Proposed API

```c
esp_err_t controller_refresh_chr(const uint8_t *data, size_t length);
```

The controller should enforce:

- a valid installed NROM image;
- `length == 3072` for the NES-SDR fast path;
- the existing controller mutex;
- existing LOAD/RUN safety rules;
- CHR readback before returning to RUN.

## Integration order

1. Validate the NES ROM and static UI through the unmodified ROM Vomitter upload flow.
2. Add the CHR-only refresh API.
3. Feed synthetic graph frames through it.
4. Run repeated LOAD/RUN cycling on hardware.
5. Only after that, connect the ESP-SDR spectrum producer.

The reference patch beside this document is the original CHR-only sketch.
The integrated bench profile adds a controller lock across RF capture,
manual `RVLA` arming, a ROM marker check, and synthetic/RF build profiles in
the ROM Vomitter firmware. Use that implementation for Issue #1; the sketch
alone does not meet its safety and integration criteria.
