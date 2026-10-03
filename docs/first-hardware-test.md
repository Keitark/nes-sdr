# First hardware test plan

This plan keeps the cartridge hardware unchanged and separates display validation
from RF integration.

## A. Static ROM / UI validation

Goal: prove the Famicom-side ROM and CHR layout first.

1. Download the latest `nes-sdr-rom` artifact from GitHub Actions, or build:
   `make -C nes`.
2. Upload `nes/build/nes-sdr.nes` through the normal FC ROM Vomitter flow.
3. Wait for the normal ROM Vomitter READY indication.
4. Press the Famicom RESET button once.
5. Confirm:
   - `NES-SDR` title is visible;
   - graph is centered and 24 columns wide;
   - labels are readable;
   - no unexpected scrolling;
   - the display remains stable for several minutes.

Expected CPU behavior after setup: the 2A03 is executing `JMP $0200` from
internal RAM.

## B. Confirm the internal-RAM parking assumption

Goal: verify the console survives loss of cartridge PRG.

Before adding RF code, use a firmware test command that only performs:

```text
RUN
 -> LOAD for a short bounded interval
 -> RUN
```

without changing SRAM contents.

Start with a long interval that is easy to observe, for example 50-100 ms.

Confirm after every cycle:

- the image returns;
- no RESET is needed;
- no scroll/palette corruption remains;
- the console does not crash.

Then repeat automatically.

## C. Synthetic CHR live refresh

Apply the reference CHR-only refresh API from
`integration/fc-rom-vomitter/`.

Feed generated 3072-byte graph frames without RF capture.

Suggested sequence:

```text
flat
 -> single peak left
 -> single peak center
 -> single peak right
 -> full scale
 -> synthetic two-peak spectrum
```

Refresh initially at 1 Hz.

Confirm the static font/UI never changes.

## D. Electrical validation

Probe at minimum:

- LOAD_MODE
- RUN
- CHR_WE_n
- CHR_OE_n
- one PPU-side CHR data bit

Look specifically for any interval where MCU and console bus drivers could
fight.

Run repeated refresh cycles before enabling Wi-Fi/RF capture.

Suggested first stress target:

```text
10,000 refreshes at 1 Hz-equivalent ownership cycling
```

The test can run faster than 1 Hz if the SRAM path allows it; the purpose is
ownership repeatability.

## E. RF integration

Only after A-D pass:

1. add the ESP-SDR last-spectrum accessor;
2. use 16 MS/s, 256-point FFT;
3. capture for about 50-100 ms;
4. stop RF capture;
5. render the latest SPC1 frame;
6. refresh 3072 CHR bytes;
7. repeat around once per second.

Keep RF capture and SRAM LOAD phases separate for the first implementation.

## F. Self-noise experiment

Record the spectrum under these conditions:

1. cartridge powered by USB only;
2. Famicom powered, before active display;
3. stable PPU display;
4. repeated CHR refresh;
5. USB disconnected if operation allows;
6. different antenna orientations.

This should make Famicom/PPU/bus-generated RF lines easy to distinguish from
external 2.4 GHz activity.

## What to record

For each milestone, keep:

- a photo/video of the screen;
- firmware commit SHA;
- ROM commit SHA;
- capture frequency / sample rate / FFT size;
- scope screenshots for LOAD/RUN ownership;
- any visible display artifact duration.

Those records will make later optimization much easier.
