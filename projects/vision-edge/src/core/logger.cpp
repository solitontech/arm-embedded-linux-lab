#include "visiond/core/logger.hpp"
#include <chrono>
#include <iomanip>
#include <iostream>
#include <sstream>

namespace visiond {

void ConsoleLogger::set_level(LogLevel level) {
    std::lock_guard<std::mutex> lock(mtx_);
    current_level_ = level;
}

bool ConsoleLogger::set_log_file(const std::string& path) {
    std::lock_guard<std::mutex> lock(mtx_);
    if (file_stream_.is_open()) file_stream_.close();
    file_stream_.open(path, std::ios::out | std::ios::app);
    return file_stream_.is_open();
}

void ConsoleLogger::log(LogLevel level, std::string_view msg) {
    if (level < current_level_) return;

    auto now = std::chrono::system_clock::now();
    auto tt = std::chrono::system_clock::to_time_t(now);
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
                  now.time_since_epoch()) % 1000;

    std::tm tm_buf{};
    localtime_r(&tt, &tm_buf);

    std::ostringstream ts;
    ts << std::put_time(&tm_buf, "%Y-%m-%d %H:%M:%S")
       << '.' << std::setfill('0') << std::setw(3) << ms.count();

    const char* tag = "INFO ";
    const char* color = "\033[32m";
    switch (level) {
        case LogLevel::DEBUG: tag = "DEBUG"; color = "\033[36m"; break;
        case LogLevel::INFO:  tag = "INFO "; color = "\033[32m"; break;
        case LogLevel::WARN:  tag = "WARN "; color = "\033[33m"; break;
        case LogLevel::ERROR: tag = "ERROR"; color = "\033[31m"; break;
    }

    std::lock_guard<std::mutex> lock(mtx_);
    std::cout << color << "[" << tag << "]\033[0m [" << ts.str() << "] "
              << msg << std::endl;

    if (file_stream_.is_open()) {
        file_stream_ << "[" << tag << "] [" << ts.str() << "] "
                     << msg << "\n";
        file_stream_.flush();
    }
}

} // namespace visiond
