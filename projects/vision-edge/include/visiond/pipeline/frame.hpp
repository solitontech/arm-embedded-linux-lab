#pragma once
#include <cstdint>

namespace visiond {

enum class PixelFormat : uint8_t {
    YUYV,       // 16bpp packed YUV 4:2:2 (V4L2 default)
    NV12,       // 12bpp planar YUV 4:2:0 (hardware codec input)
    RGB24,      // 24bpp packed RGB
    GRAY8,      // 8bpp grayscale
};

struct FrameDescriptor {
    uint8_t*    data{nullptr};       // Pointer to pixel buffer (not owned)
    uint32_t    width{0};            // Frame width in pixels
    uint32_t    height{0};           // Frame height in pixels
    uint32_t    stride{0};           // Bytes per row (may include padding)
    PixelFormat format{PixelFormat::YUYV};
    uint64_t    timestamp_ns{0};     // Monotonic clock timestamp
    int         dma_fd{-1};          // DMA-BUF fd (-1 if not DMA-backed)
    uint32_t    sequence{0};         // Frame sequence counter
};

} // namespace visiond
