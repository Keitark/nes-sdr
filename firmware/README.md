# ESP32 firmware integration

This directory currently contains the hardware-independent NES CHR renderer.

The intended ESP-SDR integration point is deliberately narrow:

```c
uint8_t fft_u8[FFT_BINS];
uint8_t bars[NES_SDR_COLUMNS];
uint8_t chr[NES_SDR_CHR_BYTES];

nes_sdr_reduce_bins_u8(fft_u8, FFT_BINS, bars);
nes_sdr_render_chr(bars, chr);
```

The resulting `chr` buffer can be copied into the normalized NROM image used by FC ROM Vomitter before its existing `sram_bus_load_and_verify()` path runs.

## Why keep this module independent?

- it can be host-tested without ESP-IDF;
- ESP-SDR can change internally without changing the NES display contract;
- the same renderer can consume real FFT bins, recorded captures, or synthetic test data.

The next firmware milestone is an adapter that takes ESP-SDR on-chip spectrum output and maps its magnitude range into unsigned 8-bit bins.
