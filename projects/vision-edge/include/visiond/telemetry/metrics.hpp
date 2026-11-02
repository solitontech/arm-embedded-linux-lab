#pragma once
#include <labkit/metrics.hpp>
#include <labkit/logger.hpp>

namespace visiond {
using labkit::SystemMetrics;
using labkit::IMetricsSource;
using labkit::ILogger;

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
