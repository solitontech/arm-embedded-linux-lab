#pragma once
#include "visiond/platform/gpio.hpp"
#include <labkit/logger.hpp>
#include <memory>

namespace visiond {
using labkit::ILogger;

enum class GpioBackend {
    BCM2711,        // Phase 2: userspace MMIO via /dev/mem
    // KERNEL,      // Phase 3: kernel driver via /dev/visiond-gpio
};

std::unique_ptr<IGpioController> make_gpio(GpioBackend backend, ILogger& logger);

} // namespace visiond
