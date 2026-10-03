cmake_minimum_required(VERSION 3.16)
project(nes_sdr_host_tests C)

enable_testing()
add_library(nes_sdr_core STATIC
    ../firmware/src/nes_sdr_frame.c
    ../firmware/src/nes_sdr_spc1.c
    ../firmware/src/nes_sdr_live.c)
target_include_directories(nes_sdr_core PUBLIC ../firmware/include)

foreach(test_name IN ITEMS test_spc1 test_live)
    add_executable(${test_name} ${test_name}.c)
    target_link_libraries(${test_name} PRIVATE nes_sdr_core)
    add_test(NAME ${test_name} COMMAND ${test_name})
endforeach()
