#pragma once
#include <labkit/lifecycle.hpp>
#include <labkit/event.hpp>
#include "visiond/core/events.hpp"
#include <atomic>
#include <condition_variable>
#include <mutex>
#include <thread>

namespace visiond {
using labkit::expected;
using labkit::unexpected;
using labkit::Error;
using labkit::ErrorCode;
using labkit::LogLevel;
using labkit::ILogger;
using labkit::SubsystemState;
using labkit::ISubsystem;
using labkit::EventBus;

class HeartbeatWorker : public ISubsystem {
public:
    HeartbeatWorker(ILogger& logger, IMetricsSource& source,
                    EventBus& bus, uint32_t interval_ms);
    ~HeartbeatWorker() override;

    expected<void, Error> init()  override;
    expected<void, Error> start() override;
    void                  stop()  override;
    std::string_view  name()  const override { return "heartbeat"; }
    SubsystemState    state() const override { return state_; }

private:
    void worker_loop();

    ILogger&        logger_;
    IMetricsSource& source_;
    EventBus&       bus_;
    uint32_t        interval_ms_;
    SubsystemState  state_{SubsystemState::CREATED};
    std::atomic<bool> running_{false};
    std::thread       thread_;
    std::condition_variable cv_;
    std::mutex              cv_mtx_;
};

} // namespace visiond
