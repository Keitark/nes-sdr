# ESP-SDR integration

Reference upstream: `ESPARGOS/esp-sdr`, inspected at commit
`ac627b0b7cb1b31da6e41e08ee38e9ae9e21863e`.

## Goal

NES-SDR only needs one recent on-device spectrum frame about once per second.

It does not need raw I/Q and it does not need to keep USB spectrum streaming active.

## Lowest-risk hook

The ESP32-S3 continuous spectrum implementation already encodes the completed
spectrum into the static `frame_out` buffer in `main/common/ring_capture.c`.

After `ring_capture_run()` returns, RF bank rotation has stopped and the last
encoded frame can be consumed safely.

The integration patch now adds a local-output mode and target helper:

```c
bool ring_capture_last_spec(const uint8_t **frame, size_t *length);
bool s3_local_spec_init(void);
bool s3_capture_local_spec(unsigned duration_ms, unsigned rate, unsigned nfft,
                           const uint8_t **frame, size_t *length);
```

`local_only` retains the most recent complete SPC1 frame without queueing it
to USB. The helper reuses `prepare_rx()`, the filter setup, and
`ring_capture_run()`; it returns only after RF capture has stopped. There is:

- no additional frame copy;
- no callback from the timing-sensitive RF loop;
- no CHR write while interrupts are disabled;
- no SRAM-bus ownership change during RF capture.

In embedded mode the ESP-SDR command-loop `app_main()` is omitted. The
integrating firmware initializes NVS and the event loop, then calls
`s3_local_spec_init()` to start Wi-Fi in receive-only NULL mode. Its SoftAP
cannot operate at the same time. The original ESP-SDR serial behavior remains
the default when embedded mode is not enabled.

## Intended 1 Hz cycle

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
sleep until next ~1 Hz update
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

The helper uses the same receiver preparation, analog-filter application,
capture, and filter restoration as the existing `SPEC` command. NES-SDR does
not duplicate RF register setup.

## Suggested first configuration

Start conservatively:

```text
sample rate:       16 MS/s (rate code 6)
FFT:               256
stride:            2
units per frame:   1
detector:          mean
capture window:    50-100 ms
refresh interval:  1 s
```

Once hardware works, tune the capture window and smoothing for appearance.

## Patch

`0001-expose-last-spectrum.patch` applies to upstream commit
`ac627b0b7cb1b31da6e41e08ee38e9ae9e21863e`. It is an integration aid,
not a vendored copy of ESP-SDR. The combined firmware build also needs the
upstream repository's pinned `esp-dsp` submodule.
