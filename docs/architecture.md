# Architecture

## Design rule: Rev A-FC stays unmodified

The first NES-SDR target uses a stock FC ROM Vomitter Rev A-FC board. No lifted pins, bodge wires, extra latches, or rewired SRAM signals are required.

That constraint changes the system split:

```text
ESP32-S3                          Famicom
---------                         -------
RF capture
FFT
bin reduction
CHR tile generation
    |
    | existing LOAD path
    v
PRG SRAM + CHR SRAM  ---------->  2A03 + PPU
                                   |
                                   v
                                   TV
```

The ESP32 does all RF/DSP work. The Famicom only displays the resulting CHR image.

## What works with zero hardware changes

The released FC ROM Vomitter already supports:

1. isolating the console from PRG/CHR SRAM;
2. writing PRG and CHR SRAM from the ESP32-S3;
3. verifying SRAM contents;
4. returning ownership to the console;
5. running a mapper-0 image after the user presses RESET.

NES-SDR therefore treats a spectrum image as ordinary CHR ROM data.

The first PoC cycle is:

```text
capture -> FFT -> render CHR -> load SRAM -> RESET -> display
```

This is a snapshot spectrum analyzer, not yet a live one.

## Why live 1 Hz update is not claimed yet

Rev A-FC switches PRG and CHR ownership together with LOAD_MODE.

During RUN:

- Famicom owns PRG SRAM;
- PPU owns CHR SRAM;
- ESP32 address buffers to both SRAMs are disabled.

During LOAD:

- ESP32 owns both SRAMs;
- the Famicom loses PRG SRAM as well as CHR SRAM.

There is also no released-board runtime handshake signal from the Famicom CPU back to the ESP32.

So a software-only live update cannot simply take CHR for a few milliseconds while the game keeps executing from PRG.

## Experimental software-only directions

These are research ideas, not requirements for the first working build.

### Internal-RAM rendezvous

A 2A03 program can copy a tiny wait loop into internal RAM and execute there while cartridge PRG is unavailable. In principle, the ESP32 could switch to LOAD, rewrite CHR, and return to RUN.

The hard problem is synchronization: the released board has no reliable signal telling the ESP32 that the CPU has entered the safe RAM loop.

Blind time-based takeover is therefore intentionally not enabled.

### PPU-address-assisted writes

The PPU can present CHR addresses during rendering while the ESP32 controls CHR WE/OE and its data-side buffer. That suggests exotic write-while-addressed experiments.

The ESP32 cannot observe the full PPU address bus on the released board and the timing margin is small, so this is also experimental only.

## Practical roadmap

1. Make snapshot mode excellent.
2. Integrate ESP-SDR on-device FFT.
3. Generate CHR frames on the ESP32.
4. Measure end-to-end capture-to-display time.
5. Only then investigate software-only live refresh.

If live refresh proves impossible without unsafe timing assumptions, the zero-mod target remains useful as a snapshot analyzer and any minimal hardware-assisted mode will be documented separately rather than silently becoming a requirement.
