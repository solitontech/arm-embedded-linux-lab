#include "visiond/platform/camera.hpp"
#include <vector>
#include <cstring>

namespace visiond {

class SyntheticCameraSource : public ICameraSource {
public:
    explicit SyntheticCameraSource(ILogger& logger) : logger_(logger) {}

    expected<void, Error> open(const CameraConfig& cfg) override {
        width_      = cfg.width;
        height_     = cfg.height;
        stride_     = cfg.width * 2;  // YUYV = 2 bytes/pixel
        frame_size_ = stride_ * height_;

        // Block size: 1/6 width x 1/4 height
        block_w_ = width_  / 6;
        block_h_ = height_ / 4;

        // Allocate render buffer (single frame, regenerated each dequeue)
        buffers_.resize(cfg.buffer_count, std::vector<uint8_t>(frame_size_, 0));

        logger_.log(LogLevel::INFO,
            "Synthetic camera opened (moving block): " +
            std::to_string(width_) + "x" + std::to_string(height_));
        return {};
    }

    expected<void, Error> start_streaming() override { return {}; }

    expected<FrameDescriptor, Error> dequeue_frame() override {
        render_frame(buffers_[current_index_].data(), sequence_);

        FrameDescriptor fd{};
        fd.data     = buffers_[current_index_].data();
        fd.width    = width_;
        fd.height   = height_;
        fd.stride   = stride_;
        fd.index    = current_index_;
        fd.sequence = sequence_++;
        fd.dma_fd   = -1;
        current_index_ = (current_index_ + 1) % static_cast<uint32_t>(buffers_.size());
        return fd;
    }

    void return_frame(uint32_t /*index*/) override {}
    void stop_streaming() override {}

private:
    // Render a YUYV frame: dark background + bright white block bouncing around
    void render_frame(uint8_t* data, uint32_t seq) {
        // Background: dark grey (Y=40, UV neutral)
        for (size_t i = 0; i < frame_size_; i += 2) {
            data[i]     = 40;   // Y — dark
            data[i + 1] = 128;  // UV — neutral chroma (no colour cast)
        }

        // Block position: triangle-wave bounce on both axes, different speeds
        const uint32_t travel_x = width_  - block_w_;
        const uint32_t travel_y = height_ - block_h_;
        const uint32_t period_x = travel_x * 2;   // one full left-right bounce
        const uint32_t period_y = travel_y * 2;   // one full up-down bounce

        const uint32_t speed_x = 6;               // px/frame horizontal
        const uint32_t speed_y = 3;               // px/frame vertical (slower → async motion)

        const uint32_t px = (seq * speed_x) % period_x;
        const uint32_t py = (seq * speed_y) % period_y;

        // Triangle wave: 0 → travel → 0
        const uint32_t bx = (px < travel_x) ? px : (period_x - px);
        const uint32_t by = (py < travel_y) ? py : (period_y - py);

        // Draw block: bright white (Y=235, UV neutral)
        for (uint32_t y = by; y < by + block_h_ && y < height_; ++y) {
            for (uint32_t x = bx; x < bx + block_w_ && x < width_; ++x) {
                const size_t offset = (y * width_ + x) * 2;
                data[offset]     = 235;  // Y — bright
                data[offset + 1] = 128;  // UV — white (neutral chroma)
            }
        }
    }

    ILogger&  logger_;
    uint32_t  width_{0}, height_{0}, stride_{0}, frame_size_{0};
    uint32_t  block_w_{0}, block_h_{0};
    uint32_t  current_index_{0}, sequence_{0};
    std::vector<std::vector<uint8_t>> buffers_;
};

std::unique_ptr<ICameraSource> make_synthetic_camera(ILogger& logger) {
    return std::make_unique<SyntheticCameraSource>(logger);
}

} // namespace visiond
