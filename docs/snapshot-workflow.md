# Zero-mod snapshot refresh workflow

The useful no-hardware-modification mode is not limited to one image per power cycle.

FC ROM Vomitter already knows how to:

- isolate the Famicom from both SRAM buses;
- let the ESP32 write and verify SRAM;
- return the SRAMs to the console.

NES-SDR can intentionally use that behavior as a **snapshot refresh** operation.

## User flow

```text
Famicom showing spectrum N
          |
          | press ESP BOOT / capture button
          v
ESP32 asserts safe LOAD topology
          |
          | Famicom CPU may stop executing useful code
          | but is electrically isolated from SRAM
          v
ESP32 captures RF
          |
          v
FFT -> SPC1 bins -> 31 bars -> CHR
          |
          v
rewrite / verify PRG + CHR SRAM
          |
          v
restore RUN topology
          |
          v
READY LED
          |
          | press Famicom RESET
          v
Famicom shows spectrum N+1
```

This deliberately accepts that the 2A03 will not keep running normally during the SRAM rewrite. We do not need it to. After RUN ownership is restored, the console RESET vector is valid again.

## Why this is preferable to clever timing

The released board's bus-safety design stays intact:

- no simultaneous console/ESP address drive;
- no simultaneous console/ESP data drive;
- no rewired buffer enables;
- no dependence on exact PPU timing;
- no blind one-second LOAD pulse while the CPU happens to be executing cartridge code.

It is slower and requires a RESET press, but it is an excellent first real-hardware SDR mode.

## Intended firmware state machine

```text
DISPLAYING
   |
   | capture requested
   v
ISOLATE
   |
   v
RF_CAPTURE
   |
   v
FFT
   |
   v
RENDER_CHR
   |
   v
SRAM_WRITE_VERIFY
   |
   v
EXPOSE_RUN
   |
   v
WAIT_FOR_USER_RESET
```

The existing FC ROM Vomitter blue READY LED can naturally indicate the final state.

## Future ergonomics

Without modifying cartridge hardware, capture can be requested through any input already available to the ESP32, for example:

- the module/board BOOT button;
- USB command;
- web UI;
- periodic capture when the console is known not to need continuous execution.

The supported baseline should remain explicit: **capture, rewrite, then press RESET**.
