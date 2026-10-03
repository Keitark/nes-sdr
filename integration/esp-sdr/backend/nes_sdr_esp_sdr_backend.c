#include "nes_sdr_backend.h"
#include "esp_sdr_local.h"

/* PlatformIO needs an explicit archive reference to include this override. */
void nes_sdr_esp_sdr_backend_link_anchor(void)
{
}

bool nes_sdr_rf_backend_available(void)
{
    return true;
}

bool nes_sdr_rf_backend_capture(uint32_t center_frequency_mhz,
                                uint32_t duration_ms,
                                const uint8_t **frame,
                                size_t *length)
{
    return esp_sdr_s3_local_spec(center_frequency_mhz, duration_ms,
                                 frame, length);
}
