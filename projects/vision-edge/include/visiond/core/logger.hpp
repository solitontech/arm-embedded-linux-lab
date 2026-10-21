#pragma once
#include <fstream>
#include <mutex>
#include <string>
#include <string_view>

namespace visiond {

enum class LogLevel { DEBUG, INFO, WARN, ERROR };

class ILogger {
public:
    virtual ~ILogger() = default;
    virtual void log(LogLevel level, std::string_view msg) = 0;
    virtual void set_level(LogLevel level) = 0;
};

class ConsoleLogger : public ILogger {
public:
    void log(LogLevel level, std::string_view msg) override;
    void set_level(LogLevel level) override;
    bool set_log_file(const std::string& path);

private:
    LogLevel current_level_{LogLevel::INFO};
    std::mutex mtx_;
    std::ofstream file_stream_;
};

} // namespace visiond
