#pragma once
#include <labkit/logger.hpp>
#include <cstdint>
#include <string>

namespace visiond {
using labkit::LogLevel;

struct DaemonConfig {
    LogLevel    log_level{LogLevel::INFO};
    uint32_t    heartbeat_interval_ms{1000};
    uint16_t    web_port{8080};
    std::string log_file;
    std::string ntp_server;          // NTP server for clock sync on boot (empty = skip)
    bool        daemon_mode{false};
    bool        show_version{false};
    bool        show_help{false};

    // Core affinity for SMP thread pinning (Phase 4)
    int8_t      core_capture{1};   // V4L2 capture + pipeline thread
    int8_t      core_simd_0{2};    // NEON worker 0 (top half frame)
    int8_t      core_simd_1{3};    // NEON worker 1 (bottom half frame)

    // Camera configuration
    uint32_t    cam_width{1920};
    uint32_t    cam_height{1080};
    uint32_t    cam_fps{30};
    uint8_t     diff_threshold{25};  // Pixel diff threshold for anomaly detection

    static DaemonConfig parse(int argc, char* argv[]);
    static void print_usage(const char* prog_name);
    static void print_version();
};

} // namespace visiond
