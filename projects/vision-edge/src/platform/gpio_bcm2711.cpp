#include "visiond/platform/gpio.hpp"
#include "visiond/platform/mmio.hpp"
#include <labkit/logger.hpp>
#include <memory>
#include <optional>
#include <utility>

namespace visiond {
using labkit::ILogger;
using labkit::LogLevel;

namespace {
constexpr off_t  BCM2711_GPIO_BASE = 0xFE200000;
constexpr size_t GPIO_BLOCK_SIZE   = 4096;

// Register offsets as uint32_t word indices
constexpr uint32_t GPFSEL0   = 0x00 / 4;
constexpr uint32_t GPSET0    = 0x1C / 4;
constexpr uint32_t GPCLR0    = 0x28 / 4;
constexpr uint32_t GPLEV0    = 0x34 / 4;
constexpr uint32_t GPIO_PUP_PDN_CNTRL_REG0 = 0xE4 / 4;
constexpr uint8_t  MAX_GPIO_PIN = 57;
} // namespace

class Bcm2711GpioController : public IGpioController {
public:
    explicit Bcm2711GpioController(ILogger& logger) : logger_(logger) {}

    expected<void, Error> init() override {
        auto region = MmioRegion::create(BCM2711_GPIO_BASE, GPIO_BLOCK_SIZE);
        if (!region.has_value())
            return unexpected<Error>(region.error());

        mmio_.emplace(std::move(region.value()));
        regs_ = mmio_->as_u32();
        logger_.log(LogLevel::INFO, "BCM2711 GPIO mapped at PA 0xFE200000");
        return {};
    }

    expected<void, Error> set_mode(uint8_t pin, PinMode mode) override {
        if (pin > MAX_GPIO_PIN)
            return unexpected<Error>(Error{ErrorCode::INVALID_ARG, "Pin out of range"});

        uint32_t reg_index = GPFSEL0 + (pin / 10);
        uint32_t bit_shift = (pin % 10) * 3;

        uint32_t val = regs_[reg_index];
        val &= ~(0b111u << bit_shift);                    // Clear 3-bit field
        if (mode == PinMode::OUTPUT)
            val |= (0b001u << bit_shift);                  // 001 = output
        regs_[reg_index] = val;                            // INPUT = 000 (default)
        return {};
    }

    expected<void, Error> set_pull(uint8_t pin, PullMode pull) override {
        if (pin > MAX_GPIO_PIN)
            return unexpected<Error>(Error{ErrorCode::INVALID_ARG, "Pin out of range"});

        // BCM2711 uses GPIO_PUP_PDN registers (2 bits per pin, 16 pins per reg)
        uint32_t reg_index = GPIO_PUP_PDN_CNTRL_REG0 + (pin / 16);
        uint32_t bit_shift = (pin % 16) * 2;
        uint32_t pull_val = 0b00;  // NONE
        if (pull == PullMode::UP)   pull_val = 0b01;
        if (pull == PullMode::DOWN) pull_val = 0b10;

        uint32_t val = regs_[reg_index];
        val &= ~(0b11u << bit_shift);
        val |= (pull_val << bit_shift);
        regs_[reg_index] = val;
        return {};
    }

    expected<void, Error> write(uint8_t pin, PinLevel level) override {
        if (pin > MAX_GPIO_PIN)
            return unexpected<Error>(Error{ErrorCode::INVALID_ARG, "Pin out of range"});

        uint32_t bank = pin / 32;
        uint32_t bit  = pin % 32;

        if (level == PinLevel::HIGH)
            regs_[GPSET0 + bank] = (1u << bit);   // Write-1-to-set
        else
            regs_[GPCLR0 + bank] = (1u << bit);   // Write-1-to-clear

        return {};
    }

    expected<PinLevel, Error> read(uint8_t pin) override {
        if (pin > MAX_GPIO_PIN)
            return unexpected<Error>(Error{ErrorCode::INVALID_ARG, "Pin out of range"});

        uint32_t bank = pin / 32;
        uint32_t bit  = pin % 32;
        uint32_t level = regs_[GPLEV0 + bank];

        return (level & (1u << bit)) ? PinLevel::HIGH : PinLevel::LOW;
    }

private:
    ILogger&    logger_;
    std::optional<MmioRegion> mmio_;
    volatile uint32_t* regs_{nullptr};
};

// Factory function — allows main.cpp to create without seeing the class definition
std::unique_ptr<IGpioController> make_bcm2711_gpio(ILogger& logger) {
    return std::make_unique<Bcm2711GpioController>(logger);
}

} // namespace visiond
