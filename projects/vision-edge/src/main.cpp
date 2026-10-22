#include "visiond/app/config.hpp"
#include "visiond/telemetry/metrics.hpp"
#include "visiond/telemetry/heartbeat.hpp"
#include "visiond/platform/gpio_subsystem.hpp"
#include "visiond/platform/gpio_factory.hpp"
#include "visiond/safety/driver_client.hpp"
#include "visiond/safety/trip_controller.hpp"
#include "visiond/app/daemon.hpp"
#include <labkit/spdlog_logger.hpp>   // heavy — only in composition root
#include <iomanip>
#include <sstream>
#include <unistd.h>

int main(int argc, char* argv[]) {
    auto config = visiond::DaemonConfig::parse(argc, argv);
    if (config.show_help)    { visiond::DaemonConfig::print_usage(argv[0]); return 0; }
    if (config.show_version) { visiond::DaemonConfig::print_version();     return 0; }

    // Composition root: create shared dependencies
    labkit::SpdlogLogger logger("visiond");
    logger.set_level(config.log_level);
    if (!config.log_file.empty())
        logger.add_file_sink(config.log_file);

    if (config.daemon_mode) {
        logger.log(labkit::LogLevel::INFO, "Daemonizing...");
        if (daemon(0, 0) < 0) {
            logger.log(labkit::LogLevel::ERROR, "daemon() syscall failed");
            return 1;
        }
    }

    labkit::EventBus event_bus;
    visiond::ProcfsMetricsSource metrics_source(logger);

    // Subscribe to MetricsEvents for logging
    event_bus.subscribe<visiond::MetricsEvent>(
        [&logger](const visiond::MetricsEvent& e) {
            std::ostringstream ss;
            ss << std::fixed << std::setprecision(1)
               << "[event] MetricsEvent: CPU " << e.metrics.cpu_usage_percent
               << "%, Mem " << (e.metrics.mem_available_kb / 1024)
               << "/" << (e.metrics.mem_total_kb / 1024) << " MB";
            logger.log(labkit::LogLevel::DEBUG, ss.str());
        });

    // Safety subsystem: kernel driver client
    visiond::DriverClient safety_driver(logger);
    auto open_result = safety_driver.open_device();
    if (!open_result.has_value()) {
        logger.log(labkit::LogLevel::WARN,
            "Safety driver unavailable: " + open_result.error().context);
        // Continue without safety — not fatal on host builds
    }

    // Trip controller with default policy (wired to SIMD pipeline in Phase 4)
    visiond::TripController trip_controller(safety_driver, logger);

    // Build orchestrator and register subsystems
    visiond::DaemonOrchestrator daemon(logger, config);

    daemon.add(std::make_unique<visiond::HeartbeatWorker>(
        logger, metrics_source, event_bus, config.heartbeat_interval_ms));

    daemon.add(std::make_unique<visiond::GpioSubsystem>(
        visiond::make_gpio(visiond::GpioBackend::BCM2711, logger)));

    return daemon.run();
}
