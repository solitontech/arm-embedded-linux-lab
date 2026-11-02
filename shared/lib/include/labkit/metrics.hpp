#pragma once
#include <cstdint>

namespace labkit {

struct SystemMetrics {
    float    cpu_usage_percent{0.0f};
    double   uptime_seconds{0.0};
    uint64_t mem_total_kb{0};
    uint64_t mem_free_kb{0};
    uint64_t mem_available_kb{0};
};

class IMetricsSource {
public:
    virtual ~IMetricsSource() = default;
    virtual SystemMetrics sample() = 0;
};

} // namespace labkit
