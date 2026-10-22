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
    bool        daemon_mode{false};
    bool        show_version{false};
    bool        show_help{false};

    static DaemonConfig parse(int argc, char* argv[]);
    static void print_usage(const char* prog_name);
};

} // namespace visiond
