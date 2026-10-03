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

So the proposed upstream-facing change is deliberately tiny:

```c
bool ring_capture_last_spec(const uint8_t **frame, size_t *length);
```

The hot path only records the final frame length. There is:

- no additional frame copy;
- no callback from the timing-sensitive RF loop;
- no CHR write while interrupts are disabled;
- no SRAM-bus ownership change during RF capture.

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
capture window:    50-100 ms
refresh interval:  1 s
```

Once hardware works, tune the capture window and smoothing for appearance.

## Patch

`0001-expose-last-spectrum.patch` documents the proposed small upstream
change. It is kept here as an integration aid, not as a vendored copy of
ESP-SDR.
