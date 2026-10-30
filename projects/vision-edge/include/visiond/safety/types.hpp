#pragma once
#include <cstdint>

namespace visiond {

struct SafetyStatus {
    bool     armed{false};
    bool     tripped{false};
    uint64_t trip_timestamp_ns{0};
    uint32_t trip_count{0};
};

struct TripPolicy {
    uint32_t anomaly_threshold{500};       // Pixel count to trigger trip
    uint32_t consecutive_frames{3};        // Must exceed threshold N frames in a row
};

} // namespace visiond
