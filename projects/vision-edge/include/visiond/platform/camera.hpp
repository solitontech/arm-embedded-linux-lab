#pragma once
#include <labkit/types.hpp>
#include <labkit/expected.hpp>
#include <labkit/logger.hpp>
#include "visiond/pipeline/frame.hpp"
#include <cstdint>
#include <memory>

namespace visiond {
using labkit::expected;
using labkit::unexpected;
using labkit::Error;
using labkit::ErrorCode;
using labkit::ILogger;
using labkit::LogLevel;

struct CameraConfig {
    uint32_t    width{1920};
    uint32_t    height{1080};
    uint32_t    fps{30};
    PixelFormat format{PixelFormat::YUYV};
    uint32_t    buffer_count{4};
};

class ICameraSource {
public:
    virtual ~ICameraSource() = default;

    virtual expected<void, Error>            open(const CameraConfig& cfg) = 0;
    virtual expected<void, Error>            start_streaming()             = 0;
    virtual expected<FrameDescriptor, Error> dequeue_frame()               = 0;
    virtual void                             return_frame(uint32_t index)  = 0;
    virtual void                             stop_streaming()              = 0;
};

// Factory functions — architecture selects the implementation
#ifdef __aarch64__
std::unique_ptr<ICameraSource> make_v4l2_camera(ILogger& logger);
#endif
std::unique_ptr<ICameraSource> make_synthetic_camera(ILogger& logger);

} // namespace visiond
