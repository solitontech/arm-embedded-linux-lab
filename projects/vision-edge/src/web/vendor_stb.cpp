// Compile stb_image_write — single translation unit
// stb_image_write.h is in shared/lib/vendor/stb/ (on the include path via framework.mk)
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wmissing-field-initializers"
#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "stb/stb_image_write.h"
#pragma GCC diagnostic pop
