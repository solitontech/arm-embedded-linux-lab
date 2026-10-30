#pragma once
#include <labkit/lifecycle.hpp>
#include <labkit/logger.hpp>
#include <labkit/event.hpp>
#include "visiond/app/config.hpp"
#include "visiond/web/stream.hpp"
#include "visiond/web/shared_state.hpp"
#include <atomic>
#include <memory>
#include <thread>

namespace visiond {
using labkit::expected;
using labkit::unexpected;
using labkit::Error;
using labkit::ErrorCode;
using labkit::ISubsystem;
using labkit::SubsystemState;
using labkit::ILogger;
using labkit::EventBus;
using labkit::LogLevel;

class WebServer : public ISubsystem {
public:
    WebServer(ILogger& logger, EventBus& bus, const DaemonConfig& config);
    ~WebServer() override;

    expected<void, Error> init()  override;
    expected<void, Error> start() override;
    void                  stop()  override;
    std::string_view  name()  const override { return "webserver"; }
    SubsystemState    state() const override { return state_; }

private:
    ILogger&       logger_;
    EventBus&      bus_;
    uint16_t       port_;
    SubsystemState state_{SubsystemState::CREATED};
    std::atomic<bool> running_{false};
    std::thread       accept_thread_;

    std::unique_ptr<SharedState> state_data_;
    MjpegStream    mjpeg_;
    WsTelemetry    ws_telemetry_;
};

} // namespace visiond
