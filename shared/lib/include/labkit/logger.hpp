#pragma once
#include <string_view>

namespace labkit {

enum class LogLevel { DEBUG, INFO, WARN, ERROR };

class ILogger {
public:
    virtual ~ILogger() = default;
    virtual void log(LogLevel level, std::string_view msg) = 0;
    virtual void set_level(LogLevel level) = 0;
};

} // namespace labkit
