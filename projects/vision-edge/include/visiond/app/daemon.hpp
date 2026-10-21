#pragma once
#include "visiond/core/lifecycle.hpp"
#include "visiond/core/logger.hpp"
#include "visiond/core/config.hpp"
#include <memory>
#include <vector>

namespace visiond {

class DaemonOrchestrator {
public:
    DaemonOrchestrator(ILogger& logger, const DaemonConfig& config);

    void add(std::unique_ptr<ISubsystem> subsystem);

    // init all -> start all -> wait for signal -> stop all (reverse order)
    int run();

private:
    void setup_signal_handlers();
    void wait_for_shutdown();

    ILogger& logger_;
    DaemonConfig config_;
    std::vector<std::unique_ptr<ISubsystem>> subsystems_;
};

} // namespace visiond
