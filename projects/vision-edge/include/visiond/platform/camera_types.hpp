#pragma once
#include "visiond/pipeline/frame.hpp"
#include <cstdint>

namespace visiond {

struct CameraConfig {
    uint32_t    width{1920};
    uint32_t    height{1080};
    uint32_t    fps{30};
    PixelFormat format{PixelFormat::YUYV};
    uint32_t    buffer_count{4};
};

} // namespace visiond
