#include "visiond/app/config.hpp"
#include <cstdlib>
#include <iostream>
#include <string_view>

namespace visiond {

void DaemonConfig::print_version() {
    std::cout << "visiond " << VISIOND_VERSION << "\n";
}

void DaemonConfig::print_usage(const char* prog_name) {
    std::cout << "Usage: " << prog_name << " [options]\n\n"
              << "VisionEdge Industrial In-Line Inspection & Safety Gateway\n\n"
              << "Options:\n"
              << "  -h, --help                 Show this help message and exit\n"
              << "  -v, --version              Show version information\n"
              << "  -d, --daemon               Run in background daemon mode\n"
              << "  -i, --interval <ms>        Telemetry heartbeat interval (default: 1000)\n"
              << "  -p, --port <port>          Embedded web server port (default: 8080)\n"
              << "  -l, --log-level <level>    Log level: debug|info|warn|error (default: info)\n"
              << "  -f, --log-file <path>      Log file destination path\n\n";
}

DaemonConfig DaemonConfig::parse(int argc, char* argv[]) {
    DaemonConfig config;
    for (int i = 1; i < argc; ++i) {
        std::string_view arg = argv[i];
        if (arg == "-h" || arg == "--help") {
            config.show_help = true; return config;
        } else if (arg == "-v" || arg == "--version") {
            config.show_version = true; return config;
        } else if (arg == "-d" || arg == "--daemon") {
            config.daemon_mode = true;
        } else if ((arg == "-i" || arg == "--interval") && i + 1 < argc) {
            config.heartbeat_interval_ms =
                static_cast<uint32_t>(std::strtoul(argv[++i], nullptr, 10));
            if (config.heartbeat_interval_ms < 100)
                config.heartbeat_interval_ms = 100;
        } else if ((arg == "-p" || arg == "--port") && i + 1 < argc) {
            config.web_port =
                static_cast<uint16_t>(std::strtoul(argv[++i], nullptr, 10));
        } else if ((arg == "-l" || arg == "--log-level") && i + 1 < argc) {
            std::string_view lv = argv[++i];
            if (lv == "debug" || lv == "DEBUG") config.log_level = LogLevel::DEBUG;
            else if (lv == "info"  || lv == "INFO")  config.log_level = LogLevel::INFO;
            else if (lv == "warn"  || lv == "WARN")  config.log_level = LogLevel::WARN;
            else if (lv == "error" || lv == "ERROR") config.log_level = LogLevel::ERROR;
        } else if ((arg == "-f" || arg == "--log-file") && i + 1 < argc) {
            config.log_file = argv[++i];
        } else {
            std::cerr << "Unknown option: " << arg << "\n";
            config.show_help = true; return config;
        }
    }
    return config;
}

} // namespace visiond
