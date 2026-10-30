#include "visiond/platform/camera.hpp"
#include <vector>
#include <cstring>

namespace visiond {

class SyntheticCameraSource : public ICameraSource {
public:
    explicit SyntheticCameraSource(ILogger& logger) : logger_(logger) {}

    expected<void, Error> open(const CameraConfig& cfg) override {
        width_  = cfg.width;
        height_ = cfg.height;
        stride_ = cfg.width * 2;  // YUYV = 2 bytes/pixel
        frame_size_ = stride_ * height_;

        // Pre-allocate synthetic frame buffers
        buffers_.resize(cfg.buffer_count, std::vector<uint8_t>(frame_size_));
        for (auto& buf : buffers_)
            generate_gradient_pattern(buf.data(), width_, height_);

        logger_.log(LogLevel::INFO, "Synthetic camera opened: " +
                    std::to_string(width_) + "x" + std::to_string(height_));
        return {};
    }

    expected<void, Error> start_streaming() override { return {}; }

    expected<FrameDescriptor, Error> dequeue_frame() override {
        FrameDescriptor fd{};
        fd.data     = buffers_[current_index_].data();
        fd.width    = width_;
        fd.height   = height_;
        fd.stride   = stride_;
        fd.index    = current_index_;
        fd.sequence = sequence_++;
        fd.dma_fd   = -1;  // No real DMA
        current_index_ = (current_index_ + 1) % static_cast<uint32_t>(buffers_.size());
        return fd;
    }

    void return_frame(uint32_t /*index*/) override {}
    void stop_streaming() override {}

private:
    void generate_gradient_pattern(uint8_t* data, uint32_t w, uint32_t h) {
        for (uint32_t y = 0; y < h; ++y)
            for (uint32_t x = 0; x < w; ++x) {
                size_t offset = (y * w + x) * 2;
                data[offset]     = static_cast<uint8_t>((x * 255) / w);  // Y (luminance gradient)
                data[offset + 1] = 128;                                   // U/V (neutral chroma)
            }
    }

    ILogger&  logger_;
    uint32_t  width_{0}, height_{0}, stride_{0}, frame_size_{0};
    uint32_t  current_index_{0}, sequence_{0};
    std::vector<std::vector<uint8_t>> buffers_;
};

std::unique_ptr<ICameraSource> make_synthetic_camera(ILogger& logger) {
    return std::make_unique<SyntheticCameraSource>(logger);
}

} // namespace visiond
