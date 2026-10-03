#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "nes_sdr_frame.h"
#include "nes_sdr_spc1.h"

static void put16(uint8_t *p, uint16_t v)
{
    p[0] = (uint8_t)v;
    p[1] = (uint8_t)(v >> 8);
}

static void put32(uint8_t *p, uint32_t v)
{
    put16(p, (uint16_t)v);
    put16(p + 2, (uint16_t)(v >> 16));
}

int main(void)
{
    enum { N = 256, HEADER = 28, CRC = 4 };
    uint8_t frame[HEADER + N + CRC];
    memset(frame, 0, sizeof(frame));

    memcpy(frame, "SPC1", 4);
    put32(frame + 4, 42);
    put32(frame + 16, 4096);
    put16(frame + 20, 16);
    frame[23] = 7;
    frame[26] = 8;
    frame[27] = 2;

    /* Strong signal near the middle. */
    for (unsigned i = 110; i < 146; ++i) {
        frame[HEADER + i] = 255;
    }

    nes_sdr_spc1_view_t view;
    assert(nes_sdr_spc1_parse(frame, sizeof(frame), &view));
    assert(view.frame_number == 42);
    assert(view.pairs == 4096);
    assert(view.ffts == 16);
    assert(view.gain == 7);
    assert(view.bin_count == N);

    uint8_t chr[NES_SDR_CHR_BYTES];
    memset(chr, 0x5a, sizeof(chr));
    assert(nes_sdr_spc1_to_chr(frame, sizeof(frame), chr));

    int nonzero = 0;
    for (size_t i = 0; i < sizeof(chr); ++i) {
        nonzero |= chr[i] != 0;
    }
    assert(nonzero);

    /* Static UI/font region must not be touched by a live spectrum update. */
    for (size_t i = NES_SDR_GRAPH_BYTES; i < sizeof(chr); ++i) {
        assert(chr[i] == 0x5a);
    }

    frame[0] = 'X';
    assert(!nes_sdr_spc1_parse(frame, sizeof(frame), &view));

    puts("SPC1 adapter tests passed");
    return 0;
}
