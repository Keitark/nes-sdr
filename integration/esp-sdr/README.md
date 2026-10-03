# ESP-SDR integration

Reference upstream: `ESPARGOS/esp-sdr`, inspected at commit
`ac627b0b7cb1b31da6e41e08ee38e9ae9e21863e`.

## Goal

NES-SDR only needs one recent on-device spectrum frame about five times per second.

It does not need raw I/Q and it does not need to keep USB spectrum streaming active.

## Lowest-risk hook

The ESP32-S3 continuous spectrum implementation already encodes the completed
spectrum into the static `frame_out` buffer in `main/common/ring_capture.c`.

After `ring_capture_run()` returns, RF bank rotation has stopped and the last
encoded frame can be consumed safely.

So the proposed upstream-facing change is deliberately tiny:

```c
bool ring_capture_last_spec(const uint8_t **frame, size_t *length);
```

The hot path only records the final frame length. There is:

- no additional frame copy;
- no callback from the timing-sensitive RF loop;
- no CHR write while interrupts are disabled;
- no SRAM-bus ownership change during RF capture.

## RF ownership: SoftAP and SDR are separate phases

The same ESP32-S3 Wi-Fi PHY is used by ROM Vomitter's SoftAP and by ESP-SDR.

The first integrated PoC therefore treats them as **exclusive modes**:

```text
SETUP MODE
  SoftAP / browser upload
  install signed NES-SDR ROM
  press Famicom RESET once
  user chooses "Start SDR"
          |
          v
HTTP response completes
          |
          v
stop SoftAP
WIFI_MODE_NULL
promiscuous RX setup
          |
          v
SDR MODE
  no browser connection
  local spectrum capture
  CHR refresh at ~5 Hz
```

Do not stop/restart the AP every second. The first PoC remains in SDR mode until
the cartridge ESP is reset or power-cycled.

Cloud-pull mode should be disabled/refused before entering SDR mode because its
background task expects station Wi-Fi connectivity.

## Intended 5 Hz cycle

For the temporary embedded build, the local-only SPC1 path uses a 2 KiB USB
output queue instead of the standalone S3 command interface's 16 KiB queue.
It also limits the embedded FFT workspace to the 256 points used by NES-SDR;
the standalone ESP-SDR build retains its 2048-point option. This frees about
37 KiB of internal RAM. The combined-build check requires the strong ESP-SDR
backend symbols and at least 44 KiB of DRAM before the S3 RF ring aperture,
leaving room for ROM Vomitter's 40 KiB image allocation. Link-time headroom
does not establish that boot and RF capture succeed on the board.

```text
prepare receiver
      |
      v
run short SPEC capture
  16 MS/s
  256-point FFT
      |
      v
ring_capture_run() returns
      |
      v
ring_capture_last_spec()
      |
      v
SPC1 -> 24 bar heights
      |
      v
render 3072 CHR bytes
      |
      v
ROM Vomitter LOAD
      |
      v
CHR write + verify
      |
      v
ROM Vomitter RUN
      |
      v
sleep until next 200 ms frame boundary
```

RF capture and Famicom SRAM access are therefore time-separated.

## Why 256 bins first

ESP-SDR's S3 continuous profile already supports 256-bin FFTs at 16 MS/s.

For a 24-column Famicom graph, 256 bins are plenty for the first PoC and keep
the post-capture frame small:

```text
28-byte SPC1 header
256 spectrum bytes
4-byte CRC
= 288 bytes
```

Higher FFT sizes can be added later without changing the NES renderer.

## Receiver-side helper

A future integration branch can expose one target-level helper around the
currently static S3 receiver preparation code:

```c
bool s3_capture_local_spec(unsigned duration_ms,
                           unsigned rate,
                           unsigned nfft,
                           const uint8_t **frame,
                           size_t *length);
```

Internally it should reuse the exact same:

- receiver preparation;
- analog filter application;
- `ring_capture_run()`;
- filter restore;

used by the existing `SPEC` command.

Do not duplicate RF register setup in NES-SDR.

## Suggested first configuration

Start conservatively:

```text
sample rate:       16 MS/s (rate code 6)
FFT:               256
stride:            2
units per frame:   1
detector:          mean
capture window:    ~50 ms
refresh interval:  200 ms (5 Hz)
```

Once hardware works, tune the capture window and smoothing for appearance. The 200 ms budget must include RF capture, CHR rendering, SRAM write, readback verification, and LOAD/RUN transition margin.

## Patches

Apply to the inspected ESP-SDR revision in order:

1. `0001-expose-last-spectrum.patch`
   - exposes the last completed SPC1 frame after a bounded run;
2. `0002-local-only-s3-spectrum.patch`
   - adds a local-only SPEC mode that does not queue USB frames;
   - exposes `esp_sdr_s3_local_spec()` for a bounded 16 MS/s / 256-bin S3 capture.

These patches are integration aids for the GPL-3.0-or-later ESP-SDR codebase;
ESP-SDR source is intentionally not vendored into the FC ROM Vomitter MIT
release tree.
