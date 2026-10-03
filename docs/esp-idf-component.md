# ESP-IDF component integration

The `firmware/` directory is a self-contained ESP-IDF component.

From an integration project, either copy/symlink the directory into
`components/nes_sdr`, or add it through `EXTRA_COMPONENT_DIRS`.

Example top-level CMake:

```cmake
set(EXTRA_COMPONENT_DIRS
    "${CMAKE_CURRENT_LIST_DIR}/../nes-sdr/firmware"
)

include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(nes_sdr_integration)
```

Consumer code can then include:

```c
#include "nes_sdr_frame.h"
#include "nes_sdr_spc1.h"
#include "nes_sdr_live.h"
```

The component intentionally has no direct dependency on ESP-IDF APIs. Platform
code supplies the capture and refresh callbacks.

That makes the same renderer/state-machine code usable in host CI and on the
ESP32-S3.
