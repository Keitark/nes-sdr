# ESP32 firmware modules

The `firmware/` directory contains hardware-independent pieces intended to be
compiled into the eventual ESP32-S3 integration build.

## Modules

### `nes_sdr_frame`

Converts unsigned 8-bit spectrum bins into the dynamic NES graph region.

Current display contract:

```text
input:  arbitrary bin count, normally 256
output: 24 bar heights
        24 x 8 NES tiles
        3072 bytes
```

The graph renderer writes only the dynamic region. Static font/UI tiles are not
touched.

### `nes_sdr_spc1`

Parses the ESP-SDR `SPC1` wire-frame layout and exposes:

```c
nes_sdr_spc1_parse(...)
nes_sdr_spc1_to_graph(...)
```

The intended same-device integration can use the same frame format internally
without sending it over USB.

### `nes_sdr_live`

Small allocation-free orchestration layer:

```text
capture callback
    |
    v
SPC1 parse
    |
    v
graph render
    |
    v
refresh callback
```

Only two platform-specific callbacks are required:

```c
bool capture(void *ctx, const uint8_t **frame, size_t *length);
int refresh(void *ctx, const uint8_t *graph, size_t length);
```

For the final ESP32-S3 build:

- `capture` will wrap a short ESP-SDR S3 spectrum run;
- `refresh` will call the FC ROM Vomitter CHR-only LOAD/write/verify/RUN path.

That keeps RF internals, display rendering, and cartridge-bus ownership
separate and individually testable.

## Recommended first live profile

```text
ESP-SDR rate code: 6 (16 MS/s)
FFT size:          256
graph columns:     24
refresh period:    ~1 s
dynamic CHR:       3072 bytes
```

See:

- `integration/esp-sdr/`
- `integration/fc-rom-vomitter/`
- `docs/live-refresh.md`
