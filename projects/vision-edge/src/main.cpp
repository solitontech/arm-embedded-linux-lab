#include "visiond/core/config.hpp"
#include "visiond/core/logger.hpp"
#include "visiond/core/event.hpp"
#include "visiond/telemetry/metrics.hpp"
#include "visiond/telemetry/heartbeat.hpp"
#include "visiond/app/daemon.hpp"
#include <iomanip>
#include <iostream>
#include <sstream>
#include <unistd.h>

int main(int argc, char* argv[]) {
    auto config = visiond::DaemonConfig::parse(argc, argv);
    if (config.show_help)    { visiond::DaemonConfig::print_usage(argv[0]); return 0; }
    if (config.show_version) { std::cout << "visiond 0.1.0\n"; return 0; }

    // Composition root: create shared dependencies
    visiond::SpdlogLogger logger("visiond");
    logger.set_level(config.log_level);
    if (!config.log_file.empty())
        logger.add_file_sink(config.log_file);

    if (config.daemon_mode) {
        logger.log(visiond::LogLevel::INFO, "Daemonizing...");
        if (daemon(0, 0) < 0) {
            logger.log(visiond::LogLevel::ERROR, "daemon() syscall failed");
            return 1;
        }
    }

    visiond::EventBus event_bus;
    visiond::ProcfsMetricsSource metrics_source(logger);

    // Subscribe to MetricsEvents for logging
    event_bus.subscribe<visiond::MetricsEvent>(
        [&logger](const visiond::MetricsEvent& e) {
            std::ostringstream ss;
            ss << std::fixed << std::setprecision(1)
               << "[event] MetricsEvent: CPU " << e.metrics.cpu_usage_percent
               << "%, Mem " << (e.metrics.mem_available_kb / 1024)
               << "/" << (e.metrics.mem_total_kb / 1024) << " MB";
            logger.log(visiond::LogLevel::DEBUG, ss.str());
        });

    // Build orchestrator and register subsystems
    visiond::DaemonOrchestrator daemon(logger, config);
    daemon.add(std::make_unique<visiond::HeartbeatWorker>(
        logger, metrics_source, event_bus, config.heartbeat_interval_ms));

    return daemon.run();
}
