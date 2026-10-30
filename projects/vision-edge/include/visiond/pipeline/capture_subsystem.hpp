#pragma once
#include <labkit/lifecycle.hpp>
#include <labkit/logger.hpp>
#include <labkit/event.hpp>
#include "visiond/platform/camera.hpp"
#include "visiond/pipeline/simd_engine.hpp"
#include "visiond/pipeline/stage.hpp"
#include "visiond/pipeline/ring_buffer.hpp"
#include "visiond/safety/trip_controller.hpp"
#include <atomic>
#include <memory>
#include <thread>
#include <vector>

namespace visiond {
using labkit::ILogger;
using labkit::ISubsystem;
using labkit::SubsystemState;
using labkit::LogLevel;
using labkit::EventBus;

class CaptureSubsystem : public ISubsystem {
public:
    CaptureSubsystem(ILogger& logger,
                     std::unique_ptr<ICameraSource> camera,
                     std::unique_ptr<ISIMDEngine> simd,
                     LocklessTripleBuffer<FrameDescriptor>& ring_buffer,
                     TripController& trip_controller,
                     EventBus& event_bus,
                     const CameraConfig& cam_cfg,
                     uint8_t diff_threshold = 25,
                     int capture_core = -1);

    ~CaptureSubsystem() override;

    expected<void, Error> init()  override;
    expected<void, Error> start() override;
    void                  stop()  override;
    std::string_view  name()  const override { return "capture"; }
    SubsystemState    state() const override { return state_; }

private:
    void pipeline_loop();

    ILogger&                                logger_;
    std::unique_ptr<ICameraSource>          camera_;
    std::unique_ptr<ISIMDEngine>            simd_;
    LocklessTripleBuffer<FrameDescriptor>&  ring_buffer_;
    TripController&                         trip_controller_;
    EventBus&                               event_bus_;
    CameraConfig                            cam_cfg_;
    uint8_t                                 diff_threshold_;
    int                                     capture_core_;

    SubsystemState      state_{SubsystemState::CREATED};
    std::atomic<bool>   running_{false};
    std::thread         thread_;
    std::vector<uint8_t> baseline_;       // First frame stored as reference
};

} // namespace visiond
