#include "visiond/web/stream.hpp"
#include "visiond/web/shared_state.hpp"
#include <cstdio>

namespace visiond {

void WsTelemetry::register_events(EventBus& bus) {
    bus.subscribe<MetricsEvent>([this](const MetricsEvent& e) { on_metrics(e); });
    bus.subscribe<TripEvent>([this](const TripEvent& e) { on_trip(e); });
    bus.subscribe<FrameEvent>([this](const FrameEvent& e) {
        if (!e.frame) return;
        std::lock_guard<std::mutex> lock(mtx_);
        last_anomaly_ = e.frame->anomaly_count;
    });
}

void WsTelemetry::on_metrics(const MetricsEvent& event) {
    float cpu = event.metrics.cpu_usage_percent;
    float mem_pct = 0.0f;
    if (event.metrics.mem_total_kb > 0)
        mem_pct = 100.0f * (1.0f - float(event.metrics.mem_available_kb) /
                                    float(event.metrics.mem_total_kb));
    {
        std::lock_guard<std::mutex> lock(mtx_);
        last_cpu_ = cpu;
        last_mem_pct_ = mem_pct;
    }

    char buf[256];
    std::snprintf(buf, sizeof(buf),
        R"({"cpu":%.1f,"mem_pct":%.1f,"armed":%s,"tripped":%s,"trips":%u,"anomaly":%u})",
        cpu, mem_pct,
        last_armed_ ? "true" : "false",
        last_tripped_ ? "true" : "false",
        last_trip_count_, last_anomaly_);

    if (!state_) return;
    auto* s = static_cast<SharedState*>(state_);
    std::lock_guard<std::mutex> lock(s->metrics_mtx);
    s->latest_json = buf;
    s->metrics_ready = true;
}

void WsTelemetry::on_trip(const TripEvent& event) {
    std::lock_guard<std::mutex> lock(mtx_);
    last_armed_ = event.armed;
    last_tripped_ = event.tripped;
    last_trip_count_ = event.trip_count;
}

} // namespace visiond
