#include "visiond/telemetry/metrics.hpp"
#include <fstream>
#include <sstream>
#include <string>

namespace visiond {

ProcfsMetricsSource::ProcfsMetricsSource(ILogger& logger)
    : logger_(logger) {}

SystemMetrics ProcfsMetricsSource::sample() {
    SystemMetrics m{};

    // Uptime
    {
        std::ifstream f("/proc/uptime");
        if (f.is_open()) f >> m.uptime_seconds;
    }

    // CPU usage (delta-based)
    {
        std::ifstream f("/proc/stat");
        if (f.is_open()) {
            std::string label;
            uint64_t user, nice, system, idle, iowait, irq, softirq, steal;
            f >> label >> user >> nice >> system >> idle
              >> iowait >> irq >> softirq >> steal;

            uint64_t idle_all = idle + iowait;
            uint64_t total = user + nice + system + idle_all + irq + softirq + steal;

            if (first_sample_) {
                first_sample_ = false;
                m.cpu_usage_percent = 0.0f;
            } else {
                uint64_t total_d = total - prev_total_;
                uint64_t idle_d  = idle_all - prev_idle_;
                if (total_d > 0)
                    m.cpu_usage_percent =
                        static_cast<float>(total_d - idle_d) * 100.0f /
                        static_cast<float>(total_d);
            }
            prev_idle_  = idle_all;
            prev_total_ = total;
        }
    }

    // Memory
    {
        std::ifstream f("/proc/meminfo");
        if (f.is_open()) {
            std::string line;
            while (std::getline(f, line)) {
                if (line.rfind("MemTotal:", 0) == 0) {
                    std::istringstream iss(line.substr(9));
                    iss >> m.mem_total_kb;
                } else if (line.rfind("MemFree:", 0) == 0) {
                    std::istringstream iss(line.substr(8));
                    iss >> m.mem_free_kb;
                } else if (line.rfind("MemAvailable:", 0) == 0) {
                    std::istringstream iss(line.substr(13));
                    iss >> m.mem_available_kb;
                }
            }
        }
    }

    return m;
}

} // namespace visiond
