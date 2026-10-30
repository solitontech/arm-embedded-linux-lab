#pragma once
#include <labkit/event.hpp>
#include "visiond/core/events.hpp"
#include <mutex>
#include <string>

namespace visiond {
using labkit::EventBus;

class MjpegStream {
public:
    void register_events(EventBus& bus);
    void* state_{nullptr};   // points to SharedState (set by WebServer::init)

private:
    void on_frame(const FrameEvent& event);
};

class WsTelemetry {
public:
    void register_events(EventBus& bus);
    void* state_{nullptr};   // points to SharedState (set by WebServer::init)

private:
    void on_metrics(const MetricsEvent& event);
    void on_trip(const TripEvent& event);

    std::mutex   mtx_;
    float        last_cpu_{0.0f};
    float        last_mem_pct_{0.0f};
    bool         last_armed_{false};
    bool         last_tripped_{false};
    uint32_t     last_trip_count_{0};
    uint32_t     last_anomaly_{0};
};

} // namespace visiond
