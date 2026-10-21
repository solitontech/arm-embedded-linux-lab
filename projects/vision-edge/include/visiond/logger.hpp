#pragma once

#include <chrono>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <mutex>
#include <sstream>
#include <string>
#include <string_view>

namespace visiond {

enum class LogLevel {
    DEBUG = 0,
    INFO  = 1,
    WARN  = 2,
    ERROR = 3
};

class Logger {
public:
    static Logger& instance() {
        static Logger logger;
        return logger;
    }

    void set_level(LogLevel level) {
        std::lock_guard<std::mutex> lock(mtx_);
        current_level_ = level;
    }

    LogLevel get_level() const {
        return current_level_;
    }

    bool set_log_file(const std::string& path) {
        std::lock_guard<std::mutex> lock(mtx_);
        if (file_stream_.is_open()) {
            file_stream_.close();
        }
        file_stream_.open(path, std::ios::out | std::ios::app);
        return file_stream_.is_open();
    }

    void log(LogLevel level, std::string_view msg) {
        if (level < current_level_) {
            return;
        }

        auto now = std::chrono::system_clock::now();
        auto in_time_t = std::chrono::system_clock::to_time_t(now);
        auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(now.time_since_epoch()) % 1000;

        std::tm tm_buf{};
        localtime_r(&in_time_t, &tm_buf);

        std::ostringstream ss_time;
        ss_time << std::put_time(&tm_buf, "%Y-%m-%d %H:%M:%S")
                << '.' << std::setfill('0') << std::setw(3) << ms.count();

        const char* level_tag = "INFO ";
        const char* color_code = "\033[32m";

        switch (level) {
            case LogLevel::DEBUG:
                level_tag = "DEBUG";
                color_code = "\033[36m"; // Cyan
                break;
            case LogLevel::INFO:
                level_tag = "INFO ";
                color_code = "\033[32m"; // Green
                break;
            case LogLevel::WARN:
                level_tag = "WARN ";
                color_code = "\033[33m"; // Yellow
                break;
            case LogLevel::ERROR:
                level_tag = "ERROR";
                color_code = "\033[31m"; // Red
                break;
        }

        std::lock_guard<std::mutex> lock(mtx_);

        // Terminal output with ANSI coloring
        std::cout << color_code << "[" << level_tag << "]\033[0m "
                  << "[" << ss_time.str() << "] "
                  << msg << std::endl;

        // Plaintext file output if configured
        if (file_stream_.is_open()) {
            file_stream_ << "[" << level_tag << "] "
                         << "[" << ss_time.str() << "] "
                         << msg << "\n";
            file_stream_.flush();
        }
    }

private:
    Logger() : current_level_(LogLevel::INFO) {}
    ~Logger() {
        if (file_stream_.is_open()) {
            file_stream_.close();
        }
    }

    Logger(const Logger&) = delete;
    Logger& operator=(const Logger&) = delete;

    LogLevel current_level_{LogLevel::INFO};
    std::ofstream file_stream_;
    std::mutex mtx_;
};

#define LOG_DEBUG(msg) ::visiond::Logger::instance().log(::visiond::LogLevel::DEBUG, (msg))
#define LOG_INFO(msg)  ::visiond::Logger::instance().log(::visiond::LogLevel::INFO,  (msg))
#define LOG_WARN(msg)  ::visiond::Logger::instance().log(::visiond::LogLevel::WARN,  (msg))
#define LOG_ERROR(msg) ::visiond::Logger::instance().log(::visiond::LogLevel::ERROR, (msg))

} // namespace visiond
