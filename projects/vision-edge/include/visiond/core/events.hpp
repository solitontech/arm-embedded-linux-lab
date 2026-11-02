#pragma once
#include "visiond/pipeline/frame.hpp"
#include "visiond/telemetry/metrics.hpp"
#include <cstdint>

namespace visiond {

// All EventBus event types in one place.
// Producers publish these; consumers subscribe via EventBus::subscribe<T>().

// Published by HeartbeatWorker at the heartbeat interval
struct MetricsEvent {
    SystemMetrics metrics;
};

// Published by CaptureSubsystem after each processed frame
struct FrameEvent {
    const FrameDescriptor* frame;   // points to the pipeline's descriptor (not owned)
};

// Published by TripController when safety state changes
struct TripEvent {
    bool     armed;
    bool     tripped;
    uint32_t trip_count;
};

} // namespace visiond
