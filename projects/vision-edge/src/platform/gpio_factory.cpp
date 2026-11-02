#include "visiond/platform/gpio_factory.hpp"

namespace visiond {

std::unique_ptr<IGpioController> make_bcm2711_gpio(ILogger& logger);

std::unique_ptr<IGpioController> make_gpio(GpioBackend backend, ILogger& logger) {
    switch (backend) {
        case GpioBackend::BCM2711: return make_bcm2711_gpio(logger);
    }
    return nullptr;
}

} // namespace visiond
