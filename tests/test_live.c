#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "nes_sdr_frame.h"
#include "nes_sdr_live.h"

enum { N = 256, HEADER = 28, CRC = 4 };

typedef struct {
    uint8_t frame[HEADER + N + CRC];
    bool capture_ok;
    int refresh_result;
    unsigned refresh_calls;
    size_t refresh_length;
    uint8_t first_graph_byte;
} fixture_t;

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

static void make_frame(fixture_t *f)
{
    memset(f, 0, sizeof(*f));
    f->capture_ok = true;
    memcpy(f->frame, "SPC1", 4);
    put32(f->frame + 4, 1);
    put32(f->frame + 16, 4096);
    put16(f->frame + 20, 8);
    f->frame[26] = 8;
    f->frame[27] = 2;
    for (unsigned i = 0; i < N; ++i) {
        f->frame[HEADER + i] = (uint8_t)((i * 29u + 17u) & 0xffu);
    }
}

static bool capture_cb(void *context, const uint8_t **frame, size_t *length)
{
    fixture_t *f = context;
    if (!f->capture_ok) {
        return false;
    }
    *frame = f->frame;
    *length = sizeof(f->frame);
    return true;
}

static int refresh_cb(void *context, const uint8_t *graph, size_t length)
{
    fixture_t *f = context;
    f->refresh_calls++;
    f->refresh_length = length;
    f->first_graph_byte = graph[0];
    return f->refresh_result;
}

int main(void)
{
    fixture_t fixture;
    make_frame(&fixture);

    nes_sdr_live_ops_t ops = {
        .capture = capture_cb,
        .capture_context = &fixture,
        .refresh = refresh_cb,
        .refresh_context = &fixture,
    };
    nes_sdr_live_stats_t stats = {0};
    uint8_t graph[NES_SDR_GRAPH_BYTES];

    assert(nes_sdr_live_step(&ops, &stats, graph) == NES_SDR_LIVE_OK);
    assert(stats.attempts == 1);
    assert(stats.frames_ok == 1);
    assert(fixture.refresh_calls == 1);
    assert(fixture.refresh_length == NES_SDR_GRAPH_BYTES);

    fixture.capture_ok = false;
    assert(nes_sdr_live_step(&ops, &stats, graph) == NES_SDR_LIVE_CAPTURE_FAILED);
    assert(stats.capture_failures == 1);

    fixture.capture_ok = true;
    fixture.frame[0] = 'X';
    assert(nes_sdr_live_step(&ops, &stats, graph) == NES_SDR_LIVE_FRAME_INVALID);
    assert(stats.invalid_frames == 1);

    make_frame(&fixture);
    fixture.refresh_result = -1;
    ops.capture_context = &fixture;
    ops.refresh_context = &fixture;
    assert(nes_sdr_live_step(&ops, &stats, graph) == NES_SDR_LIVE_REFRESH_FAILED);
    assert(stats.refresh_failures == 1);

    puts("live refresh state-machine tests passed");
    return 0;
}
