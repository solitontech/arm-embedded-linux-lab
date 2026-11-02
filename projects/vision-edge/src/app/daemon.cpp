#include "visiond/app/daemon.hpp"
#include <labkit/term.hpp>
#include <condition_variable>
#include <csignal>
#include <iostream>
#include <mutex>
#include <string>

namespace {

std::condition_variable g_shutdown_cv;
std::mutex g_shutdown_mtx;
volatile std::sig_atomic_t g_shutdown_requested = 0;

void signal_handler(int /*sig*/) {
    g_shutdown_requested = 1;
    g_shutdown_cv.notify_all();
}

} // anonymous namespace

namespace visiond {

DaemonOrchestrator::DaemonOrchestrator(ILogger& logger, const DaemonConfig& config)
    : logger_(logger), config_(config) {}

void DaemonOrchestrator::add(std::unique_ptr<ISubsystem> subsystem) {
    subsystems_.push_back(std::move(subsystem));
}

void DaemonOrchestrator::setup_signal_handlers() {
    struct sigaction sa{};
    sa.sa_handler = signal_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0;
    sigaction(SIGINT,  &sa, nullptr);
    sigaction(SIGTERM, &sa, nullptr);
}

void DaemonOrchestrator::wait_for_shutdown() {
    std::unique_lock<std::mutex> lock(g_shutdown_mtx);
    g_shutdown_cv.wait(lock, [] { return g_shutdown_requested != 0; });
}

int DaemonOrchestrator::run() {
    labkit::term::banner(std::cout, {
        "VisionEdge Industrial In-Line Inspection & Safety Gateway",
        "Flagship Platform Daemon (visiond v" VISIOND_VERSION ")",
        "Hardware: Raspberry Pi 4 (BCM2711 / Quad Cortex-A72 / AArch64)"
    });
    std::cout << '\n';

    setup_signal_handlers();
    logger_.log(LogLevel::INFO,
                "Registered POSIX signal handlers (SIGINT, SIGTERM)");

    // Init all subsystems in registration order
    logger_.log(LogLevel::INFO, "INITIALIZING subsystems...");
    for (auto& ss : subsystems_) {
        auto res = ss->init();
        if (!res) {
            logger_.log(LogLevel::ERROR,
                        std::string("Failed to init subsystem '")
                        + std::string(ss->name()) + "': " + res.error().context);
            return 1;
        }
    }

    // Start all subsystems in registration order
    logger_.log(LogLevel::INFO, "STARTING subsystems...");
    for (auto& ss : subsystems_) {
        auto res = ss->start();
        if (!res) {
            logger_.log(LogLevel::ERROR,
                        std::string("Failed to start subsystem '")
                        + std::string(ss->name()) + "': " + res.error().context);
            // Stop already-started subsystems in reverse order
            for (auto it = subsystems_.rbegin(); it != subsystems_.rend(); ++it) {
                if ((*it)->state() == SubsystemState::RUNNING)
                    (*it)->stop();
            }
            return 1;
        }
    }

    logger_.log(LogLevel::INFO,
                "All subsystems RUNNING. Waiting for shutdown signal...");

    wait_for_shutdown();

    // Stop all subsystems in reverse registration order
    logger_.log(LogLevel::WARN, "Shutdown signal received. STOPPING subsystems...");
    for (auto it = subsystems_.rbegin(); it != subsystems_.rend(); ++it)
        (*it)->stop();

    logger_.log(LogLevel::INFO, "All subsystems TERMINATED. Clean exit.");
    return 0;
}

} // namespace visiond
