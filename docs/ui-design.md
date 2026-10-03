# UI design

## Direction

The screen should read like a compact 1980s RF instrument, not like a modern
web dashboard squeezed into 256x240 pixels.

Primary visual idea:

- black background;
- white title, labels, and spectrum bars;
- Famicom-red horizontal axis / tick marks;
- monospaced 5x7 uppercase typography;
- generous empty space around the graph;
- no sprites or animation required from the 2A03.

## Screen grid

The PPU background is a 32 x 30 tile grid.

Current layout:

| Row | Content |
|---:|---|
| 2 | `NES-SDR` |
| 4 | `RF SPECTRUM` |
| 6 | `2.4 GHZ / ESP32-S3` |
| 9-16 | 24-column spectrum graph, centered at columns 4-27 |
| 17 | static horizontal axis + low/center/high ticks |
| 19 | `LOW   CENTER   HIGH` |
| 21 | `FFT SPAN / RX BW` |
| 24 | `ESP-SDR + FAMICOM` |

Everything outside those rows stays empty.

## CHR allocation

Pattern table 0 is intentionally split between dynamic graph data and static
instrument UI.

| Tiles | Purpose |
|---|---|
| 0-191 | dynamic spectrum graph |
| 192 | blank |
| 193-235 | 5x7 font glyphs |
| 236 | horizontal axis |
| 237 | axis tick |
| 238-255 | reserved |

This leaves 18 tiles available for future dynamic status text without changing
the graph layout.

## Dynamic graph

Each of the 24 columns owns eight unique tiles, one for each vertical tile row.

The nametable never changes.

A spectrum refresh changes only the bitmaps in tiles 0-191:

```text
24 columns x 8 rows x 16 bytes = 3072 bytes
```

Bars are six pixels wide, leaving one blank pixel on both sides.

## Color planes

Current use:

- plane 0 -> palette color 1 -> white;
- plane 1 -> palette color 2 -> Famicom-red accent;
- both planes -> palette color 3 -> reserved highlight.

Text and spectrum bars use plane 0.

The static axis/ticks use plane 1.

That leaves a useful future option: a peak-hold marker can also use plane 1,
giving a red trace over white live bars without spending more CHR tiles.

## Frequency-axis wording

The first build deliberately avoids hard-coded numeric edge frequencies.

ESP-SDR span depends on sample rate and analog bandwidth. Therefore the fixed
labels are:

```text
LOW        CENTER        HIGH
        FFT SPAN / RX BW
```

Numeric center/span labels can later use tiles 238-255 as dynamically rewritten
status glyphs.

## Design constraints

- do not require CPU-side nametable updates after initialization;
- do not use NMI;
- do not use sprites for essential information;
- keep all changing visual state inside the dynamic CHR region;
- preserve a readable screen even if RF refresh pauses;
- avoid tiny decorative detail that will look poor on composite video.

## Next visual refinements

After the first real Famicom capture:

1. check overscan margins on CRT and HDMI capture;
2. adjust vertical placement if row 24 is too close to overscan;
3. evaluate white/red contrast on real NTSC output;
4. optionally add red peak-hold markers;
5. decide whether reserved tiles should become dynamic center/span readout.
