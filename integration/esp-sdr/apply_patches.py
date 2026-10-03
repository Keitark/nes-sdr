#!/usr/bin/env python3
"""Apply the minimal NES-SDR hooks to a pinned ESP-SDR checkout.

The transform is intentionally strict: every expected source fragment must
occur exactly once. Upstream drift therefore fails loudly instead of silently
patching the wrong location.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected 1 match, found {count}")
    path.write_text(text.replace(old, new, 1))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkout", type=Path)
    args = parser.parse_args()
    root = args.checkout

    ring_h = root / "main/common/ring_capture.h"
    ring_c = root / "main/common/ring_capture.c"
    cmake = root / "main/CMakeLists.txt"
    receiver = root / "main/targets/esp32s3/receiver.c"
    local_h = root / "main/esp_sdr_local.h"

    # Patch 1: expose the most recently encoded SPC1 frame after a bounded run.
    replace_once(
        ring_h,
        '#include <stdbool.h>\n#include <stdint.h>\n',
        '#include <stdbool.h>\n#include <stddef.h>\n#include <stdint.h>\n',
    )
    replace_once(
        ring_h,
        'bool ring_capture_valid_nfft(unsigned n);\n'
        '/* 0 Hz handling after the FFT: 0 = notch bin 0, 1 = slow DC tracker (default). */\n',
        'bool ring_capture_valid_nfft(unsigned n);\n'
        '/* Valid after a completed RING_MODE_SPEC run and until the next run.\n'
        ' * The returned pointer aliases ring_capture.c\'s internal frame buffer.\n'
        ' * Consume it only after ring_capture_run() has returned. */\n'
        'bool ring_capture_last_spec(const uint8_t **frame, size_t *length);\n'
        '/* 0 Hz handling after the FFT: 0 = notch bin 0, 1 = slow DC tracker (default). */\n',
    )
    replace_once(
        ring_c,
        'static uint8_t frame_out[sizeof(spec_header_t) + RING_SPEC_NFFT_MAX + 4];\n'
        'static unsigned spec_n, spec_log2;        /* FFT size of the current run */\n',
        'static uint8_t frame_out[sizeof(spec_header_t) + RING_SPEC_NFFT_MAX + 4];\n'
        'static size_t last_spec_len;\n'
        'static unsigned spec_n, spec_log2;        /* FFT size of the current run */\n',
    )
    replace_once(
        ring_c,
        '    memcpy(frame_out + len, &st.emit_crc, 4);\n'
        '    ring_result_t *r = st.res;\n',
        '    memcpy(frame_out + len, &st.emit_crc, 4);\n'
        '    last_spec_len = len + 4;\n'
        '    ring_result_t *r = st.res;\n',
    )
    replace_once(
        ring_c,
        '/* Retire a bank before RF reuses it. Once unpacking is complete the FFT owns\n',
        'bool ring_capture_last_spec(const uint8_t **frame, size_t *length) {\n'
        '    if (!frame || !length || !last_spec_len) return false;\n'
        '    *frame = frame_out;\n'
        '    *length = last_spec_len;\n'
        '    return true;\n'
        '}\n\n'
        '/* Retire a bank before RF reuses it. Once unpacking is complete the FFT owns\n',
    )
    replace_once(
        ring_c,
        'RING_HOT void ring_capture_run(const ring_config_t *cfg, ring_result_t *r) {\n'
        '    memset(r, 0, sizeof(*r));\n'
        '    memset(&st, 0, sizeof(st));\n',
        'RING_HOT void ring_capture_run(const ring_config_t *cfg, ring_result_t *r) {\n'
        '    memset(r, 0, sizeof(*r));\n'
        '    memset(&st, 0, sizeof(st));\n'
        '    last_spec_len = 0;\n',
    )

    # Patch 2: local-only spectrum mode, avoiding USB output for embedded use.
    replace_once(
        ring_h,
        '    bool stats;                /* SPEC: insert SPS1 statistics frames (~4/s) */\n'
        '    unsigned iq_dec;',
        '    bool stats;                /* SPEC: insert SPS1 statistics frames (~4/s) */\n'
        '    bool local_only;           /* SPEC: keep encoded frame local; skip USB queue */\n'
        '    unsigned iq_dec;',
    )
    replace_once(
        ring_c,
        '    if (txq_push(frame_out, len + 4)) {\n'
        '        st.last_ok = esp_timer_get_time();\n'
        '        r->frames++;\n'
        '        st.dropped = false;\n'
        '    } else {\n',
        '    if (st.cfg->local_only) {\n'
        '        st.last_ok = esp_timer_get_time();\n'
        '        r->frames++;\n'
        '        st.dropped = false;\n'
        '    } else if (txq_push(frame_out, len + 4)) {\n'
        '        st.last_ok = esp_timer_get_time();\n'
        '        r->frames++;\n'
        '        st.dropped = false;\n'
        '    } else {\n',
    )
    replace_once(
        ring_c,
        '#if !CONFIG_IDF_TARGET_ESP32S3\n'
        '#define TXQ_SIZE 2048u\n'
        '#else\n'
        '#define TXQ_SIZE 16384u /* 7 frames of 2048 bins, 56 of 256 */\n'
        '#endif\n',
        '#if !CONFIG_IDF_TARGET_ESP32S3 || defined(ESP_SDR_EMBEDDED)\n'
        '/* The embedded backend keeps SPC1 local and does not stream USB frames. */\n'
        '#define TXQ_SIZE 2048u\n'
        '#else\n'
        '#define TXQ_SIZE 16384u /* 7 frames of 2048 bins, 56 of 256 */\n'
        '#endif\n',
    )
    replace_once(
        cmake,
        'option(SAMPLE_RATE_PROBE "Build volatile hardware sample-rate diagnostics (never package)" OFF)\n',
        'option(SAMPLE_RATE_PROBE "Build volatile hardware sample-rate diagnostics (never package)" OFF)\n'
        'option(ESP_SDR_EMBEDDED "Build ESP-SDR as a component inside another ESP-IDF app" OFF)\n',
    )
    replace_once(
        cmake,
        'idf_component_register(SRCS "${receiver}" ${sources}\n'
        '    LDFRAGMENTS ${fragments}\n',
        'idf_component_register(SRCS "${receiver}" ${sources}\n'
        '    INCLUDE_DIRS "."\n'
        '    LDFRAGMENTS ${fragments}\n',
    )
    replace_once(
        cmake,
        'target_link_options(${COMPONENT_LIB} INTERFACE\n'
        '    "-T${CMAKE_CURRENT_LIST_DIR}/${target_dir}/sram_guard.ld")\n',
        'if(ESP_SDR_EMBEDDED)\n'
        '    target_compile_definitions(${COMPONENT_LIB} PRIVATE ESP_SDR_EMBEDDED=1)\n'
        'endif()\n'
        'target_link_options(${COMPONENT_LIB} INTERFACE\n'
        '    "-T${CMAKE_CURRENT_LIST_DIR}/${target_dir}/sram_guard.ld")\n',
    )

    local_h.write_text(
        '#pragma once\n\n'
        '#include <stdbool.h>\n'
        '#include <stddef.h>\n'
        '#include <stdint.h>\n\n'
        '#include "sdkconfig.h"\n\n'
        '#if CONFIG_IDF_TARGET_ESP32S3\n'
        '/* Wi-Fi must already be in the ESP-SDR-compatible NULL/promiscuous mode. */\n'
        'bool esp_sdr_s3_local_spec(uint32_t frequency_mhz, uint32_t duration_ms,\n'
        '                           const uint8_t **frame, size_t *length);\n'
        '#endif\n'
    )

    replace_once(
        receiver,
        '#include "burst_serial.h"\n#include "rx_tuning.h"\n',
        '#include "burst_serial.h"\n#include "esp_sdr_local.h"\n#include "rx_tuning.h"\n',
    )
    helper = '''bool esp_sdr_s3_local_spec(uint32_t mhz, uint32_t duration_ms,
                           const uint8_t **frame, size_t *length) {
    if (!frame || !length || !duration_ms || duration_ms > 1000u ||
        mhz < S3_FREQ_MIN || mhz > S3_FREQ_MAX) return false;

    frequency_mhz=mhz;
    rx_ready=false;
    prepare_rx();
    ring_capture_init();

    ring_config_t c={
        .mode=RING_MODE_SPEC,
        .rate=6,
        .duration_ms=duration_ms,
        .nfft=256,
        .stride=2,
        .units_per_frame=1,
        .max_hold=false,
        .stats=false,
        .local_only=true,
    };
    ring_result_t result;
    rx_filter_apply();
    ring_capture_run(&c,&result);
    rx_filter_restore();
    if (result.status || !result.frames) return false;
    return ring_capture_last_spec(frame,length);
}

'''
    replace_once(
        receiver,
        'static bool ring_command(const char *line) {\n',
        helper + 'static bool ring_command(const char *line) {\n',
    )

    replace_once(
        receiver,
        'void app_main(void) {\n',
        '#ifndef ESP_SDR_EMBEDDED\nvoid app_main(void) {\n',
    )
    receiver_text = receiver.read_text()
    if not receiver_text.endswith('}\n'):
        raise RuntimeError(f"{receiver}: expected app_main closing brace at EOF")
    receiver.write_text(
        receiver_text + '#endif /* ESP_SDR_EMBEDDED */\n'
    )

    print("ESP-SDR NES-SDR integration transforms applied")


if __name__ == "__main__":
    main()
