#pragma once
#include <labkit/types.hpp>
#include <labkit/expected.hpp>
#include <cstdint>

namespace visiond {
using labkit::expected;
using labkit::unexpected;
using labkit::Error;
using labkit::ErrorCode;

enum class PinMode  { INPUT, OUTPUT };
enum class PinLevel { LOW, HIGH };
enum class PullMode { NONE, UP, DOWN };

class IGpioController {
public:
    virtual ~IGpioController() = default;
    virtual expected<void, Error> init()                               = 0;
    virtual expected<void, Error> set_mode(uint8_t pin, PinMode mode)  = 0;
    virtual expected<void, Error> set_pull(uint8_t pin, PullMode pull) = 0;
    virtual expected<void, Error> write(uint8_t pin, PinLevel level)   = 0;
    virtual expected<PinLevel, Error> read(uint8_t pin)                = 0;
};

} // namespace visiond
