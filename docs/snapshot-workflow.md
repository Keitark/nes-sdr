# Zero-mod snapshot fallback

NES-SDR's primary architecture is now the no-reset live-refresh design described
in [live-refresh.md](live-refresh.md).

This document keeps the simpler **capture -> rewrite -> RESET** flow as a
bring-up fallback.

## Why keep a fallback mode?

Before relying on permanent 2A03 internal-RAM parking, it is useful to prove the
RF-to-CHR path independently.

FC ROM Vomitter already knows how to:

- isolate the Famicom from both SRAM buses;
- let the ESP32 write and verify SRAM;
- return the SRAMs to the console.

So the fallback flow is:

```text
capture RF
   |
   v
FFT -> SPC1 -> graph CHR
   |
   v
rewrite normal NROM image / SRAM
   |
   v
restore RUN
   |
   v
press Famicom RESET
   |
   v
display new snapshot
```

This mode is slower and interactive, but it is extremely useful while debugging
the first RF integration because it does not depend on live ownership cycling.

## When to use it

Use snapshot fallback when:

- validating the first real ESP-SDR spectrum;
- checking the graph renderer;
- debugging SRAM contents;
- verifying frequency-axis orientation;
- diagnosing a live-refresh failure.

Once the internal-RAM parking and CHR-only refresh tests pass, live mode should
be the normal path.

## Important difference from live mode

Snapshot fallback may rewrite both PRG and CHR and expects a user RESET
afterward.

Live mode writes only the 3072-byte graph region of CHR and should not require
RESET.
