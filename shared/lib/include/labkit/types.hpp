#pragma once
#include <cstdint>
#include <string>

namespace labkit {

enum class ErrorCode : uint16_t {
    OK = 0,
    INVALID_ARG,
    IO_ERROR,
    DEVICE_NOT_FOUND,
    PERMISSION_DENIED,
    ALREADY_RUNNING,
    NOT_INITIALIZED,
    TIMEOUT,
};

struct Error {
    ErrorCode   code;
    std::string context;
};

} // namespace labkit
