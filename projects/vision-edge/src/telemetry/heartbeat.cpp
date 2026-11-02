#include "visiond/telemetry/heartbeat.hpp"
#include <iomanip>
#include <sstream>

namespace visiond {

HeartbeatWorker::HeartbeatWorker(ILogger& logger, IMetricsSource& source,
                                 EventBus& bus, uint32_t interval_ms)
    : logger_(logger), source_(source), bus_(bus), interval_ms_(interval_ms) {}

HeartbeatWorker::~HeartbeatWorker() {
    stop();
}

expected<void, Error> HeartbeatWorker::init() {
    if (state_ != SubsystemState::CREATED)
        return unexpected<Error>(Error{ErrorCode::ALREADY_RUNNING,
                                       "heartbeat: already initialized"});
    state_ = SubsystemState::INITIALIZED;
    logger_.log(LogLevel::INFO, "heartbeat: initialized");
    return {};
}

expected<void, Error> HeartbeatWorker::start() {
    if (state_ != SubsystemState::INITIALIZED)
        return unexpected<Error>(Error{ErrorCode::NOT_INITIALIZED,
                                       "heartbeat: not initialized"});
    if (running_.exchange(true))
        return unexpected<Error>(Error{ErrorCode::ALREADY_RUNNING,
                                       "heartbeat: already running"});
    state_ = SubsystemState::RUNNING;
    thread_ = std::thread(&HeartbeatWorker::worker_loop, this);
    logger_.log(LogLevel::INFO, "heartbeat: started (interval "
                + std::to_string(interval_ms_) + "ms)");
    return {};
}

void HeartbeatWorker::stop() {
    if (!running_.exchange(false)) return;
    cv_.notify_all();
    if (thread_.joinable()) thread_.join();
    state_ = SubsystemState::STOPPED;
    logger_.log(LogLevel::INFO, "heartbeat: stopped");
}

void HeartbeatWorker::worker_loop() {
    while (running_.load()) {
        SystemMetrics m = source_.sample();
        bus_.publish(MetricsEvent{m});

        std::ostringstream ss;
        ss << std::fixed << std::setprecision(1)
           << "Heartbeat: CPU " << m.cpu_usage_percent << "% | "
           << "Uptime " << static_cast<uint64_t>(m.uptime_seconds) << "s | "
           << "Mem Avail " << (m.mem_available_kb / 1024) << "MB / "
           << (m.mem_total_kb / 1024) << "MB";
        logger_.log(LogLevel::INFO, ss.str());

        std::unique_lock<std::mutex> lock(cv_mtx_);
        cv_.wait_for(lock, std::chrono::milliseconds(interval_ms_),
                     [this] { return !running_.load(); });
    }
}

} // namespace visiond
