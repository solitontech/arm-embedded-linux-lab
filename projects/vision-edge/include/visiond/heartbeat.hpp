#pragma once

#include <atomic>
#include <condition_variable>
#include <mutex>
#include <string>
#include <thread>

namespace visiond {

struct SystemMetrics {
    float cpu_usage_percent{0.0f};
    double uptime_seconds{0.0};
    uint64_t mem_total_kb{0};
    uint64_t mem_free_kb{0};
    uint64_t mem_available_kb{0};
};

class HeartbeatWorker {
public:
    explicit HeartbeatWorker(uint32_t interval_ms = 1000);
    ~HeartbeatWorker();

    void start();
    void stop();

    SystemMetrics get_latest_metrics() const;

private:
    void worker_loop();
    SystemMetrics sample_metrics();

    uint32_t interval_ms_;
    std::atomic<bool> running_{false};
    std::thread thread_;
    mutable std::mutex metrics_mtx_;
    SystemMetrics latest_metrics_{};
    std::condition_variable cv_;
    std::mutex cv_mtx_;

    // CPU sampling state for /proc/stat
    uint64_t prev_user_{0};
    uint64_t prev_nice_{0};
    uint64_t prev_system_{0};
    uint64_t prev_idle_{0};
    uint64_t prev_iowait_{0};
    uint64_t prev_irq_{0};
    uint64_t prev_softirq_{0};
    uint64_t prev_steal_{0};
    bool first_cpu_sample_{true};
};

} // namespace visiond
