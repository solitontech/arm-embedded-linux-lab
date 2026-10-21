#include "visiond/heartbeat.hpp"
#include "visiond/logger.hpp"
#include <fstream>
#include <sstream>
#include <iomanip>

namespace visiond {

HeartbeatWorker::HeartbeatWorker(uint32_t interval_ms)
    : interval_ms_(interval_ms) {}

HeartbeatWorker::~HeartbeatWorker() {
    stop();
}

void HeartbeatWorker::start() {
    if (running_.exchange(true)) {
        return; // Already running
    }
    thread_ = std::thread(&HeartbeatWorker::worker_loop, this);
}

void HeartbeatWorker::stop() {
    if (!running_.exchange(false)) {
        return;
    }
    cv_.notify_all();
    if (thread_.joinable()) {
        thread_.join();
    }
}

SystemMetrics HeartbeatWorker::get_latest_metrics() const {
    std::lock_guard<std::mutex> lock(metrics_mtx_);
    return latest_metrics_;
}

void HeartbeatWorker::worker_loop() {
    LOG_INFO("Heartbeat telemetry worker thread started (interval: " +
             std::to_string(interval_ms_) + "ms)");

    while (running_.load()) {
        SystemMetrics metrics = sample_metrics();

        {
            std::lock_guard<std::mutex> lock(metrics_mtx_);
            latest_metrics_ = metrics;
        }

        std::ostringstream ss;
        ss << std::fixed << std::setprecision(1)
           << "Heartbeat: CPU " << metrics.cpu_usage_percent << "% | "
           << "Uptime " << static_cast<uint64_t>(metrics.uptime_seconds) << "s | "
           << "Mem Avail " << (metrics.mem_available_kb / 1024) << "MB / "
           << (metrics.mem_total_kb / 1024) << "MB";

        LOG_INFO(ss.str());

        std::unique_lock<std::mutex> lock(cv_mtx_);
        cv_.wait_for(lock, std::chrono::milliseconds(interval_ms_), [this] {
            return !running_.load();
        });
    }

    LOG_INFO("Heartbeat telemetry worker thread stopped.");
}

SystemMetrics HeartbeatWorker::sample_metrics() {
    SystemMetrics metrics{};

    // 1. Sample system uptime from /proc/uptime
    std::ifstream uptime_file("/proc/uptime");
    if (uptime_file.is_open()) {
        uptime_file >> metrics.uptime_seconds;
    }

    // 2. Sample CPU usage from /proc/stat
    std::ifstream stat_file("/proc/stat");
    if (stat_file.is_open()) {
        std::string cpu_label;
        uint64_t user = 0, nice = 0, system = 0, idle = 0, iowait = 0, irq = 0, softirq = 0, steal = 0;
        stat_file >> cpu_label >> user >> nice >> system >> idle >> iowait >> irq >> softirq >> steal;

        if (first_cpu_sample_) {
            prev_user_ = user;
            prev_nice_ = nice;
            prev_system_ = system;
            prev_idle_ = idle;
            prev_iowait_ = iowait;
            prev_irq_ = irq;
            prev_softirq_ = softirq;
            prev_steal_ = steal;
            first_cpu_sample_ = false;
            metrics.cpu_usage_percent = 0.0f;
        } else {
            uint64_t prev_idle_all = prev_idle_ + prev_iowait_;
            uint64_t idle_all = idle + iowait;

            uint64_t prev_non_idle = prev_user_ + prev_nice_ + prev_system_ + prev_irq_ + prev_softirq_ + prev_steal_;
            uint64_t non_idle = user + nice + system + irq + softirq + steal;

            uint64_t prev_total = prev_idle_all + prev_non_idle;
            uint64_t total = idle_all + non_idle;

            uint64_t total_diff = total - prev_total;
            uint64_t idle_diff = idle_all - prev_idle_all;

            if (total_diff > 0) {
                metrics.cpu_usage_percent = static_cast<float>(total_diff - idle_diff) * 100.0f / static_cast<float>(total_diff);
            }

            prev_user_ = user;
            prev_nice_ = nice;
            prev_system_ = system;
            prev_idle_ = idle;
            prev_iowait_ = iowait;
            prev_irq_ = irq;
            prev_softirq_ = softirq;
            prev_steal_ = steal;
        }
    }

    // 3. Sample Memory from /proc/meminfo
    std::ifstream meminfo_file("/proc/meminfo");
    if (meminfo_file.is_open()) {
        std::string line;
        while (std::getline(meminfo_file, line)) {
            if (line.rfind("MemTotal:", 0) == 0) {
                std::istringstream iss(line.substr(9));
                iss >> metrics.mem_total_kb;
            } else if (line.rfind("MemFree:", 0) == 0) {
                std::istringstream iss(line.substr(8));
                iss >> metrics.mem_free_kb;
            } else if (line.rfind("MemAvailable:", 0) == 0) {
                std::istringstream iss(line.substr(13));
                iss >> metrics.mem_available_kb;
            }
        }
    }

    return metrics;
}

} // namespace visiond
