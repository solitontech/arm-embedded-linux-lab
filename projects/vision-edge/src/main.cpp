#include "visiond/config.hpp"
#include "visiond/heartbeat.hpp"
#include "visiond/logger.hpp"
#include "visiond/state.hpp"

#include <csignal>
#include <condition_variable>
#include <iostream>
#include <mutex>
#include <unistd.h>

namespace {

std::condition_variable g_shutdown_cv;
std::mutex g_shutdown_mtx;
volatile std::sig_atomic_t g_signal_received = 0;

void posix_signal_handler(int sig) {
    g_signal_received = sig;
    visiond::StateManager::instance().set_state(visiond::DaemonState::STOPPING);
    g_shutdown_cv.notify_all();
}

void setup_signal_handlers() {
    struct sigaction sa{};
    sa.sa_handler = posix_signal_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0; // Do not use SA_RESTART so blocking syscalls interrupt cleanly

    sigaction(SIGINT,  &sa, nullptr);
    sigaction(SIGTERM, &sa, nullptr);
    sigaction(SIGHUP,  &sa, nullptr);
}

void print_banner() {
    std::cout << "\033[1;36m"
              << "====================================================================\n"
              << "       VisionEdge Industrial In-Line Inspection & Safety Gateway     \n"
              << "       Flagship Platform Daemon (visiond v0.1.0)                    \n"
              << "       Hardware: Raspberry Pi 4 (BCM2711 / Quad Cortex-A72 / AArch64)\n"
              << "====================================================================\n"
              << "\033[0m" << std::endl;
}

} // anonymous namespace

int main(int argc, char* argv[]) {
    // 1. Parse command-line configuration
    visiond::DaemonConfig config = visiond::DaemonConfig::parse_args(argc, argv);

    if (config.show_help) {
        visiond::DaemonConfig::print_usage(argv[0]);
        return 0;
    }

    if (config.show_version) {
        std::cout << "visiond version 0.1.0 (Phase 1 Baseline)\n"
                  << "Target: ARM Cortex-A72 / AArch64 (Linux)\n"
                  << "Build Standard: C++20\n";
        return 0;
    }

    // 2. Configure logging
    visiond::Logger::instance().set_level(config.log_level);
    if (!config.log_file.empty()) {
        if (!visiond::Logger::instance().set_log_file(config.log_file)) {
            std::cerr << "Warning: Could not open log file: " << config.log_file << "\n";
        }
    }

    // 3. Daemonize if requested
    if (config.daemon_mode) {
        LOG_INFO("Daemonizing vision-edge process...");
        if (daemon(0, 0) < 0) {
            LOG_ERROR("daemon() syscall failed");
            return 1;
        }
    }

    print_banner();

    // 4. Update lifecycle state to INITIALIZING
    auto& state_mgr = visiond::StateManager::instance();
    state_mgr.set_state(visiond::DaemonState::INITIALIZING);
    LOG_INFO("State transition -> INITIALIZING");

    // 5. Setup POSIX signal handlers
    setup_signal_handlers();
    LOG_INFO("Registered POSIX signal handlers (SIGINT, SIGTERM, SIGHUP)");

    // 6. Start Heartbeat Telemetry Worker
    visiond::HeartbeatWorker heartbeat(config.heartbeat_interval_ms);
    heartbeat.start();

    // 7. Transition to RUNNING
    state_mgr.set_state(visiond::DaemonState::RUNNING);
    LOG_INFO("State transition -> RUNNING");
    LOG_INFO("Gateway active. Supervisory thread entering wait state.");

    // 8. Main supervisory loop: wait for shutdown signal
    {
        std::unique_lock<std::mutex> lock(g_shutdown_mtx);
        g_shutdown_cv.wait(lock, [&state_mgr] {
            return !state_mgr.is_running();
        });
    }

    // 9. Graceful shutdown sequence
    int sig = g_signal_received;
    LOG_WARN("Shutdown sequence triggered by signal: " + std::to_string(sig));

    LOG_INFO("Stopping background heartbeat telemetry worker...");
    heartbeat.stop();

    state_mgr.set_state(visiond::DaemonState::TERMINATED);
    LOG_INFO("State transition -> TERMINATED");
    LOG_INFO("VisionEdge daemon shutdown cleanly. Exit 0.");

    return 0;
}
