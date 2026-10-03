idf_component_register(
    SRCS "nes_sdr_esp_sdr_backend.c"
    REQUIRES nes_sdr esp_sdr_rf
    WHOLE_ARCHIVE
)
