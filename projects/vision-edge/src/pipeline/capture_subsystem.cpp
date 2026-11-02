#include "visiond/pipeline/capture_subsystem.hpp"
#include "visiond/pipeline/thread_utils.hpp"
#include "visiond/core/events.hpp"
#include <chrono>

namespace visiond {

CaptureSubsystem::CaptureSubsystem(
    ILogger& logger,
    std::unique_ptr<ICameraSource> camera,
    std::unique_ptr<ISIMDEngine> simd,
    LocklessTripleBuffer<FrameDescriptor>& ring_buffer,
    TripController& trip_controller,
    EventBus& event_bus,
    const CameraConfig& cam_cfg,
    uint8_t diff_threshold,
    int capture_core)
    : logger_(logger)
    , camera_(std::move(camera))
    , simd_(std::move(simd))
    , ring_buffer_(ring_buffer)
    , trip_controller_(trip_controller)
    , event_bus_(event_bus)
    , cam_cfg_(cam_cfg)
    , diff_threshold_(diff_threshold)
    , capture_core_(capture_core)
{}

CaptureSubsystem::~CaptureSubsystem() {
    stop();
}

expected<void, Error> CaptureSubsystem::init() {
    auto result = camera_->open(cam_cfg_);
    if (!result.has_value())
        return result;

    logger_.log(LogLevel::INFO,
        "Capture subsystem initialized (SIMD: " + std::string(simd_->name()) + ")");
    state_ = SubsystemState::INITIALIZED;
    return {};
}

expected<void, Error> CaptureSubsystem::start() {
    auto result = camera_->start_streaming();
    if (!result.has_value())
        return result;

    running_ = true;
    thread_ = std::thread(&CaptureSubsystem::pipeline_loop, this);

    // Pin capture thread to the configured core
    if (capture_core_ >= 0) {
        auto pin = pin_thread_to_core(thread_.native_handle(), capture_core_);
        if (pin.has_value())
            logger_.log(LogLevel::INFO,
                "Capture thread pinned to core " + std::to_string(capture_core_));
        else
            logger_.log(LogLevel::WARN,
                "Core pinning failed: " + pin.error().context);
    }

    state_ = SubsystemState::RUNNING;
    logger_.log(LogLevel::INFO, "Capture pipeline started");
    return {};
}

void CaptureSubsystem::stop() {
    if (!running_.exchange(false))
        return;

    if (thread_.joinable())
        thread_.join();

    camera_->stop_streaming();
    state_ = SubsystemState::STOPPED;
    logger_.log(LogLevel::INFO, "Capture pipeline stopped");
}

void CaptureSubsystem::pipeline_loop() {
    // Capture first frame as the baseline reference
    bool baseline_captured = false;

    while (running_) {
        auto result = camera_->dequeue_frame();
        if (!result.has_value()) {
            // EAGAIN on non-blocking V4L2 — yield and retry
            std::this_thread::sleep_for(std::chrono::milliseconds(1));
            continue;
        }

        auto& frame = result.value();

        if (!baseline_captured) {
            // Store a copy of the first frame as baseline
            size_t frame_bytes = static_cast<size_t>(frame.stride) * frame.height;
            baseline_.assign(frame.data, frame.data + frame_bytes);
            baseline_captured = true;
            logger_.log(LogLevel::INFO,
                "Baseline frame captured (" + std::to_string(frame.width) +
                "x" + std::to_string(frame.height) +
                ", seq " + std::to_string(frame.sequence) + ")");
            camera_->return_frame(frame.index);
            continue;
        }

        // SIMD pixel diff against baseline
        size_t num_pixels = static_cast<size_t>(frame.width) * frame.height;
        frame.anomaly_count = simd_->pixel_diff_threshold(
            frame.data, baseline_.data(), num_pixels, diff_threshold_);

        // Feed anomaly count to trip controller
        trip_controller_.evaluate(frame.anomaly_count);

        // Publish frame descriptor to ring buffer (for Phase 5 web stream)
        auto& write_buf = ring_buffer_.get_write_buffer();
        write_buf = frame;
        ring_buffer_.publish();

        // Publish FrameEvent for web dashboard consumers
        event_bus_.publish(FrameEvent{&frame});

        // Return frame to camera for reuse
        camera_->return_frame(frame.index);
    }
}

} // namespace visiond
