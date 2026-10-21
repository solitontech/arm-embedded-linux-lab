#pragma once
#include "visiond/core/logger.hpp"
#include <cstdint>

namespace visiond {

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

class ProcfsMetricsSource : public IMetricsSource {
public:
    explicit ProcfsMetricsSource(ILogger& logger);
    SystemMetrics sample() override;

private:
    ILogger& logger_;
    uint64_t prev_idle_{0};
    uint64_t prev_total_{0};
    bool first_sample_{true};
};

} // namespace visiond
