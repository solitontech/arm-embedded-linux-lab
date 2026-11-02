#include "visiond/app/config.hpp"
#include "visiond/telemetry/metrics.hpp"
#include "visiond/telemetry/heartbeat.hpp"
#include "visiond/platform/gpio_subsystem.hpp"
#include "visiond/platform/gpio_factory.hpp"
#include "visiond/platform/camera.hpp"
#include "visiond/safety/driver_client.hpp"
#include "visiond/safety/trip_controller.hpp"
#include "visiond/pipeline/simd_engine.hpp"
#include "visiond/pipeline/ring_buffer.hpp"
#include "visiond/pipeline/capture_subsystem.hpp"
#include "visiond/web/server.hpp"
#include "visiond/app/daemon.hpp"
#include <labkit/spdlog_logger.hpp>   // heavy — only in composition root
#include <iomanip>
#include <sstream>
#include <unistd.h>
#include <cstdlib>  // system()

int main(int argc, char* argv[]) {
    auto config = visiond::DaemonConfig::parse(argc, argv);
    if (config.show_help)    { visiond::DaemonConfig::print_usage(argv[0]); return 0; }
    if (config.show_version) { visiond::DaemonConfig::print_version();     return 0; }

    // Composition root: create shared dependencies
    labkit::SpdlogLogger logger("visiond");
    logger.set_level(config.log_level);
    if (!config.log_file.empty())
        logger.add_file_sink(config.log_file);

    // Sync system clock via NTP on embedded targets (no RTC — clock starts at epoch on boot).
    // Uses the NTP server exported by the Docker dev container on the host.
    if (!config.ntp_server.empty()) {
        logger.log(labkit::LogLevel::INFO, "Syncing clock from NTP server: " + config.ntp_server);
        std::string cmd = "ntpd -q -p " + config.ntp_server + " 2>/dev/null || true";
        if (::system(cmd.c_str()) != 0) {
            logger.log(labkit::LogLevel::WARN, "NTP sync failed — timestamps may show epoch (1970)");
        }
    }

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

    // Trip controller with default policy
    visiond::TripController trip_controller(safety_driver, logger);

    // Select camera and SIMD implementations at compile time
#ifdef __aarch64__
    std::unique_ptr<visiond::ICameraSource> camera;
    if (::access("/dev/video0", F_OK) == 0) {
        camera = visiond::make_v4l2_camera(logger);
    } else {
        logger.log(visiond::LogLevel::WARN, "/dev/video0 not found; falling back to synthetic camera");
        camera = visiond::make_synthetic_camera(logger);
    }
    auto simd   = visiond::make_neon_simd_engine();
#else
    auto camera = visiond::make_synthetic_camera(logger);
    auto simd   = visiond::make_scalar_simd_engine();
#endif

    // Shared ring buffer: capture thread publishes, web stream consumes (Phase 5)
    visiond::LocklessTripleBuffer<visiond::FrameDescriptor> ring_buffer;

    visiond::CameraConfig cam_cfg;
    cam_cfg.width  = config.cam_width;
    cam_cfg.height = config.cam_height;
    cam_cfg.fps    = config.cam_fps;

    // Build orchestrator and register subsystems
    visiond::DaemonOrchestrator daemon(logger, config);

    daemon.add(std::make_unique<visiond::HeartbeatWorker>(
        logger, metrics_source, event_bus, config.heartbeat_interval_ms));

    // GPIO MMIO requires /dev/mem — only meaningful on RPi4
#ifdef __aarch64__
    daemon.add(std::make_unique<visiond::GpioSubsystem>(
        visiond::make_gpio(visiond::GpioBackend::BCM2711, logger)));
#endif

    daemon.add(std::make_unique<visiond::CaptureSubsystem>(
        logger, std::move(camera), std::move(simd),
        ring_buffer, trip_controller, event_bus, cam_cfg,
        config.diff_threshold, config.core_capture));

    // Phase 5: embedded web dashboard
    daemon.add(std::make_unique<visiond::WebServer>(logger, event_bus, config));

    return daemon.run();
}
